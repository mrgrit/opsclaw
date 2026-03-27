# Week 13: 분산 지식

## 학습 목표
- 분산 지식 아키텍처의 개념과 필요성을 이해한다
- local_knowledge.json의 구조와 역할을 파악한다
- SubAgent 간 지식 전달(knowledge transfer) 메커니즘을 이해한다
- 분산 지식을 활용한 보안 운영 개선을 실습한다

---

## 1. 왜 분산 지식이 필요한가?

### 중앙 집중 vs 분산

| 방식 | 장점 | 단점 |
|------|------|------|
| 중앙 집중 | 단일 관리 지점 | 단일 장애점, 네트워크 의존 |
| 분산 | 네트워크 장애에 강함 | 동기화 필요 |

각 SubAgent가 자신의 환경에 대한 지식을 로컬에 저장하면:
- 네트워크 장애 시에도 기본 운영 가능
- 로컬 컨텍스트로 더 정확한 판단
- 중앙 서버 부하 감소

---

## 2. local_knowledge.json

각 SubAgent는 `local_knowledge.json` 파일에 로컬 지식을 저장한다.

### 2.1 구조

```json
{
  "agent_id": "http://192.168.208.150:8002",
  "hostname": "secu",
  "role": "nftables + Suricata IPS",
  "last_updated": "2026-03-27T10:00:00Z",
  "system_info": {
    "os": "Ubuntu 22.04",
    "kernel": "6.8.0-106-generic",
    "services": ["nftables", "suricata", "sshd"]
  },
  "security_baseline": {
    "open_ports": [22, 8002],
    "users": ["root", "opsclaw", "student"],
    "firewall_rules_count": 45
  },
  "learned_patterns": [
    {
      "pattern": "SSH brute force from 203.0.113.0/24",
      "first_seen": "2026-03-25",
      "action_taken": "IP blocked via nftables",
      "effectiveness": "high"
    }
  ],
  "local_policies": {
    "auto_block_threshold": 10,
    "alert_level_minimum": 8
  }
}
```

### 2.2 지식 카테고리

| 카테고리 | 내용 | 갱신 주기 |
|---------|------|----------|
| system_info | OS, 서비스, 설정 | Explore 시 |
| security_baseline | 포트, 사용자, 규칙 | Daemon 주기 |
| learned_patterns | 학습된 공격 패턴 | 이벤트 발생 시 |
| local_policies | 로컬 대응 정책 | 관리자 설정 |

---

## 3. Knowledge Transfer

### 3.1 지식 전달 흐름

```
SubAgent A (secu)          Manager            SubAgent B (web)
    │                         │                     │
    │ ── 지식 공유 요청 ──→   │                     │
    │                         │ ── 지식 전달 ──→    │
    │                         │                     │
    │   "secu에서 발견된       │   "secu 에서 공격    │
    │    공격 패턴 공유"       │    패턴 수신"        │
```

### 3.2 지식 전달 시나리오

```bash
# secu에서 공격 패턴 발견
KNOWLEDGE='{
  "source": "http://192.168.208.150:8002",
  "type": "threat_intelligence",
  "data": {
    "attack_type": "SSH brute force",
    "source_ip": "203.0.113.50",
    "timestamp": "2026-03-27T10:00:00Z",
    "action": "blocked"
  }
}'

# Manager를 통해 다른 SubAgent에 지식 전달
# 실제 구현에서는 Manager API의 knowledge endpoint 사용
```

### 3.3 지식 동기화 패턴

```
시나리오: secu에서 공격 IP 차단 → web/siem에도 알림

1. secu SubAgent: 공격 IP 203.0.113.50 탐지 및 차단
2. secu → Manager: 위협 인텔리전스 공유
3. Manager → web SubAgent: "이 IP에서 웹 공격 가능성, 모니터링 강화"
4. Manager → siem SubAgent: "이 IP 관련 알림 우선순위 상향"
```

---

## 4. LLM과 분산 지식의 결합

### 4.1 로컬 지식을 LLM 프롬프트에 활용

```bash
LOCAL_KNOWLEDGE='{
  "hostname": "web",
  "role": "웹 서버",
  "open_ports": [22, 80, 443, 8080],
  "recent_alerts": ["SQL Injection 시도 3건", "XSS 시도 1건"],
  "baseline_change": "포트 8080이 새로 열림"
}'

curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"gemma3:12b\",
    \"messages\": [
      {\"role\": \"system\", \"content\": \"보안 관제 에이전트입니다. 로컬 지식을 기반으로 현재 상황을 분석합니다.\"},
      {\"role\": \"user\", \"content\": \"로컬 지식:\\n$LOCAL_KNOWLEDGE\\n\\n현재 보안 상황을 분석하고 조치가 필요한 항목을 우선순위로 나열하세요.\"}
    ],
    \"temperature\": 0.3
  }" | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

### 4.2 교차 지식 분석

```bash
# 여러 SubAgent의 지식을 통합하여 분석
COMBINED='{
  "secu": {"alerts": 15, "blocked_ips": 3, "top_threat": "SSH brute force"},
  "web":  {"alerts": 8,  "blocked_ips": 1, "top_threat": "SQL Injection"},
  "siem": {"total_events": 5000, "critical": 2, "high": 15}
}'

curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"gemma3:12b\",
    \"messages\": [
      {\"role\": \"system\", \"content\": \"SOC 매니저입니다. 여러 보안 시스템의 데이터를 종합 분석합니다.\"},
      {\"role\": \"user\", \"content\": \"3개 서버의 보안 현황:\\n$COMBINED\\n\\n종합 위협 평가와 우선 대응 사항을 제시하세요.\"}
    ],
    \"temperature\": 0.3
  }" | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

---

## 5. 실습

### 실습 1: 로컬 지식 수집

```bash
# 프로젝트 준비
PID=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"name":"knowledge-lab","request_text":"분산 지식 실습","master_mode":"external"}' \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")
curl -s -X POST "http://localhost:8000/projects/$PID/plan" -H "X-API-Key: opsclaw-api-key-2026" > /dev/null
curl -s -X POST "http://localhost:8000/projects/$PID/execute" -H "X-API-Key: opsclaw-api-key-2026" > /dev/null

# 여러 서버에서 지식 수집
curl -s -X POST "http://localhost:8000/projects/$PID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "tasks": [
      {"order":1, "instruction_prompt":"hostname && uname -r && ss -tlnp | grep LISTEN | wc -l", "risk_level":"low", "subagent_url":"http://localhost:8002"},
      {"order":2, "instruction_prompt":"hostname && uname -r && ss -tlnp | grep LISTEN | wc -l", "risk_level":"low", "subagent_url":"http://192.168.208.150:8002"}
    ],
    "subagent_url":"http://localhost:8002"
  }' | python3 -m json.tool
```

### 실습 2: 지식 기반 LLM 분석

```bash
# 수집된 정보를 LLM으로 종합 분석
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "분산 시스템 보안 분석가입니다."},
      {"role": "user", "content": "2개 서버의 로컬 지식을 비교 분석하세요:\n\nopsclaw 서버: 커널 6.8.0-106, 열린 포트 5개 (22,8000,8001,8002,5432)\nsecu 서버: 커널 6.8.0-106, 열린 포트 3개 (22,8002,8443)\n\n각 서버의 보안 수준을 평가하고 개선 사항을 제시하세요."}
    ],
    "temperature": 0.3
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

---

## 6. 분산 지식의 보안 고려사항

| 위험 | 대응 |
|------|------|
| 지식 변조 | PoW 체인으로 무결성 검증 |
| 오래된 지식 | TTL(Time-To-Live) 설정 |
| 과도한 공유 | need-to-know 원칙 적용 |
| 동기화 충돌 | 타임스탬프 기반 최신 우선 |

---

## 핵심 정리

1. 분산 지식은 각 SubAgent가 로컬 환경 정보를 자체 저장하는 구조이다
2. local_knowledge.json에 시스템 정보, 보안 기준선, 학습된 패턴을 저장한다
3. Manager를 통해 SubAgent 간 지식을 전달하여 전체 보안 수준을 높인다
4. LLM 프롬프트에 로컬 지식을 포함하면 더 정확한 맥락 분석이 가능하다
5. 지식의 무결성과 최신성을 유지하기 위한 검증 메커니즘이 필요하다

---

## 다음 주 예고
- Week 14: RL Steering - 보상 함수 설계와 행동 통제
