# 실험 B: RL 정책 수렴 + UCB1 커버리지

## 입증 목표

**U2 — 자기강화 학습**: Q-table이 학습 반복에 따라 수렴하며, UCB1 탐색이 greedy 대비 유의미한 커버리지 향상을 달성한다.

## 가설

> H1: Q-learning 정책은 100회 학습 내에 수렴한다 (Q-value 변동 <0.01).
> H2: UCB1 탐색은 greedy 대비 state-action 커버리지가 30%p 이상 높다.
> H3: UCB1 추천 action은 미방문 영역을 우선 선택한다.

## 실험 절차

### Phase 1: 에피소드 생성 (다양한 시나리오)

```bash
# 다양한 risk_level + 성공/실패 시나리오로 30개 프로젝트 × 3~5 태스크 실행
# → task_reward 테이블에 100+ 에피소드 축적

for i in $(seq 1 10); do
  PRJ=$(curl -s -X POST http://localhost:8000/projects \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"exp-B-rl-$i\",\"request_text\":\"RL training data\",\"master_mode\":\"external\"}" \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['project']['id'])")

  curl -s -X POST "http://localhost:8000/projects/$PRJ/plan" > /dev/null
  curl -s -X POST "http://localhost:8000/projects/$PRJ/execute" > /dev/null

  # 다양한 risk_level 조합
  curl -s -X POST "http://localhost:8000/projects/$PRJ/execute-plan" \
    -H "Content-Type: application/json" \
    -d "{
      \"tasks\": [
        {\"order\":1,\"title\":\"probe-$i\",\"instruction_prompt\":\"hostname && uptime\",\"risk_level\":\"low\"},
        {\"order\":2,\"title\":\"check-$i\",\"instruction_prompt\":\"df -h\",\"risk_level\":\"medium\"},
        {\"order\":3,\"title\":\"service-$i\",\"instruction_prompt\":\"systemctl status sshd\",\"risk_level\":\"high\"}
      ],
      \"subagent_url\": \"http://localhost:8002\",
      \"parallel\": true
    }"
done
```

### Phase 2: 반복 학습 + 수렴 측정

```python
# scripts/exp_b_rl_convergence.py
import requests, json

results = []
for epoch in range(20):
    r = requests.post("http://localhost:8000/rl/train",
                       params={"limit": 500}).json()
    stats = requests.get("http://localhost:8000/rl/policy").json()

    results.append({
        "epoch": epoch + 1,
        "episodes_used": r.get("episodes_used", 0),
        "q_mean": stats.get("q_table_mean"),
        "q_max": stats.get("q_table_max"),
        "coverage_pct": stats.get("coverage_pct"),
        "visit_coverage_pct": stats.get("coverage_by_visits_pct"),
        "visited": stats.get("visited_count"),
        "unvisited": stats.get("unvisited_count"),
    })
    print(f"Epoch {epoch+1}: coverage={stats.get('coverage_by_visits_pct')}% "
          f"q_mean={stats.get('q_table_mean')} visited={stats.get('visited_count')}")

# CSV 저장
import csv
with open("data/exp_b_convergence.csv", "w") as f:
    w = csv.DictWriter(f, fieldnames=results[0].keys())
    w.writeheader()
    w.writerows(results)
```

### Phase 3: UCB1 vs Greedy 비교

```python
# 동일 state에서 탐색 전략별 추천 비교
strategies = ["greedy", "ucb1", "epsilon"]
for agent in ["http://localhost:8002"]:
    for risk in ["low", "medium", "high"]:
        for strat in strategies:
            r = requests.get("http://localhost:8000/rl/recommend", params={
                "agent_id": agent, "risk_level": risk,
                "task_order": 1, "exploration": strat,
            }).json()
            print(f"{strat:8s} risk={risk:8s} → {r.get('recommended_risk_level')} "
                  f"visits={r.get('visit_counts')}")
```

## 측정 지표

| 지표 | 산출 방법 | 기대값 |
|------|---------|--------|
| Q-value 수렴 epoch | \|Q_mean(t) - Q_mean(t-1)\| < 0.01 최초 도달 | <100 |
| 최종 커버리지 (greedy) | nonzero_entries / 192 | <60% |
| 최종 커버리지 (UCB1) | visit_counts > 0 / 192 | >80% |
| UCB1 커버리지 향상폭 | UCB1 - greedy (percentage point) | >30%p |
| 추천 다양성 (entropy) | -Σ p(a) log p(a) | UCB1 > greedy |

## 결과 시각화

- **Figure 1**: Q-value mean/max 수렴 곡선 (epoch vs Q-value)
- **Figure 2**: 커버리지 % 증가 곡선 (greedy vs UCB1)
- **Figure 3**: 48×4 히트맵 (visit_counts, 전략별 비교)
- **Table 1**: 전략별 추천 action 분포 (entropy 비교)
