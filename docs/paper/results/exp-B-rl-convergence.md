# 실험 B 결과: RL 정책 수렴 + UCB1 커버리지

**실행일:** 2026-03-25
**학습:** 20 epoch, 에피소드 ~100건, α=0.1

## 결과 요약

| 지표 | 결과 | 기대값 | 판정 |
|------|------|--------|------|
| Q-value 수렴 | **epoch 5** (delta<0.001) | <100 | **PASS** |
| 최종 Q-table coverage | 4.2% (8/192) | >80% (UCB1 시) | **주의** |
| UCB1 미방문 추천 | **정확 동작** (미방문 action 우선) | 미방문 우선 | **PASS** |

## Phase 2: 수렴 곡선

| Epoch | Q_mean | delta | coverage | visited/192 |
|-------|--------|-------|----------|-------------|
| 1 | 0.0184 | - | 4.2% | 8 |
| 5 | 0.0243 | 0.0008 | 4.2% | 8 |
| 10 | 0.0272 | 0.0004 | 4.2% | 8 |
| 15 | 0.0288 | 0.0002 | 4.2% | 8 |
| 20 | 0.0298 | 0.0001 | 4.2% | 8 |

**수렴 판정:** epoch 5에서 delta < 0.001 → **빠른 수렴 확인**

## Phase 3: UCB1 vs Greedy 비교

| State (risk) | Greedy | UCB1 | Epsilon | 분석 |
|-------------|--------|------|---------|------|
| low | low (방문 1374회) | **medium** (미방문) | low | UCB1이 미방문 탐색 |
| medium | medium (방문 412회) | **low** (미방문) | low | UCB1이 미방문 탐색 |
| high | high (방문 204회) | **low** (미방문) | high | UCB1이 미방문 탐색 |

**핵심 발견:** UCB1은 모든 경우에서 **미방문 action을 정확히 추천**. Greedy는 기존 방문 action만 반복.

## 커버리지 분석 + 한계

### 낮은 커버리지(4.2%) 원인
- **단일 에이전트:** 동일 SubAgent(localhost:8002)만 사용 → success_rate 고정
- **균일한 task_order:** 대부분 1~3 → order_bucket=0 고정
- **48 states 중 소수만 활성:** risk_level×success_rate_bucket×order_bucket 조합 제한적

### UCB1의 가치
- 커버리지 자체를 높이려면 **다양한 에이전트/시나리오** 필요
- UCB1은 주어진 state에서 **미방문 action을 탐색**하여 Q-table 다양성 확보
- 실운영에서 여러 에이전트 + 다양한 risk_level 혼합 시 커버리지 자연 확장 예상

### 개선 권고
1. **다중 에이전트 환경:** secu/web/siem 각각 SubAgent → success_rate 다양화
2. **task_order 다양화:** 5~10개 태스크 프로젝트 → order_bucket 1,2 활성화
3. **ε-greedy 자동 적용:** recommend() 결과를 execute-plan에 자동 반영

## OpsClaw 위임 준수 점검

이 실험의 모든 태스크는 OpsClaw API(`POST /projects`, `POST /execute-plan`, `POST /rl/train`, `GET /rl/recommend`)를 통해 실행됨. 직접 SSH 사용 없음. ✅

## 발견사항 (개선 필요)

| 항목 | 내용 | 심각도 |
|------|------|--------|
| **커버리지 정체** | 동일 환경 반복 시 Q-table 8/192만 학습됨 | 중간 |
| **UCB1 효과 제한** | UCB1은 action만 탐색 — state 다양화는 별도 필요 | 중간 |
| **visit_count 누적** | 20 epoch × ~100 episodes = 2000회가 8셀에 집중 | 낮음 |
