# 실험 G: Playbook 재현성

## 입증 목표

**U4 — 결정론적 실행**: 동일 Playbook을 반복 실행 시 >95% 의미적 재현율 달성.

## 가설

> H1: 동일 Playbook 10회 실행 시 stdout의 의미적 일치율 >95%.
> H2: LLM 기반 adhoc 실행은 재현율 <50%.
> H3: Playbook 스크립트 빌더는 shell injection에 안전하다.

## 실험 절차

### Phase 1: Playbook 생성 + 10회 반복 실행

```bash
# Playbook 생성
PB=$(curl -s -X POST http://localhost:8000/playbooks \
  -H "Content-Type: application/json" \
  -d '{"name":"exp-G-determinism","version":"1.0.0","description":"재현성 테스트"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin).get('playbook',{}).get('id',''))")

# Step 추가
curl -s -X POST "http://localhost:8000/playbooks/$PB/steps" \
  -H "Content-Type: application/json" \
  -d '[
    {"order":1,"type":"skill","ref":"probe_linux_host","name":"시스템 정보 수집"},
    {"order":2,"type":"tool","ref":"query_metric","name":"메트릭 조회","metadata":{"metric":"cpu"}}
  ]'

# 10회 반복 실행 (결과 수집)
for i in $(seq 1 10); do
  PRJ=$(curl -s -X POST http://localhost:8000/projects \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"exp-G-run-$i\",\"request_text\":\"determinism test $i\",\"master_mode\":\"external\"}" \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['project']['id'])")
  curl -s -X POST "http://localhost:8000/projects/$PRJ/plan" > /dev/null
  curl -s -X POST "http://localhost:8000/projects/$PRJ/execute" > /dev/null

  # Playbook 실행
  RESULT=$(curl -s -X POST "http://localhost:8000/projects/$PRJ/playbook/run" \
    -H "Content-Type: application/json" \
    -d "{\"subagent_url\":\"http://localhost:8002\"}")

  echo "$RESULT" > "/tmp/exp_g_run_$i.json"
  echo "Run $i: $(echo "$RESULT" | python3 -c "import sys,json; r=json.load(sys.stdin); print(r.get('result',{}).get('status','?'))")"
done
```

### Phase 2: 재현율 계산

```python
import json, difflib

results = []
for i in range(1, 11):
    with open(f"/tmp/exp_g_run_{i}.json") as f:
        r = json.load(f)
    steps = r.get("result", {}).get("step_results", [])
    # 각 step의 stdout에서 타임스탬프/PID 제거 후 비교
    normalized = []
    for s in steps:
        stdout = s.get("stdout", "")
        # 타임스탬프, PID 등 변동 요소 제거
        import re
        stdout = re.sub(r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}', 'TIMESTAMP', stdout)
        stdout = re.sub(r'\b\d{2,6}\b', 'NUM', stdout)
        normalized.append(stdout)
    results.append(normalized)

# 첫 번째 결과를 기준으로 유사도 계산
baseline = results[0]
similarities = []
for i in range(1, len(results)):
    sim = difflib.SequenceMatcher(None, str(baseline), str(results[i])).ratio()
    similarities.append(sim)
    print(f"Run {i+1} vs Run 1: similarity={sim:.4f}")

avg_sim = sum(similarities) / len(similarities)
print(f"\n평균 재현율: {avg_sim:.4f} ({avg_sim*100:.1f}%)")
```

### Phase 3: Adhoc(LLM) 비교군

```bash
# 동일 작업을 adhoc dispatch로 10회 실행 (LLM이 매번 다른 스크립트 생성)
for i in $(seq 1 10); do
  curl -s -X POST "http://localhost:8000/projects/$PRJ/dispatch" \
    -H "Content-Type: application/json" \
    -d '{"command":"시스템의 CPU, 메모리, 디스크 사용량을 조사하고 요약해줘","mode":"adhoc","subagent_url":"http://localhost:8002"}' \
    > "/tmp/exp_g_adhoc_$i.json"
done
# → 같은 분석으로 재현율 측정
```

## 측정 지표

| 지표 | Playbook | Adhoc (LLM) |
|------|---------|-------------|
| 의미적 재현율 | >95% | <50% |
| stdout 길이 변동 (CV) | <10% | >50% |
| 명령어 일치율 | 100% | <30% |
