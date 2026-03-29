# OpsClaw SOC 보안 운영 가이드

## 1. 개요

이 문서는 OpsClaw를 SOC(Security Operations Center) 운영에 활용하는 방법을 다룬다.
Wazuh SIEM, Suricata IPS, nftables 방화벽을 OpsClaw로 통합 관리하는 실전 절차를 설명한다.

**인프라 구성:**

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  v-secu      │     │  v-web       │     │  v-siem      │
│ 192.168.0.108│     │ 192.168.0.110│     │ 192.168.0.109│
│ nftables     │     │ Apache       │     │ Wazuh 4.11.2 │
│ Suricata IPS │     │ JuiceShop    │     │ SIEM/분석     │
│ SubAgent:8002│     │ SubAgent:8002│     │ SubAgent:8002│
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │
       └────────────────────┼────────────────────┘
                            │
                   ┌────────▼────────┐
                   │  OpsClaw Manager │
                   │  :8000           │
                   │  Evidence/PoW/RL │
                   └──────────────────┘
```

**공통 설정:**

```bash
export OPSCLAW_API_KEY=opsclaw-api-key-2026
export MANAGER=http://localhost:8000
alias oc='curl -s -H "X-API-Key: $OPSCLAW_API_KEY" -H "Content-Type: application/json"'
SECU="http://192.168.0.108:8002"
WEB="http://192.168.0.110:8002"
SIEM="http://192.168.0.109:8002"
```

---

## 2. 알림 분석 워크플로

### 2.1 Wazuh 알림 → OpsClaw LLM 분석 → 트리아지

```
Wazuh 알림 발생
     │
     ▼
OpsClaw 프로젝트 생성 (자동 또는 수동)
     │
     ▼
알림 데이터 수집 (dispatch → v-siem)
     │
     ▼
LLM 분석 (OpsClaw /chat 또는 Master)
     │
     ▼
위험도 판정 (Critical/High/Medium/Low)
     │
     ├── Critical/High → 즉시 대응 (nftables 차단 등)
     ├── Medium → 추가 조사 후 판단
     └── Low → 기록만 (Evidence)
```

### 2.2 알림 수집 및 분석

```bash
# 프로젝트 생성
oc -X POST $MANAGER/projects \
  -d '{
    "name": "alert-triage-20260330",
    "request_text": "Wazuh 고위험 알림 분석 및 대응",
    "master_mode": "external"
  }'
PID="<project_id>"
oc -X POST $MANAGER/projects/$PID/plan
oc -X POST $MANAGER/projects/$PID/execute

# Wazuh 최근 고위험 알림 수집
oc -X POST $MANAGER/projects/$PID/dispatch \
  -d '{
    "command": "tail -500 /var/ossec/logs/alerts/alerts.json | python3 -c \"import json,sys; alerts=[json.loads(l) for l in sys.stdin if l.strip()]; high=[a for a in alerts if a.get(\\\"rule\\\",{}).get(\\\"level\\\",0)>=10]; print(f\\\"총 {len(alerts)}건 중 고위험 {len(high)}건\\\"); [print(json.dumps({\\\"rule_id\\\": a[\\\"rule\\\"][\\\"id\\\"], \\\"level\\\": a[\\\"rule\\\"][\\\"level\\\"], \\\"desc\\\": a[\\\"rule\\\"].get(\\\"description\\\",\\\"\\\"), \\\"srcip\\\": a.get(\\\"srcip\\\",\\\"-\\\"), \\\"ts\\\": a.get(\\\"timestamp\\\",\\\"\\\")}, ensure_ascii=False)) for a in high[-10:]]\"",
    "subagent_url": "'$SIEM'"
  }'
```

### 2.3 LLM 기반 알림 분석 (Chat API)

```bash
# OpsClaw Chat으로 프로젝트 컨텍스트 기반 분석 요청
oc -X POST $MANAGER/chat \
  -d '{
    "message": "이 프로젝트의 Evidence에서 수집된 Wazuh 알림을 분석해줘. 어떤 위협이 있고, 즉시 대응이 필요한 것은 무엇인가?",
    "context_type": "project",
    "context_id": "'$PID'"
  }'
```

---

## 3. Suricata 규칙 관리

### 3.1 현재 규칙 확인

```bash
oc -X POST $MANAGER/projects/$PID/dispatch \
  -d '{
    "command": "wc -l /etc/suricata/rules/*.rules && echo \"---\" && cat /etc/suricata/rules/local.rules",
    "subagent_url": "'$SECU'"
  }'
```

### 3.2 커스텀 규칙 추가

```bash
# SQL Injection 탐지 규칙 추가
oc -X POST $MANAGER/projects/$PID/execute-plan \
  -d '{
    "tasks": [
      {
        "order": 1,
        "title": "Suricata SQL Injection 규칙 추가",
        "instruction_prompt": "echo '\''alert http any any -> any any (msg:\"CUSTOM SQLi Attempt\"; flow:to_server,established; content:\"union\"; nocase; content:\"select\"; nocase; distance:0; sid:9000001; rev:1;)'\'' >> /etc/suricata/rules/local.rules && suricata -T -c /etc/suricata/suricata.yaml && echo \"Rule validation OK\"",
        "risk_level": "medium",
        "subagent_url": "'$SECU'"
      },
      {
        "order": 2,
        "title": "Suricata 규칙 리로드",
        "instruction_prompt": "kill -USR2 $(pidof suricata) && sleep 2 && tail -5 /var/log/suricata/suricata.log",
        "risk_level": "medium",
        "subagent_url": "'$SECU'"
      }
    ]
  }'
```

### 3.3 Suricata 알림 확인

```bash
oc -X POST $MANAGER/projects/$PID/dispatch \
  -d '{
    "command": "tail -50 /var/log/suricata/fast.log | tail -20",
    "subagent_url": "'$SECU'"
  }'
```

### 3.4 Suricata EVE JSON 분석

```bash
oc -X POST $MANAGER/projects/$PID/dispatch \
  -d '{
    "command": "tail -200 /var/log/suricata/eve.json | python3 -c \"import json,sys; events=[json.loads(l) for l in sys.stdin if l.strip()]; alerts=[e for e in events if e.get(\\\"event_type\\\")==\\\"alert\\\"]; print(f\\\"Alert count: {len(alerts)}\\\"); [print(f\\\"  [{a[\\\"alert\\\"][\\\"severity\\\"]}] {a[\\\"alert\\\"][\\\"signature\\\"]} src={a.get(\\\"src_ip\\\",\\\"-\\\")}\\\") for a in alerts[-10:]]\"",
    "subagent_url": "'$SECU'"
  }'
```

---

## 4. nftables 방화벽 관리

### 4.1 현재 규칙 확인

```bash
oc -X POST $MANAGER/projects/$PID/dispatch \
  -d '{"command": "nft list ruleset", "subagent_url": "'$SECU'"}'
```

### 4.2 IP 차단

```bash
# 단일 IP 차단
oc -X POST $MANAGER/projects/$PID/execute-plan \
  -d '{
    "tasks": [{
      "order": 1,
      "title": "악성 IP 차단",
      "instruction_prompt": "nft add rule inet filter input ip saddr 198.51.100.0/24 counter drop",
      "risk_level": "high",
      "subagent_url": "'$SECU'"
    }],
    "confirmed": true
  }'
```

### 4.3 포트 제한

```bash
# 특정 포트만 허용하고 나머지 차단
oc -X POST $MANAGER/projects/$PID/execute-plan \
  -d '{
    "tasks": [
      {
        "order": 1,
        "title": "SSH 접근 IP 제한",
        "instruction_prompt": "nft add rule inet filter input tcp dport 22 ip saddr != { 192.168.0.0/24, 10.0.0.0/8 } counter drop",
        "risk_level": "high",
        "subagent_url": "'$SECU'"
      },
      {
        "order": 2,
        "title": "규칙 확인",
        "instruction_prompt": "nft list chain inet filter input",
        "risk_level": "low",
        "subagent_url": "'$SECU'"
      }
    ],
    "confirmed": true
  }'
```

### 4.4 규칙 백업/복원

```bash
# 현재 규칙 백업
oc -X POST $MANAGER/projects/$PID/dispatch \
  -d '{
    "command": "nft list ruleset > /etc/nftables.backup.$(date +%Y%m%d) && echo \"Backup saved\"",
    "subagent_url": "'$SECU'"
  }'

# 규칙 복원 (위험도 높음)
oc -X POST $MANAGER/projects/$PID/execute-plan \
  -d '{
    "tasks": [{
      "order": 1,
      "title": "nftables 규칙 복원",
      "instruction_prompt": "nft -f /etc/nftables.backup.20260330 && nft list ruleset | head -20",
      "risk_level": "critical",
      "subagent_url": "'$SECU'"
    }],
    "confirmed": true
  }'
```

---

## 5. Wazuh 설정 관리

### 5.1 에이전트 상태 확인

```bash
oc -X POST $MANAGER/projects/$PID/dispatch \
  -d '{
    "command": "/var/ossec/bin/agent_control -l",
    "subagent_url": "'$SIEM'"
  }'
```

### 5.2 Wazuh 규칙 확인

```bash
oc -X POST $MANAGER/projects/$PID/dispatch \
  -d '{
    "command": "cat /var/ossec/etc/rules/local_rules.xml",
    "subagent_url": "'$SIEM'"
  }'
```

### 5.3 커스텀 Wazuh 규칙 추가

```bash
oc -X POST $MANAGER/projects/$PID/execute-plan \
  -d '{
    "tasks": [
      {
        "order": 1,
        "title": "Wazuh 커스텀 규칙 추가",
        "instruction_prompt": "cat >> /var/ossec/etc/rules/local_rules.xml << '\''RULES_EOF'\''
<group name=\"custom_ssh\">
  <rule id=\"100100\" level=\"12\">
    <if_sid>5763</if_sid>
    <match>Failed password</match>
    <description>SSH brute force - multiple failures from same IP</description>
    <group>authentication_failures,</group>
  </rule>
</group>
RULES_EOF
/var/ossec/bin/wazuh-analysisd -t && echo \"Rule syntax OK\"",
        "risk_level": "medium",
        "subagent_url": "'$SIEM'"
      },
      {
        "order": 2,
        "title": "Wazuh 재시작",
        "instruction_prompt": "systemctl restart wazuh-manager && sleep 3 && systemctl is-active wazuh-manager",
        "risk_level": "medium",
        "subagent_url": "'$SIEM'"
      }
    ]
  }'
```

### 5.4 Wazuh 로그 분석

```bash
# 최근 알림 통계
oc -X POST $MANAGER/projects/$PID/dispatch \
  -d '{
    "command": "tail -1000 /var/ossec/logs/alerts/alerts.json | python3 -c \"import json,sys,collections; alerts=[json.loads(l) for l in sys.stdin if l.strip()]; levels=collections.Counter(a.get(\\\"rule\\\",{}).get(\\\"level\\\",0) for a in alerts); print(\\\"Level distribution:\\\"); [print(f\\\"  Level {k}: {v}건\\\") for k,v in sorted(levels.items(), reverse=True)]\"",
    "subagent_url": "'$SIEM'"
  }'
```

---

## 6. 위협 인텔리전스 활용

### 6.1 IOC(Indicator of Compromise) 차단

```bash
# 위협 IP 목록 기반 일괄 차단
oc -X POST $MANAGER/projects/$PID/execute-plan \
  -d '{
    "tasks": [
      {
        "order": 1,
        "title": "IOC IP 목록 차단",
        "instruction_prompt": "for ip in 198.51.100.10 198.51.100.20 203.0.113.50; do nft add rule inet filter input ip saddr $ip counter drop; done && nft list chain inet filter input | grep -c drop && echo \"rules applied\"",
        "risk_level": "high",
        "subagent_url": "'$SECU'"
      },
      {
        "order": 2,
        "title": "Suricata IOC 규칙 추가",
        "instruction_prompt": "for ip in 198.51.100.10 198.51.100.20 203.0.113.50; do echo \"drop ip $ip any -> any any (msg:\\\"IOC blocked IP $ip\\\"; sid:$((RANDOM+9001000)); rev:1;)\" >> /etc/suricata/rules/local.rules; done && suricata -T -c /etc/suricata/suricata.yaml && echo \"Rules valid\"",
        "risk_level": "medium",
        "subagent_url": "'$SECU'"
      }
    ],
    "confirmed": true
  }'
```

### 6.2 의심 IP 조사

```bash
# 특정 IP의 활동 이력 조사
oc -X POST $MANAGER/projects/$PID/dispatch \
  -d '{
    "command": "echo \"=== Auth log ===\" && grep 203.0.113.50 /var/log/auth.log | tail -10 && echo \"=== nftables counters ===\" && nft list ruleset | grep -A1 203.0.113.50 && echo \"=== Suricata alerts ===\" && grep 203.0.113.50 /var/log/suricata/fast.log | tail -10",
    "subagent_url": "'$SECU'"
  }'
```

---

## 7. 자동 Blue Agent (5분 주기)

OpsClaw Watcher로 자동 방어 사이클을 구성한다.

### 7.1 Watcher 등록

```bash
# 5분마다 Wazuh 고위험 알림을 확인하고 자동 차단
oc -X POST $MANAGER/watchers \
  -d '{
    "project_name": "auto-blue-agent",
    "watch_type": "security_monitor",
    "metadata": {
      "interval_s": 300,
      "check_command": "tail -200 /var/ossec/logs/alerts/alerts.json | python3 -c \"import json,sys; alerts=[json.loads(l) for l in sys.stdin if l.strip()]; high=[a for a in alerts if a.get(\\\"rule\\\",{}).get(\\\"level\\\",0)>=12]; ips=set(a.get(\\\"srcip\\\",\\\"\\\") for a in high if a.get(\\\"srcip\\\")); print(len(ips)); [print(ip) for ip in ips]\"",
      "target": "'$SIEM'",
      "action_target": "'$SECU'",
      "auto_block": true
    }
  }'
```

### 7.2 자동 대응 흐름

```
매 5분:
  1. Wazuh에서 Level 12+ 알림 확인 (v-siem)
  2. 공격 IP 추출
  3. nftables에 자동 차단 규칙 추가 (v-secu)
  4. Evidence 기록 + PoW 블록 생성
  5. Slack/Email 알림 발송
```

---

## 8. PoW 리더보드와 팀 성과

### 8.1 에이전트별 성과 조회

```bash
# 전체 리더보드 (보상 순위)
oc $MANAGER/pow/leaderboard?limit=10

# 응답 예시
{
  "leaderboard": [
    {"agent_id": "http://192.168.0.108:8002", "balance": 45.2, "total_tasks": 50, "success_rate": 94.0},
    {"agent_id": "http://192.168.0.110:8002", "balance": 38.7, "total_tasks": 42, "success_rate": 90.5},
    {"agent_id": "http://192.168.0.109:8002", "balance": 35.1, "total_tasks": 38, "success_rate": 92.1}
  ]
}
```

### 8.2 SOC 팀 KPI 추적

```bash
# 에이전트별 상세 통계
oc "$MANAGER/rewards/agents?agent_id=$SECU"

# RL 정책 상태 (Q-learning 학습 결과)
oc $MANAGER/rl/policy

# 최적 risk_level 추천 (UCB1)
oc "$MANAGER/rl/recommend?agent_id=$SECU&risk_level=medium&exploration=ucb1"
```

### 8.3 성과 보고서 자동 생성

```bash
# 프로젝트 전체 보고서
oc $MANAGER/reports/project/$PID

# 감사 로그 내보내기
oc -X POST $MANAGER/admin/audit/export \
  -d '{"format": "json", "limit": 500}'
```

---

## 9. Notification 설정 (SOC 운영용)

### 9.1 채널 구성

```bash
# Slack 알림 채널
oc -X POST $MANAGER/notifications/channels \
  -d '{
    "name": "soc-slack",
    "channel_type": "slack",
    "config": {"channel": "#soc-alerts"}
  }'

# Email 알림 채널
oc -X POST $MANAGER/notifications/channels \
  -d '{
    "name": "soc-email",
    "channel_type": "email",
    "config": {
      "smtp_host": "smtp.company.com",
      "smtp_port": 587,
      "from": "soc@company.com",
      "to": ["soc-team@company.com"]
    }
  }'

# Webhook (SOAR 연동)
oc -X POST $MANAGER/notifications/channels \
  -d '{
    "name": "soar-webhook",
    "channel_type": "webhook",
    "config": {"url": "http://soar.internal:9090/api/incidents"}
  }'
```

### 9.2 규칙 구성

```bash
# 인시던트 생성 → Slack + Email
CH_SLACK="<slack channel_id>"
CH_EMAIL="<email channel_id>"

oc -X POST $MANAGER/notifications/rules \
  -d '{"name": "incident-slack", "event_type": "incident.created", "channel_id": "'$CH_SLACK'"}'

oc -X POST $MANAGER/notifications/rules \
  -d '{"name": "incident-email", "event_type": "incident.created", "channel_id": "'$CH_EMAIL'"}'

# 스케줄 실패 → Slack
oc -X POST $MANAGER/notifications/rules \
  -d '{"name": "schedule-fail-slack", "event_type": "schedule.failed", "channel_id": "'$CH_SLACK'"}'

# 모든 이벤트 → Webhook (SOAR)
CH_WEBHOOK="<webhook channel_id>"
oc -X POST $MANAGER/notifications/rules \
  -d '{"name": "all-to-soar", "event_type": "*", "channel_id": "'$CH_WEBHOOK'"}'
```

### 9.3 알림 테스트

```bash
# 테스트 이벤트 발사
oc -X POST $MANAGER/notifications/test \
  -d '{"event_type": "incident.created", "payload": {"summary": "SOC 알림 테스트", "severity": "high"}}'

# 발송 이력 확인
oc $MANAGER/notifications/logs?limit=10
```

---

## 10. SOC 일일 루틴

매일 수행해야 하는 SOC 운영 절차를 OpsClaw로 자동화한다.

```bash
# 일일 SOC 점검 프로젝트 생성
oc -X POST $MANAGER/projects \
  -d '{"name": "soc-daily-20260330", "request_text": "일일 SOC 점검", "master_mode": "external"}'
PID="<project_id>"
oc -X POST $MANAGER/projects/$PID/plan
oc -X POST $MANAGER/projects/$PID/execute

# 일일 점검 항목 일괄 실행
oc -X POST $MANAGER/projects/$PID/execute-plan \
  -d '{
    "parallel": true,
    "tasks": [
      {"order": 1, "title": "Wazuh 상태", "instruction_prompt": "systemctl is-active wazuh-manager && /var/ossec/bin/agent_control -l | grep -c Active", "risk_level": "low", "subagent_url": "'$SIEM'"},
      {"order": 2, "title": "Suricata 상태", "instruction_prompt": "systemctl is-active suricata && tail -5 /var/log/suricata/stats.log", "risk_level": "low", "subagent_url": "'$SECU'"},
      {"order": 3, "title": "nftables 규칙 수", "instruction_prompt": "nft list ruleset | grep -c rule", "risk_level": "low", "subagent_url": "'$SECU'"},
      {"order": 4, "title": "디스크 사용량", "instruction_prompt": "df -h / /var/log | tail -2", "risk_level": "low", "subagent_url": "'$SECU'"},
      {"order": 5, "title": "Apache 상태", "instruction_prompt": "systemctl is-active apache2 && curl -s -o /dev/null -w \"%{http_code}\" http://localhost/", "risk_level": "low", "subagent_url": "'$WEB'"}
    ]
  }'

# 결과 확인
oc $MANAGER/projects/$PID/evidence/summary

# 일일 보고서 자동 생성
oc -X POST $MANAGER/projects/$PID/completion-report \
  -d '{"auto": true}'
```
