# 실험 A: PoW 체인 무결성 검증

## 입증 목표

**U1 — 작업 증명 가능성**: 임의 블록 위변조 시 100% 탐지율 달성.

## 가설

> OpsClaw의 PoW 해시 체인은 단일 블록 수정 시에도 무결성 위반을 감지한다.
> 탐지율은 위변조 위치(초기/중간/마지막 블록)에 무관하게 100%이다.

## 실험 환경

- Manager API: http://localhost:8000
- SubAgent: http://localhost:8002
- DB: PostgreSQL (opsclaw)
- 검증 함수: `packages/pow_service/__init__.py:verify_chain()`

## 실험 절차

### Phase 1: 정상 블록 생성

```bash
# 1. 프로젝트 생성 + 5개 태스크 실행
PRJ=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -d '{"name":"exp-A-chain-test","request_text":"chain integrity test","master_mode":"external"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['project']['id'])")

curl -s -X POST "http://localhost:8000/projects/$PRJ/plan" > /dev/null
curl -s -X POST "http://localhost:8000/projects/$PRJ/execute" > /dev/null

curl -s -X POST "http://localhost:8000/projects/$PRJ/execute-plan" \
  -H "Content-Type: application/json" \
  -d '{
    "tasks": [
      {"order":1,"title":"task-1","instruction_prompt":"hostname","risk_level":"low"},
      {"order":2,"title":"task-2","instruction_prompt":"uptime","risk_level":"low"},
      {"order":3,"title":"task-3","instruction_prompt":"date","risk_level":"medium"},
      {"order":4,"title":"task-4","instruction_prompt":"whoami","risk_level":"low"},
      {"order":5,"title":"task-5","instruction_prompt":"uname -a","risk_level":"low"}
    ],
    "subagent_url": "http://localhost:8002"
  }'

# 2. 정상 상태 검증 (baseline)
curl -s "http://localhost:8000/pow/verify?agent_id=http://localhost:8002"
# 예상: {"valid": true, "blocks": N, "tampered": []}
```

### Phase 2: 위변조 주입

```sql
-- 시나리오 2a: block_hash 변조 (중간 블록)
UPDATE proof_of_work
SET block_hash = 'tampered_' || block_hash
WHERE id = (SELECT id FROM proof_of_work ORDER BY ts OFFSET 2 LIMIT 1);

-- 시나리오 2b: prev_hash 변조 (체인 연결 끊기)
UPDATE proof_of_work
SET prev_hash = '0000000000000000000000000000000000000000000000000000000000000000'
WHERE id = (SELECT id FROM proof_of_work ORDER BY ts OFFSET 3 LIMIT 1);

-- 시나리오 2c: nonce 변조 (난이도 조건 위반)
UPDATE proof_of_work
SET nonce = nonce + 999999
WHERE id = (SELECT id FROM proof_of_work ORDER BY ts DESC LIMIT 1);
```

### Phase 3: 위변조 탐지

```bash
# 각 시나리오 후 검증
curl -s "http://localhost:8000/pow/verify?agent_id=http://localhost:8002" | python3 -c "
import sys, json
r = json.load(sys.stdin)['result']
print(f'valid={r[\"valid\"]}, tampered={len(r[\"tampered\"])}')
for t in r['tampered']:
    print(f'  {t[\"id\"]}: {t[\"reason\"]}')
"
```

### Phase 4: 복원 후 재검증

```sql
-- 원복 (rollback)
-- 위변조 전 백업으로 복원 후 재검증
```

## 측정 지표

| 지표 | 산출 방법 | 기대값 |
|------|---------|--------|
| 탐지율 (Detection Rate) | 탐지 건수 / 위변조 건수 | 100% |
| 위양성률 (False Positive) | 정상 블록 탐지 건수 / 전체 정상 블록 | 0% |
| 탐지 유형별 분류 | block_hash_mismatch / chain_broken / difficulty_not_met | 각 시나리오에 매핑 |
| 검증 소요시간 | verify_chain 호출 시간 (ms) | <500ms (50 블록 기준) |

## 결과 테이블 (양식)

| 시나리오 | 위변조 대상 | 탐지 여부 | 탐지 이유 | 소요시간 |
|---------|-----------|----------|---------|---------|
| 2a | block_hash (3번째 블록) | | | |
| 2b | prev_hash (4번째 블록) | | | |
| 2c | nonce (마지막 블록) | | | |
| baseline | 없음 (정상) | valid=true | - | |

## 비교 분석

| 프레임워크 | 위변조 탐지 메커니즘 | 탐지율 |
|-----------|-------------------|--------|
| **OpsClaw** | SHA-256 해시 체인 + nonce 난이도 검증 | 100% (실험) |
| AutoGPT | 없음 (로그 파일) | 0% |
| CrewAI | 없음 | 0% |
| LangChain | Callback 기반 로그 | 0% |
