# 실험 D: 경험 재활용 효과 (A/B 테스트)

## 입증 목표

**U3 — 경험 축적 및 재활용**: RAG 기반 경험 검색이 새 프로젝트의 계획 품질과 실행 성공률을 향상시킨다.

## 가설

> H1: 과거 경험을 RAG로 주입한 LLM 응답이, 주입하지 않은 응답 대비 지시문 구체성이 높다.
> H2: 고보상 에피소드(reward ≥ 1.1)는 자동으로 experience로 승급된다.
> H3: 경험 DB가 축적될수록 RAG 검색 적중률이 향상된다.

## 실험 절차

### Phase 1: 경험 축적 (10개 프로젝트 실행)

```bash
# 다양한 운영 작업 실행 → experience 자동 축적
SCENARIOS=("hostname && uptime" "df -h && free -m" "systemctl list-units --failed"
           "cat /etc/os-release" "ss -tlnp" "ps aux --sort=-rss | head -20"
           "last -10" "journalctl -p err --since '1 hour ago'" "ip addr show" "w")

for i in $(seq 0 9); do
  PRJ=$(curl -s -X POST http://localhost:8000/projects \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"exp-D-phase1-$i\",\"request_text\":\"${SCENARIOS[$i]}\",\"master_mode\":\"external\"}" \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['project']['id'])")
  curl -s -X POST "http://localhost:8000/projects/$PRJ/plan" > /dev/null
  curl -s -X POST "http://localhost:8000/projects/$PRJ/execute" > /dev/null
  curl -s -X POST "http://localhost:8000/projects/$PRJ/execute-plan" \
    -H "Content-Type: application/json" \
    -d "{\"tasks\":[{\"order\":1,\"title\":\"task-$i\",\"instruction_prompt\":\"${SCENARIOS[$i]}\",\"risk_level\":\"low\"}],\"subagent_url\":\"http://localhost:8002\"}" > /dev/null
done

# RL 학습 → 고보상 에피소드 자동 experience 승급 확인
curl -s -X POST "http://localhost:8000/rl/train"
```

### Phase 2: A/B 테스트

```python
import requests

# A그룹: RAG 없이 채팅 (빈 context)
response_a = requests.post("http://localhost:8000/chat", json={
    "message": "디스크 사용량을 점검하고 90% 이상인 파티션을 정리하는 방법을 알려줘",
    "context_type": "project",
    "context_id": "",  # 빈 context
}).json()

# B그룹: RAG 포함 채팅 (기존 프로젝트 context)
response_b = requests.post("http://localhost:8000/chat", json={
    "message": "디스크 사용량을 점검하고 90% 이상인 파티션을 정리하는 방법을 알려줘",
    "context_type": "project",
    "context_id": "prj_xxxxx",  # Phase 1에서 생성된 관련 프로젝트
}).json()

# 비교: reply 길이, 구체적 명령어 포함 여부, RAG 참조 건수
print(f"A(no RAG): {len(response_a['reply'])} chars, rag_sources=0")
print(f"B(RAG):    {len(response_b['reply'])} chars, rag_sources={response_b.get('rag_sources',0)}")
```

### Phase 3: 자동 승급 검증

```bash
# experience 목록 확인
curl -s "http://localhost:8000/experience?limit=20" | python3 -c "
import sys, json
r = json.load(sys.stdin)
items = r.get('items', [])
auto = [e for e in items if e.get('title','').startswith('[Auto]')]
print(f'총 experience: {len(items)}, 자동 승급: {len(auto)}')
for e in auto[:5]:
    print(f'  {e[\"title\"][:60]} category={e.get(\"category\",\"?\")}')
"
```

## 측정 지표

| 지표 | 산출 방법 | 기대값 |
|------|---------|--------|
| 자동 승급률 | auto_promoted / (reward ≥ 1.1 projects) | >80% |
| RAG 참조 건수 (B그룹) | rag_sources 평균 | >1.0 |
| 응답 구체성 | 명령어/파일경로 포함 비율 (정규식) | B > A |
| 응답 길이 | 문자 수 | B > A (컨텍스트 활용) |
| RAG 검색 적중률 | 적중 건수 / 쿼리 수 | >60% |
