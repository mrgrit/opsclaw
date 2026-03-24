# 실험 C: 증거 완전성 감사

## 입증 목표

**U3 — 경험 축적**: 모든 실행된 태스크가 evidence + PoW 블록으로 100% 추적 가능하다.

## 가설

> 실행된 모든 태스크에 대해 (1) evidence 레코드, (2) PoW 블록, (3) task_reward가 존재하며,
> PoW의 evidence_hash = sha256(stdout + stderr + exit_code) 이 evidence 원본과 일치한다.

## 실험 절차

### Phase 1: 혼합 시나리오 실행

5개 태스크 (성공 3, 실패 1, 오류 1)를 의도적으로 구성하여 실행.

```bash
PRJ=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -d '{"name":"exp-C-evidence","request_text":"evidence completeness test","master_mode":"external"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['project']['id'])")

curl -s -X POST "http://localhost:8000/projects/$PRJ/plan" > /dev/null
curl -s -X POST "http://localhost:8000/projects/$PRJ/execute" > /dev/null

RESULT=$(curl -s -X POST "http://localhost:8000/projects/$PRJ/execute-plan" \
  -H "Content-Type: application/json" \
  -d '{
    "tasks": [
      {"order":1,"title":"success-1","instruction_prompt":"echo hello","risk_level":"low"},
      {"order":2,"title":"success-2","instruction_prompt":"hostname","risk_level":"low"},
      {"order":3,"title":"success-3","instruction_prompt":"date +%s","risk_level":"medium"},
      {"order":4,"title":"failure-1","instruction_prompt":"exit 1","risk_level":"high"},
      {"order":5,"title":"error-1","instruction_prompt":"nonexistent_command_xyz","risk_level":"low"}
    ],
    "subagent_url": "http://localhost:8002",
    "confirmed": true
  }')
echo "$RESULT" | python3 -m json.tool
```

### Phase 2: 증거 대조

```sql
-- 1) 프로젝트의 evidence 수
SELECT COUNT(*) as evidence_count FROM evidence WHERE project_id = '${PRJ}';

-- 2) 프로젝트의 PoW 블록 수
SELECT COUNT(*) as pow_count FROM proof_of_work WHERE project_id = '${PRJ}';

-- 3) task_reward 수
SELECT COUNT(*) as reward_count FROM task_reward WHERE project_id = '${PRJ}';

-- 4) evidence_hash 일치 검증
SELECT
  pw.id,
  pw.task_title,
  pw.evidence_hash,
  md5(e.stdout_ref || e.stderr_ref || CAST(e.exit_code AS TEXT)) as recalc_hash
FROM proof_of_work pw
JOIN evidence e ON e.project_id = pw.project_id
WHERE pw.project_id = '${PRJ}';
```

### Phase 3: Replay API로 타임라인 재구성

```bash
curl -s "http://localhost:8000/projects/$PRJ/replay" | python3 -c "
import sys, json
r = json.load(sys.stdin)
print(f'Steps: {r[\"steps_total\"]}, Success: {r[\"steps_success\"]}, Reward: {r[\"total_reward\"]}')
for s in r['timeline']:
    print(f'  #{s[\"task_order\"]} {s[\"task_title\"]:20s} exit={s.get(\"exit_code\",\"?\")} reward={s.get(\"total_reward\",0):.4f} {s[\"ts\"]}')
"
```

## 측정 지표

| 지표 | 산출 방법 | 기대값 |
|------|---------|--------|
| 증거 완전율 | evidence_count / tasks_executed | 100% |
| PoW 블록 완전율 | pow_blocks / (ok + failed tasks) | 100% |
| evidence_hash 일치율 | 일치 건수 / 전체 블록 | 100% |
| 타임라인 재구성 정확도 | replay steps == executed tasks | 100% |
