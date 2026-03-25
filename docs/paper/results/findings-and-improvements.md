# 실험 중 발견사항 종합 — 우수성, 한계, 개선 필요, 버그

**실험 기간:** 2026-03-25
**실험 범위:** 기반 검증 A~H + 비교 실험

---

## 우수성 (Strengths)

| # | 발견 | 실험 | 정량 근거 |
|---|------|------|---------|
| S1 | **PoW 위변조 100% 탐지** | A | block_hash/nonce 변조 즉시 탐지, 위양성 0% |
| S2 | **시간대 완전 불변** | H | 5개 TZ에서 50/50 해시 일치 (ts_raw 기반) |
| S3 | **상태 머신 100% 차단** | E | 무효 전이 5/5 거부, replan 복구 성공 |
| S4 | **Playbook 재현율 100%** | G | 10회 반복 동일 stdout (의미적 완전 일치) |
| S5 | **병렬 4.0x 가속** | F | N=5 태스크, sequential 대비 |
| S6 | **증거 완전율 100%** | C | evidence/PoW/reward 모두 태스크 수와 일치 |
| S7 | **자동 경험 승급** | D | 20건 [Auto] 승급, reward≥1.1 정확 트리거 |
| S8 | **RL 빠른 수렴** | B | epoch 5에서 Q-value delta < 0.001 |
| S9 | **UCB1 미방문 탐색** | B | 모든 state에서 미방문 action 정확 추천 |
| S10 | **3.4x 속도 + 10건 증적** | 비교 | OpsClaw vs Claude Code, parallel + auto evidence |

---

## 한계 (Limitations)

| # | 한계 | 실험 | 영향 |
|---|------|------|------|
| L1 | **RL 커버리지 4.2%** | B | 동일 환경 반복 시 state 다양성 부족 → 48개 중 8개만 학습 |
| L2 | **단일 SubAgent 병목** | F | 병렬 실행 시 로컬 SubAgent가 경합 → 이론 대비 80% 효율 |
| L3 | **한국어 FTS 미지원** | D | RAG 검색이 영문 기반 → 한국어 쿼리 적중 0 |
| L4 | **prev_hash 변조 탐지** | A | orphan 분류로 처리됨 (tampered=0) — 간접 감지만 가능 |
| L5 | **N=1 태스크 오버헤드** | F | 단일 태스크에서 OpsClaw가 직접 실행보다 약간 느림 |

---

## 개선 필요 (Improvements Needed)

| # | 개선안 | 관련 | 우선순위 |
|---|--------|------|---------|
| I1 | **다중 SubAgent 분산** | L2 | 높음 — secu/web/siem 각각 SubAgent 운영 |
| I2 | **한국어 trigram FTS** | L3 | 중간 — `pg_trgm` 확장 + 한국어 인덱스 |
| I3 | **RL state 확장** | L1 | 중간 — agent_id별 독립 state, task 유형 추가 |
| I4 | **prev_hash orphan 경보** | L4 | 낮음 — orphan_count > 0 시 경고 표시 |
| I5 | **ε-greedy 자동 적용** | B | 낮음 — recommend() 결과를 execute-plan에 자동 반영 |
| I6 | **Codex 비교 환경** | 비교 | 중간 — OpenAI Codex CLI 설치 + 동일 시나리오 실행 |

---

## 버그 / 이슈

| # | 내용 | 발견 실험 | 심각도 |
|---|------|---------|--------|
| BUG-1 | `_mask_secrets` 패턴에 한국어 패스워드 미포함 | 일반 | 낮음 |
| BUG-2 | PoW 블록 병렬 생성 시 prev_hash가 완료 순서 의존 (task order와 다를 수 있음) | F | 낮음 |
| ISSUE-1 | experience 카테고리가 전부 "operations" — LLM 분류 미동작 (pi LLM 미연결 시 기본값) | D | 중간 |

---

## 논문에서 활용할 핵심 수치

```
위변조 탐지율:     100% (실험 A)
시간대 불변성:     100% (실험 H, 5 TZ)
상태 전이 차단율:  100% (실험 E)
Playbook 재현율:   100% (실험 G, 10회)
증거 완전율:       100% (실험 C)
병렬 가속:         4.0x (실험 F, N=5)
RL 수렴:           epoch 5 (실험 B)
경험 자동 승급:    20건 (실험 D)
OpsClaw vs Claude: 3.4x 속도 + 10건 증적 (비교)
```
