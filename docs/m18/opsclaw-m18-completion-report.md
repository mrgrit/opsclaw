# OpsClaw M18 완료보고서: Proof of Work & Blockchain Reward

**날짜:** 2026-03-22 (nonce 채굴 추가: 2026-03-23)
**마일스톤:** M18 — Proof of Work & Blockchain Reward
**상태:** ✅ 완료

---

## 개요

각 SubAgent의 Task 실행 결과를 해시 체인으로 기록하고 RL(강화학습) reward signal을 자동 계산하는 인프라를 구현했다. 외부 블록체인 의존성 없이 내부망에서 완전히 동작하는 자체 Merkle Chain을 채택했다.

**핵심 개념: 작업 수행 = 채굴.** `execute-plan`으로 Task를 실행하면 자동으로 nonce 채굴 → PoW 블록 생성 → 보상 지급이 이루어진다.

**장기 비전:** PoW → 보상 토큰 → 강화학습 → 에이전트 policy 지속 개선

---

## 완료 항목

### WORK-79: DB 마이그레이션 (`migrations/0009_proof_of_work.sql`)

| 테이블 | 역할 |
|--------|------|
| `proof_of_work` | Task 1개 = 블록 1개. sha256 해시 체인으로 위변조 불가 기록. nonce/difficulty 컬럼 포함 (0010) |
| `task_reward` | Task별 RL reward signal. base_score + speed_bonus + risk_penalty |
| `reward_ledger` | 에이전트별 누적 잔액. UPSERT로 자동 관리 |

> **migration 0010 (2026-03-23 추가):** `proof_of_work` 테이블에 `nonce INTEGER`, `difficulty INTEGER` 컬럼 추가. 기존 블록은 nonce=0, difficulty=0으로 자동 마이그레이션.

### WORK-80~82 + nonce 채굴 (2026-03-23): pow_service (`packages/pow_service/__init__.py`)

핵심 함수:
- `_mine_block()` — nonce를 0부터 증가시키며 `sha256(prev_hash+evidence_hash+ts+nonce)`가 difficulty개 leading zero 만족하는 값 탐색
- `generate_proof()` — Task 실행 결과 → nonce 채굴 → PoW 블록 + 보상 + ledger UPSERT (원자적)
- `verify_chain()` — 에이전트 전체 블록 hash chain 재계산 검증 + nonce/difficulty 검증
- `get_agent_stats()` — 잔액 + 최근 보상 이력
- `get_leaderboard()` — 보상 상위 에이전트 랭킹
- `get_project_pow()` — 프로젝트 PoW 블록 목록
- `get_project_replay()` — 작업 타임라인 (task_order, ts, exit_code, block_hash, total_reward)

보상 함수 (`_calculate_reward`):
```
base_score  = +1.0 (성공) / -1.0 (실패)
speed_bonus = +0.3 (<5s) / +0.15 (<30s) / +0.05 (<60s)  — 성공 시만
risk_penalty= -0.1 (high 실패) / -0.2 (critical 실패)
quality_bonus = 0.0 (향후 human feedback 연결)
```

### WORK-83: Manager API 연동 + 엔드포인트

**execute-plan 자동 연동:** Task 완료 시 `generate_proof()` 자동 호출 (dry_run 제외, 예외 발생해도 작업 결과에 영향 없음)

**신규 API 엔드포인트 7개:**
```
GET /pow/blocks?agent_id=&limit=   블록 목록
GET /pow/blocks/{pow_id}           단건 조회
GET /pow/verify?agent_id=          체인 무결성 검증
GET /pow/leaderboard               보상 랭킹
GET /rewards/agents?agent_id=      에이전트 잔액 + 통계
GET /projects/{id}/pow             프로젝트 PoW 블록
GET /projects/{id}/replay          작업 Replay 타임라인
```

---

## 테스트 결과

```
[1] DB 테이블 존재 확인           ✅✅✅
[2] execute-plan → PoW 자동 생성  ✅✅✅
[3] 블록 해시 직접 검증            ✅✅
[4] task_reward 보상 내용          ✅✅✅✅
[5] reward_ledger 에이전트 잔액    ✅✅✅
[6] verify_chain API               ✅✅✅
[7] Leaderboard API                ✅✅
[8] Replay 타임라인 API            ✅✅✅
[9] 위변조 감지 (변조 → 탐지)      ✅✅

결과: 25/25 PASS ✅
```

**위변조 감지 동작 확인:**
- 블록 hash 변조 → `valid: false`, `reason: block_hash_mismatch`
- 체인 끊김 → `reason: chain_broken`

---

## RL 연결 설계

```
Task 실행
  → exit_code / duration_s / risk_level 자동 기록
  → reward = base_score + speed_bonus + risk_penalty
  → reward_ledger 적립 (누적 잔액)
  → [향후 M21+] 누적 task_reward → policy network 학습
  → 더 나은 instruction_prompt / risk_level 판단
```

`quality_bonus` 필드는 현재 0.0으로 예약됨 — human feedback 또는 validation 결과와 연결 예정.
