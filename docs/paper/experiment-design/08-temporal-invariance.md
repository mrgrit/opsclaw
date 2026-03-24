# 실험 H: PoW 시간대 불변성 (M27 패치 검증)

## 입증 목표

**U1 — 작업 증명 가능성**: PoW 해시 검증이 DB 세션 시간대(timezone)에 무관하게 일관된 결과를 반환한다.

## 가설

> H1: ts_raw 기반 해시 계산은 DB timezone 변경 시에도 block_hash 검증 결과가 동일하다.
> H2: orphan 블록(병렬 세션)이 정상 체인과 분리 집계된다.

## 실험 절차

### Phase 1: 블록 생성 (UTC 환경)

```bash
PRJ=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -d '{"name":"exp-H-tz","request_text":"timezone invariance","master_mode":"external"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['project']['id'])")
curl -s -X POST "http://localhost:8000/projects/$PRJ/plan" > /dev/null
curl -s -X POST "http://localhost:8000/projects/$PRJ/execute" > /dev/null
curl -s -X POST "http://localhost:8000/projects/$PRJ/execute-plan" \
  -H "Content-Type: application/json" \
  -d '{"tasks":[{"order":1,"title":"tz-test","instruction_prompt":"date","risk_level":"low"}],"subagent_url":"http://localhost:8002"}'

# 검증 (baseline)
RESULT1=$(curl -s "http://localhost:8000/pow/verify?agent_id=http://localhost:8002")
echo "UTC: $RESULT1"
```

### Phase 2: DB 시간대 변경 후 검증

```sql
-- 세션 시간대를 변경하여 검증
SET timezone = 'Asia/Seoul';
-- 검증 쿼리 (verify_chain과 동일 로직)
SELECT id, ts, ts_raw, block_hash FROM proof_of_work ORDER BY ts DESC LIMIT 5;
```

```bash
# API를 통한 검증 (서버 시간대 무관)
RESULT2=$(curl -s "http://localhost:8000/pow/verify?agent_id=http://localhost:8002")
echo "After TZ change: $RESULT2"

# 두 결과 비교
python3 -c "
r1 = $RESULT1
r2 = $RESULT2
print(f'UTC valid={r1[\"result\"][\"valid\"]}, Changed valid={r2[\"result\"][\"valid\"]}')
assert r1['result']['valid'] == r2['result']['valid'], 'TZ invariance FAILED'
print('PASS: Timezone invariance verified')
"
```

## 측정 지표

| 시간대 | verify_chain valid | tampered | orphans |
|--------|-------------------|----------|---------|
| UTC | | | |
| Asia/Seoul (+9) | | | |
| US/Pacific (-7) | | | |
| UTC 재검증 | | | |

**기대 결과:** 모든 시간대에서 동일한 valid/tampered/orphans 값.
