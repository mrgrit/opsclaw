# 실험 E: 상태 머신 유효성 검증

## 입증 목표

명시적 상태 전이 머신이 (1) 무효 전이를 100% 차단하고, (2) replan 기능이 실패 복구에 효과적임을 입증.

## 가설

> H1: 무효 상태 전이 시도 시 100% 거부 (HTTP 400).
> H2: replan 후 재실행 시 70% 이상 복구 성공.

## 실험 절차

### Phase 1: 무효 전이 차단 테스트

```bash
PRJ=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -d '{"name":"exp-E-state","request_text":"state machine test","master_mode":"external"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['project']['id'])")

# 유효: intake → plan (200)
echo "intake→plan: $(curl -s -o /dev/null -w '%{http_code}' -X POST "http://localhost:8000/projects/$PRJ/plan")"

# 무효 시도들 (현재 stage=plan)
echo "plan→validate: $(curl -s -o /dev/null -w '%{http_code}' -X POST "http://localhost:8000/projects/$PRJ/validate")"
echo "plan→close: $(curl -s -o /dev/null -w '%{http_code}' -X POST "http://localhost:8000/projects/$PRJ/close")"

# 유효: plan → execute (200)
echo "plan→execute: $(curl -s -o /dev/null -w '%{http_code}' -X POST "http://localhost:8000/projects/$PRJ/execute")"

# 무효: execute → plan (허용되지 않음, replan 별도 API)
echo "execute→plan(직접): $(curl -s -o /dev/null -w '%{http_code}' -X POST "http://localhost:8000/projects/$PRJ/plan")"
```

### Phase 2: Replan 복구 테스트

```bash
# 의도적 실패 후 replan
curl -s -X POST "http://localhost:8000/projects/$PRJ/execute-plan" \
  -H "Content-Type: application/json" \
  -d '{"tasks":[{"order":1,"title":"fail-task","instruction_prompt":"exit 1","risk_level":"low"}],"subagent_url":"http://localhost:8002"}'

# replan 시도
echo "replan: $(curl -s -o /dev/null -w '%{http_code}' -X POST "http://localhost:8000/projects/$PRJ/replan" -H "Content-Type: application/json" -d '{"reason":"retry after failure"}')"

# 재실행
curl -s -X POST "http://localhost:8000/projects/$PRJ/execute" > /dev/null
curl -s -X POST "http://localhost:8000/projects/$PRJ/execute-plan" \
  -H "Content-Type: application/json" \
  -d '{"tasks":[{"order":1,"title":"success-retry","instruction_prompt":"echo recovered","risk_level":"low"}],"subagent_url":"http://localhost:8002"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin).get('overall'))"
```

## 측정 지표

| 지표 | 기대값 |
|------|--------|
| 무효 전이 차단율 | 100% (모두 400) |
| replan 성공률 | >70% |
| 재실행까지 평균 시도 | <3회 |
