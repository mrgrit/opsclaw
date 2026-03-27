# Week 14: 자동화 관제 - OpsClaw Agent Daemon

## 학습 목표
- AI 기반 자율 보안 관제의 개념을 이해한다
- OpsClaw Agent Daemon의 explore/daemon/stimulate 기능을 사용한다
- 자율 탐지 에이전트를 구성하고 자극 테스트를 수행한다
- 자동화 관제의 장점과 한계를 분석한다

---

## 1. 자동화 관제 개념

### 1.1 전통적 관제 vs AI 자동화 관제

| 항목 | 전통적 관제 | AI 자동화 관제 |
|------|-----------|--------------|
| 탐지 | 시그니처 룰 기반 | 시그니처 + AI 판단 |
| 분석 | 분석관 수동 분석 | LLM 자동 분석 + 분석관 검증 |
| 대응 | 매뉴얼 기반 | 자동 대응 + 승인 체계 |
| 24/7 | 교대 근무 필요 | 에이전트 상시 가동 |
| 확장성 | 인력 비례 | 에이전트 추가 |

### 1.2 OpsClaw Agent Daemon 아키텍처

```
+---------------------------------------------+
|              OpsClaw Manager API              |
|              (http://localhost:8000)           |
+-----------+-----------+-----------------------+
|           |           |                       |
|  Explore  |  Daemon   |  Stimulate            |
|  (탐색)    |  (감시)    |  (자극 테스트)         |
|           |           |                       |
|  환경 파악  |  주기적    |  의도적 공격           |
|  자산 조사  |  로그 조회  |  탐지 능력 검증        |
+-----------+-----------+-----------------------+
         |           |            |
         +-----------+------------+
                     |
              SubAgent (각 서버)
```

---

## 2. Explore: 환경 탐색

### 2.1 OpsClaw API로 환경 탐색

```bash
export OPSCLAW_API_KEY=opsclaw-api-key-2026

# 프로젝트 생성
echo "=== Phase 1: 프로젝트 생성 ==="
PROJECT=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{"name":"soc-explore-demo","request_text":"보안 관제 환경 탐색","master_mode":"external"}')
PROJECT_ID=$(echo "$PROJECT" | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")
echo "Project ID: $PROJECT_ID"

# Stage 전환
curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/plan" \
  -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null
curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/execute" \
  -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null
echo "Stage: execute"
```

### 2.2 secu 서버 탐색

```bash
export OPSCLAW_API_KEY=opsclaw-api-key-2026

echo "=== secu 서버 탐색 ==="
curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "hostname && uname -a && echo --- && ss -tlnp | head -10 && echo --- && systemctl list-units --type=service --state=running | grep -E \"suricata|nftables|wazuh|ssh\"",
        "risk_level": "low",
        "subagent_url": "http://192.168.208.150:8002"
      }
    ],
    "subagent_url": "http://192.168.208.150:8002"
  }' | python3 -c "
import json, sys
data = json.load(sys.stdin)
for r in data.get('results', []):
    print(f'Task {r.get(\"order\",\"?\")}: {r.get(\"status\",\"?\")}')
    output = r.get('output','')
    print(output[:500] if output else '(출력 없음)')
"
```

### 2.3 siem 서버 탐색

```bash
export OPSCLAW_API_KEY=opsclaw-api-key-2026

echo "=== siem 서버 탐색 ==="
curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "hostname && echo --- && systemctl status wazuh-manager 2>/dev/null | head -5 && echo --- && ls -la /var/ossec/logs/alerts/ 2>/dev/null | tail -5",
        "risk_level": "low",
        "subagent_url": "http://192.168.208.152:8002"
      }
    ],
    "subagent_url": "http://192.168.208.152:8002"
  }' | python3 -c "
import json, sys
data = json.load(sys.stdin)
for r in data.get('results', []):
    print(f'Task {r.get(\"order\",\"?\")}: {r.get(\"status\",\"?\")}')
    print(r.get('output','')[:500])
"
```

---

## 3. Daemon: 주기적 관제 순환

### 3.1 관제 순환 스크립트

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 << 'ENDSSH'
cat << 'SCRIPT' > /tmp/soc_daemon.sh
#!/bin/bash
OLLAMA_URL="http://192.168.0.105:11434/v1/chat/completions"

echo "=== SOC Daemon 시작 ($(date)) ==="

# 1. Suricata 최신 경보 수집
echo "[1] Suricata 경보 수집"
SURICATA_ALERTS=$(sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.1 \
  "tail -20 /var/log/suricata/fast.log 2>/dev/null" 2>/dev/null)
echo "  수집: $(echo "$SURICATA_ALERTS" | wc -l)줄"

# 2. Wazuh 최신 경보 수집
echo "[2] Wazuh 경보 수집"
WAZUH_ALERTS=$(sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.100 \
  "tail -5 /var/ossec/logs/alerts/alerts.json 2>/dev/null" 2>/dev/null)
echo "  수집: $(echo "$WAZUH_ALERTS" | wc -l)줄"

# 3. LLM 분석
echo "[3] LLM 분석 요청"
ANALYSIS=$(curl -s "$OLLAMA_URL" \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"gemma3:12b\",
    \"messages\": [
      {\"role\": \"system\", \"content\": \"SOC L1 자동 분석 에이전트입니다. 경보를 분석하여 심각도와 대응 필요 여부를 판단합니다. 한국어로 간결하게.\"},
      {\"role\": \"user\", \"content\": \"보안 경보 분석:\\nSuricata: ${SURICATA_ALERTS:-(없음)}\\nWazuh: ${WAZUH_ALERTS:-(없음)}\\n\\n1) 요약 2) 위험도 3) 대응 필요 여부\"}
    ],
    \"temperature\": 0.2
  }" 2>/dev/null | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])" 2>/dev/null)

echo ""
echo "=== LLM 분석 결과 ==="
echo "$ANALYSIS"
SCRIPT

chmod +x /tmp/soc_daemon.sh
bash /tmp/soc_daemon.sh
ENDSSH
```

### 3.2 경보 임계값 기반 에스컬레이션

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 << 'ENDSSH'
python3 << 'PYEOF'
alerts = [
    {"time": "09:01", "source": "suricata", "severity": "low", "desc": "HTTP 스캔 탐지"},
    {"time": "09:02", "source": "suricata", "severity": "low", "desc": "포트 스캔 탐지"},
    {"time": "09:03", "source": "suricata", "severity": "medium", "desc": "SQL Injection 시도"},
    {"time": "09:04", "source": "wazuh", "severity": "medium", "desc": "SSH 인증 실패 (3회)"},
    {"time": "09:05", "source": "suricata", "severity": "high", "desc": "리버스셸 탐지"},
    {"time": "09:06", "source": "wazuh", "severity": "high", "desc": "파일 무결성 변경"},
    {"time": "09:07", "source": "wazuh", "severity": "critical", "desc": "root 계정 로그인"},
]

THRESHOLDS = {"critical": 1, "high": 2, "medium": 5, "low": 10}

counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
for a in alerts:
    counts[a["severity"]] += 1

print("=== 경보 에스컬레이션 분석 ===")
print(f"총 경보: {len(alerts)}건\n")

escalate = False
for sev in ["critical", "high", "medium", "low"]:
    t = THRESHOLDS[sev]
    c = counts[sev]
    status = "ESCALATE" if c >= t else "OK"
    if c >= t: escalate = True
    print(f"  {sev:<10} {c}건 / 임계값 {t} -> [{status}]")

print(f"\n판정: {'에스컬레이션 - SOC L2 호출' if escalate else '정상'}")

if escalate:
    print("\n에스컬레이션 사유:")
    for a in alerts:
        if a["severity"] in ["critical", "high"]:
            print(f"  [{a['time']}] [{a['severity'].upper()}] {a['desc']}")
PYEOF
ENDSSH
```

---

## 4. Stimulate: 자극 테스트

### 4.1 탐지 능력 검증

```bash
export OPSCLAW_API_KEY=opsclaw-api-key-2026

echo "=== 자극 테스트: 포트 스캔 ==="
curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/dispatch" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "command": "for port in 22 80 443 3306 5432 8080; do timeout 1 bash -c \"echo > /dev/tcp/10.20.30.1/$port\" 2>/dev/null && echo \"Port $port: OPEN\" || echo \"Port $port: CLOSED\"; done",
    "subagent_url": "http://192.168.208.151:8002"
  }' | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('output','')[:300])"
```

### 4.2 SQL Injection 자극

```bash
export OPSCLAW_API_KEY=opsclaw-api-key-2026

echo "=== 자극: SQLi 시도 ==="
curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/dispatch" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "command": "curl -s -o /dev/null -w \"%{http_code}\" \"http://localhost:3000/rest/products/search?q=test%27+OR+1=1--\" && echo \" (SQLi 전송)\"",
    "subagent_url": "http://192.168.208.151:8002"
  }' | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('output','')[:200])"
```

### 4.3 탐지 확인

```bash
export OPSCLAW_API_KEY=opsclaw-api-key-2026

echo "=== 탐지 확인: Suricata ==="
curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/dispatch" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "command": "tail -10 /var/log/suricata/fast.log 2>/dev/null | grep -iE \"sql|scan|injection\" || echo \"관련 경보 없음\"",
    "subagent_url": "http://192.168.208.150:8002"
  }' | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('output','')[:300])"
```

---

## 5. 자동 대응 파이프라인

### 5.1 탐지-분석-대응 자동화

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 << 'ENDSSH'
python3 << 'PYEOF'
def detect(log_entry):
    keywords = {
        "critical": ["reverse shell", "root login", "data exfiltration"],
        "high": ["sql injection", "brute force", "privilege escalation"],
        "medium": ["port scan", "directory traversal", "xss"],
        "low": ["404 error", "invalid user agent"],
    }
    for severity, patterns in keywords.items():
        for pattern in patterns:
            if pattern in log_entry.lower():
                return severity, pattern
    return "info", "unknown"

def respond(severity, pattern):
    if severity == "critical":
        return f"[AUTO] 즉시 차단 + SOC L2 알림 ({pattern})"
    elif severity == "high":
        return f"[MANUAL] SOC L1 분석 필요 ({pattern})"
    else:
        return f"[LOG] 기록 ({pattern})"

test_logs = [
    "192.168.1.100: Reverse Shell connection on port 4444",
    "10.0.0.5: SQL Injection attempt on /api/login",
    "172.16.0.1: Port scan detected (SYN, 100 ports)",
    "192.168.1.50: 404 error on /nonexistent",
    "10.0.0.10: Root login from unknown IP",
]

print("=== 탐지-분석-대응 파이프라인 ===\n")
for log in test_logs:
    severity, pattern = detect(log)
    action = respond(severity, pattern)
    print(f"로그: {log[:60]}...")
    print(f"  탐지: {severity.upper()} ({pattern})")
    print(f"  대응: {action}\n")
PYEOF
ENDSSH
```

---

## 6. 자동화 관제의 한계와 인간 역할

### 6.1 역할 분담

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 << 'ENDSSH'
python3 << 'PYEOF'
roles = {
    "자동화(AI) 담당": [
        "대량 로그 수집 및 정규화",
        "알려진 패턴 매칭 (시그니처)",
        "반복적 1차 분류 (L1 티켓팅)",
        "IOC 자동 업데이트 및 매칭",
        "정기 보고서 자동 생성",
        "규칙 기반 자동 차단",
    ],
    "인간(분석관) 담당": [
        "제로데이 공격 분석",
        "비즈니스 컨텍스트 판단",
        "오탐/정탐 최종 판별",
        "법적/규제 대응 결정",
        "위협 헌팅 가설 수립",
        "경영진 커뮤니케이션",
        "사고 대응 의사결정",
    ],
}

for role, tasks in roles.items():
    print(f"\n{role}")
    print("=" * 40)
    for task in tasks:
        print(f"  - {task}")

print("\n핵심: AI는 인간을 '대체'가 아닌 '증강(augment)'한다")
PYEOF
ENDSSH
```

---

## 핵심 정리

1. OpsClaw Agent Daemon은 explore/daemon/stimulate 3단계로 자율 관제한다
2. LLM은 경보 1차 분석과 분류를 자동화하여 분석관 부담을 줄인다
3. 에스컬레이션 임계값으로 자동 경보 분류와 상위 통보를 구현한다
4. 자극 테스트로 탐지 능력을 지속적으로 검증해야 한다
5. 자동 대응 파이프라인은 탐지-분석-대응을 연결한다
6. AI는 인간을 대체가 아닌 증강하며, 최종 판단은 인간이 수행한다

---

## 다음 주 예고
- Week 15: 기말 종합 인시던트 대응 훈련 - Red Team vs Blue Team
