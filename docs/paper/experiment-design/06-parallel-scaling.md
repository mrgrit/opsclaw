# 실험 F: 병렬 스케일링

## 입증 목표

**U5 — 병렬 멀티에이전트**: parallel=true 시 N개 태스크가 동시 실행되어 순차 대비 유의미한 속도 향상 달성.

## 가설

> H1: N개 태스크 병렬 실행 시 speedup ≈ min(N, 5).
> H2: 병렬 실행 시 태스크별 결과가 독립적 (partial failure 격리).

## 실험 절차

```bash
# N = 1, 2, 3, 5 태스크로 순차/병렬 비교
for N in 1 2 3 5; do
  # 태스크 생성 (각 태스크는 ~2초 소요되는 명령)
  TASKS=""
  for i in $(seq 1 $N); do
    [ -n "$TASKS" ] && TASKS="$TASKS,"
    TASKS="$TASKS{\"order\":$i,\"title\":\"sleep-$i\",\"instruction_prompt\":\"sleep 2 && echo task-$i-done\",\"risk_level\":\"low\"}"
  done

  # 프로젝트 생성
  PRJ=$(curl -s -X POST http://localhost:8000/projects \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"exp-F-par-N$N\",\"request_text\":\"parallel test\",\"master_mode\":\"external\"}" \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['project']['id'])")
  curl -s -X POST "http://localhost:8000/projects/$PRJ/plan" > /dev/null
  curl -s -X POST "http://localhost:8000/projects/$PRJ/execute" > /dev/null

  # 순차 실행
  T0=$(date +%s%N)
  curl -s -X POST "http://localhost:8000/projects/$PRJ/execute-plan" \
    -H "Content-Type: application/json" \
    -d "{\"tasks\":[$TASKS],\"subagent_url\":\"http://localhost:8002\",\"parallel\":false}" > /dev/null
  T1=$(date +%s%N)
  SEQ_MS=$(( (T1 - T0) / 1000000 ))

  # 새 프로젝트로 병렬 실행
  PRJ2=$(curl -s -X POST http://localhost:8000/projects \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"exp-F-par-N${N}p\",\"request_text\":\"parallel test\",\"master_mode\":\"external\"}" \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['project']['id'])")
  curl -s -X POST "http://localhost:8000/projects/$PRJ2/plan" > /dev/null
  curl -s -X POST "http://localhost:8000/projects/$PRJ2/execute" > /dev/null

  T0=$(date +%s%N)
  curl -s -X POST "http://localhost:8000/projects/$PRJ2/execute-plan" \
    -H "Content-Type: application/json" \
    -d "{\"tasks\":[$TASKS],\"subagent_url\":\"http://localhost:8002\",\"parallel\":true}" > /dev/null
  T1=$(date +%s%N)
  PAR_MS=$(( (T1 - T0) / 1000000 ))

  SPEEDUP=$(echo "scale=2; $SEQ_MS / $PAR_MS" | bc 2>/dev/null || echo "N/A")
  echo "N=$N  sequential=${SEQ_MS}ms  parallel=${PAR_MS}ms  speedup=${SPEEDUP}x"
done
```

## 측정 지표

| N | T_sequential (ms) | T_parallel (ms) | Speedup | 이론 최대 |
|---|-------------------|----------------|---------|----------|
| 1 | | | 1.0x | 1.0x |
| 2 | | | | 2.0x |
| 3 | | | | 3.0x |
| 5 | | | | 5.0x |

## 시각화

- **Figure**: N vs Speedup 그래프 (이론 최대 대비 실제)
- **Table**: Partial failure 시 독립성 검증 (1개 실패해도 나머지 성공)
