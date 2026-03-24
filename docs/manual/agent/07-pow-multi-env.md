# PoW 블록체인 — 다중 환경 운영 가이드

> **대상**: OpsClaw를 여러 세션, 여러 서버에서 운영하는 관리자 및 에이전트

---

## 배경: 왜 체인 무결성이 깨지는가

OpsClaw PoW 블록체인은 `agent_id`별로 독립된 해시 체인을 유지한다.
각 블록은 `prev_hash → block_hash` 링크로 연결되며, `verify_chain`은 이 링크를 따라가 위변조를 탐지한다.

다음 3가지 시나리오에서 체인 무결성이 깨질 수 있었다 **(M27 패치로 해결됨)**:

| 버그 | 증상 | 원인 |
|------|------|------|
| **Bug A** | `block_hash_mismatch` | DB 세션 timezone ≠ UTC → ts 문자열 변형 → SHA256 입력 달라짐 |
| **Bug B** | `chain_broken` | 다른 세션 채굴 블록이 섞여 `ORDER BY ts ASC` 정렬 순서가 prev_hash 연결과 불일치 |
| **Bug C** | 체인 분기 | 병렬 `generate_proof()` 호출 시 경쟁 조건으로 같은 prev_hash 공유 |

---

## M27 패치 내용

### 1. `ts_raw` — 원본 timestamp 문자열 보존

채굴 시 사용한 `datetime.now(timezone.utc).isoformat()` 문자열을 `ts_raw TEXT` 컬럼에 그대로 저장.
`verify_chain`은 `ts_raw`를 우선 사용하므로 DB 세션 timezone과 무관하게 동일한 hash를 재계산한다.

```
채굴 시:  ts_raw = "2026-03-24T14:11:10.800896+00:00"  (저장)
검증 시:  ts_str = block["ts_raw"]                      (그대로 사용)
```

기존 블록(ts_raw=NULL)은 마이그레이션(0013)에서 자동 backfill되고,
fallback 로직이 UTC 정규화를 보장한다.

### 2. linked-list traversal — 분기 체인 감지

`verify_chain`이 `ORDER BY ts ASC` 대신 `prev_hash` 링크를 따라 genesis에서 체인을 재구성.
분기(fork)가 발생해도 **longest-chain rule**로 메인 체인을 선택하고, 나머지는 `orphans`로 집계한다.

```json
{
  "valid": true,
  "blocks": 42,
  "orphans": 3,   // 다른 세션에서 채굴된 분기 블록 (메인 체인 무결성에 영향 없음)
  "tampered": []
}
```

### 3. `pg_advisory_xact_lock` — 병렬 채굴 직렬화

`generate_proof()`가 `agent_id` 기반 advisory lock을 획득한 후 `prev_hash` 조회 → 채굴 → INSERT를
단일 트랜잭션 안에서 처리. 동시 호출 시 먼저 온 요청이 끝난 후 다음 요청이 시작되어 체인 분기를 방지한다.

---

## 운영 원칙

### agent_id 네이밍 컨벤션

`agent_id`는 **전역 고유**해야 한다. 같은 `agent_id`를 다른 환경에서 사용하면 체인이 섞인다.

```
# 올바른 예 (호스트별 고유 URL)
http://secu:8002        → secu 서버 SubAgent
http://web:8002         → web 서버 SubAgent
http://siem:8002        → siem 서버 SubAgent
http://192.168.208.142:8002  → opsclaw control-plane SubAgent

# 잘못된 예 (여러 환경이 같은 ID 공유)
http://localhost:8002   → 어느 서버인지 불명확
```

`execute-plan` 호출 시 `subagent_url`을 명시하면 자동으로 `agent_id`로 사용된다:

```bash
curl -X POST http://localhost:8000/projects/{id}/execute-plan \
  -d '{"tasks":[...],"subagent_url":"http://secu:8002"}'
```

### git pull 후 체인 보존

M27 패치 이후 `git pull` → 서비스 재시작만으로 기존 체인이 유지된다.
마이그레이션이 새로 추가된 경우 반드시 적용한다:

```bash
# 마이그레이션 확인 및 적용
ls migrations/*.sql | sort
PGPASSWORD=opsclaw psql -h 127.0.0.1 -U opsclaw -d opsclaw -f migrations/0013_pow_ts_raw.sql

# 서비스 재시작
kill $(pgrep -f "manager-api") && sleep 2
set -a && source .env && set +a
export PYTHONPATH=/home/opsclaw/opsclaw
nohup .venv/bin/python3.11 -m uvicorn apps.manager-api.src.main:app \
  --host 0.0.0.0 --port 8000 --log-level warning > /tmp/manager.log 2>&1 &

# 체인 무결성 확인
curl "http://localhost:8000/pow/verify?agent_id=http://localhost:8002"
```

---

## verify_chain 결과 해석

```bash
curl "http://localhost:8000/pow/verify?agent_id=http://secu:8002"
```

| 필드 | 정상 | 비정상 |
|------|------|--------|
| `valid` | `true` | `false` |
| `blocks` | 채굴 블록 수 | — |
| `orphans` | `0` (이상적) | `>0` = 분기 블록 존재 (메인 체인 무결성엔 무관) |
| `tampered` | `[]` | 문제 블록 ID + 이유 목록 |

### 오류 유형별 대응

| reason | 원인 | 조치 |
|--------|------|------|
| `block_hash_mismatch` | ts_raw 누락 레거시 블록 (마이그레이션 미적용) | `0013` 마이그레이션 재적용 |
| `chain_broken` | 분기 체인 블록이 메인 체인에 혼입 | orphan 수 확인; M27 패치 적용 여부 확인 |
| `difficulty_not_met` | 블록 데이터 직접 조작 | DB 감사 로그 확인 |

### orphan 블록 확인 쿼리

```sql
-- 메인 체인에 속하지 않는 orphan 블록 조회
-- (verify_chain API가 orphan 수를 반환하므로 일반적으로 직접 조회할 필요 없음)
WITH RECURSIVE chain AS (
    SELECT block_hash, prev_hash, 0 AS depth
    FROM proof_of_work
    WHERE agent_id = 'http://secu:8002' AND prev_hash = repeat('0', 64)
    UNION ALL
    SELECT pw.block_hash, pw.prev_hash, c.depth + 1
    FROM proof_of_work pw
    JOIN chain c ON pw.prev_hash = c.block_hash
    WHERE pw.agent_id = 'http://secu:8002'
)
SELECT pw.id, pw.block_hash, pw.ts
FROM proof_of_work pw
WHERE pw.agent_id = 'http://secu:8002'
  AND pw.block_hash NOT IN (SELECT block_hash FROM chain);
```

---

## 체인 초기화 (극단적 복구)

정상적인 운영에서는 필요 없다. 심각한 데이터 손상으로 복구가 불가능한 경우에만 사용.

```bash
# 특정 agent_id의 체인 전체 삭제 (보상 기록도 함께 삭제됨)
PGPASSWORD=opsclaw psql -h 127.0.0.1 -U opsclaw -d opsclaw << 'SQL'
BEGIN;
DELETE FROM task_reward WHERE agent_id = 'http://secu:8002';
DELETE FROM reward_ledger WHERE agent_id = 'http://secu:8002';
DELETE FROM proof_of_work WHERE agent_id = 'http://secu:8002';
COMMIT;
SQL

# 초기화 후 검증
curl "http://localhost:8000/pow/verify?agent_id=http://secu:8002"
# {"valid": true, "blocks": 0, "orphans": 0, "tampered": []}
```

> **주의**: 체인 초기화는 해당 에이전트의 모든 보상 이력을 삭제한다.
> 반드시 pg_dump로 백업 후 진행할 것.
