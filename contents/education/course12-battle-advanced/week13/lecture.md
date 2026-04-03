# Week 13: 퍼플팀 — Red+Blue 협업, ATT&CK Gap 분석

## 학습 목표
- 퍼플팀(Purple Team)의 개념과 Red/Blue 팀 협업 방법론을 이해한다
- ATT&CK Gap 분석을 수행하여 조직의 탐지 커버리지를 평가할 수 있다
- Red 팀의 공격 기법과 Blue 팀의 탐지 규칙을 매핑할 수 있다
- 퍼플팀 연습을 계획하고 실행할 수 있다
- 탐지 개선 계획을 수립하고 OpsClaw로 자동화할 수 있다

## 선수 지식
- 공방전 기초 과정 이수
- Week 11 레드팀 운영 이해
- Week 12 블루팀 운영 이해

## 실습 환경

| 호스트 | IP | 역할 | 접속 |
|--------|-----|------|------|
| opsclaw | 10.20.30.201 | 퍼플팀 조율 | `ssh opsclaw@10.20.30.201` |
| secu | 10.20.30.1 | Blue 환경 (IPS) | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 공방전 대상 | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | 탐지 현황 대시보드 | `sshpass -p1 ssh siem@10.20.30.100` |

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:30 | 퍼플팀 이론 | 강의 |
| 0:30-1:10 | ATT&CK Gap 분석 실습 | 실습 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:20 | 퍼플팀 연습 (Red 공격 + Blue 탐지) | 실습 |
| 2:20-2:30 | 휴식 | - |
| 2:30-3:10 | 탐지 개선 계획 수립 | 실습 |
| 3:10-3:30 | 결과 분석 토론 + 퀴즈 | 토론 |

---

# Part 1: 퍼플팀 이론 (30분)

## 1.1 퍼플팀이란?

퍼플팀은 Red 팀과 Blue 팀이 **동시에 협업**하여 공격/방어 역량을 동시에 향상시키는 방법론이다.

```
기존 모델:
[Red Team] ──공격──→ [대상] ←──방어── [Blue Team]
               (독립 수행)              (독립 수행)

퍼플팀 모델:
[Red Team] ←──실시간 공유──→ [Blue Team]
     │                            │
     └──── 공동 분석/개선 ────┘
              ↓
      [탐지 커버리지 향상]
```

## 1.2 퍼플팀 프로세스

| 단계 | 활동 | 산출물 |
|------|------|--------|
| 1. 계획 | ATT&CK 기법 선정 | 테스트 매트릭스 |
| 2. 공격 | Red가 기법 실행 | 공격 로그 |
| 3. 탐지 | Blue가 실시간 탐지 시도 | 탐지/미탐 결과 |
| 4. 분석 | 공동 결과 분석 | Gap 리포트 |
| 5. 개선 | 탐지 규칙 추가/수정 | 업데이트된 규칙 |
| 6. 재검증 | 동일 기법 재실행 | 개선 확인 |

## 1.3 ATT&CK 기반 탐지 매트릭스

```
             | T1190 | T1059 | T1053 | T1071 | T1048 |
Suricata     |  [O]  |  [ ]  |  [ ]  |  [O]  |  [△]  |
Wazuh        |  [△]  |  [O]  |  [O]  |  [ ]  |  [ ]  |
fail2ban     |  [ ]  |  [ ]  |  [ ]  |  [ ]  |  [ ]  |
auditd       |  [ ]  |  [O]  |  [O]  |  [ ]  |  [ ]  |

[O] = 탐지 가능  [△] = 부분 탐지  [ ] = 미탐지 (Gap)
```

---

# Part 2: ATT&CK Gap 분석 실습 (40분)

## 실습 2.1: 현재 탐지 커버리지 평가

> **목적**: 현재 보안 도구의 ATT&CK 커버리지를 측정한다
> **배우는 것**: Gap 분석 방법론, 커버리지 매핑

```bash
# Suricata 규칙에서 탐지 가능한 ATT&CK 기법 추출
curl -X POST http://localhost:8000/projects/{id}/dispatch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{"command":"grep -r \"sid:\" /etc/suricata/rules/ | wc -l && grep -ri \"mitre\\|attack\" /etc/suricata/rules/ | head -10","subagent_url":"http://10.20.30.1:8002"}'

# Wazuh 규칙에서 MITRE 매핑 추출
curl -X POST http://localhost:8000/projects/{id}/dispatch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{"command":"grep -r \"<mitre>\" /var/ossec/ruleset/rules/ | grep -oP \"T[0-9]+\" | sort -u","subagent_url":"http://10.20.30.100:8002"}'
```

## 실습 2.2: Gap 식별

> **목적**: 탐지되지 않는 ATT&CK 기법을 식별한다
> **배우는 것**: 우선순위 기반 Gap 분석

```bash
# 테스트할 ATT&CK 기법 목록 (우선순위 기반)
cat << 'EOF'
Priority 1 (Critical):
  T1190 - Exploit Public-Facing Application
  T1059 - Command and Scripting Interpreter
  T1053 - Scheduled Task/Job
  T1071 - Application Layer Protocol (C2)

Priority 2 (High):
  T1048 - Exfiltration Over Alternative Protocol
  T1543 - Create or Modify System Process
  T1098 - Account Manipulation
  T1003 - OS Credential Dumping

Priority 3 (Medium):
  T1550 - Use Alternate Authentication Material
  T1558 - Steal or Forge Kerberos Tickets
EOF
```

---

# Part 3: 퍼플팀 연습 실행 (60분)

## 실습 3.1: 구조화된 퍼플팀 연습

> **목적**: Red 공격과 Blue 탐지를 동시에 실행하며 실시간으로 결과를 비교한다
> **배우는 것**: 퍼플팀 협업, 실시간 탐지 검증

```bash
# 퍼플팀 프로젝트 생성
curl -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "purple-team-exercise-01",
    "request_text": "퍼플팀 연습: T1190, T1059, T1053 탐지 검증",
    "master_mode": "external"
  }'

# Stage 전환
curl -X POST http://localhost:8000/projects/{id}/plan -H "X-API-Key: $OPSCLAW_API_KEY"
curl -X POST http://localhost:8000/projects/{id}/execute -H "X-API-Key: $OPSCLAW_API_KEY"

# Round 1: T1190 (웹 익스플로잇) 테스트
curl -X POST http://localhost:8000/projects/{id}/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {"order":1,"instruction_prompt":"[RED] curl \"http://10.20.30.80:3000/rest/products/search?q=test%27%20OR%201=1--\"","risk_level":"medium","subagent_url":"http://localhost:8002"},
      {"order":2,"instruction_prompt":"[BLUE] tail -20 /var/log/suricata/fast.log","risk_level":"low","subagent_url":"http://10.20.30.1:8002"},
      {"order":3,"instruction_prompt":"[BLUE] cat /var/ossec/logs/alerts/alerts.json | jq -r \"select(.rule.mitre.id[]? == \\\"T1190\\\") | .rule.description\" | tail -5","risk_level":"low","subagent_url":"http://10.20.30.100:8002"}
    ],
    "subagent_url":"http://localhost:8002"
  }'

# Round 2: T1053 (Cron Persistence) 테스트
curl -X POST http://localhost:8000/projects/{id}/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {"order":1,"instruction_prompt":"[RED] echo \"*/5 * * * * /tmp/test_beacon.sh\" | crontab - 2>/dev/null; crontab -l","risk_level":"medium","subagent_url":"http://10.20.30.80:8002"},
      {"order":2,"instruction_prompt":"[BLUE] cat /var/ossec/logs/alerts/alerts.json | jq -r \"select(.rule.mitre.id[]? == \\\"T1053\\\") | .rule.description\" | tail -5","risk_level":"low","subagent_url":"http://10.20.30.100:8002"}
    ],
    "subagent_url":"http://localhost:8002"
  }'
```

---

# Part 4: 탐지 개선 계획 (40분)

## 4.1 Gap 분석 결과표

```markdown
| ATT&CK ID | 기법 | Red 결과 | Blue 탐지 | Gap |
|-----------|------|---------|----------|-----|
| T1190 | Exploit Web App | 성공 | Suricata 탐지 | 없음 |
| T1059 | Shell Execution | 성공 | auditd 탐지 | 부분 |
| T1053 | Cron Job | 성공 | Wazuh 탐지 | 없음 |
| T1071 | C2 HTTP | 성공 | 미탐지 | **Gap** |
| T1048 | DNS Exfil | 성공 | 미탐지 | **Gap** |
```

## 4.2 개선 계획 수립

```bash
# Gap에 대한 탐지 규칙 추가
# T1071 (C2 HTTP) 탐지 규칙
cat > /tmp/c2_detect.rules << 'EOF'
alert http $HOME_NET any -> $EXTERNAL_NET any (msg:"Potential C2 Beacon - Regular Interval"; flow:to_server; threshold:type both, track by_src, count 10, seconds 300; sid:4000001; rev:1;)
EOF

# T1048 (DNS Exfil) 탐지 규칙
cat >> /tmp/c2_detect.rules << 'EOF'
alert dns $HOME_NET any -> any any (msg:"Potential DNS Exfiltration"; dns.query; pcre:"/^[a-zA-Z0-9+\/=]{40,}\./"; sid:4000002; rev:1;)
EOF
```

---

## 검증 체크리스트
- [ ] 퍼플팀의 Red/Blue 협업 프로세스를 설명할 수 있다
- [ ] ATT&CK Gap 분석을 수행하여 탐지 커버리지를 측정할 수 있다
- [ ] 구조화된 퍼플팀 연습을 계획하고 실행할 수 있다
- [ ] Gap에 대한 탐지 규칙을 작성할 수 있다
- [ ] 개선 결과를 재검증하는 절차를 수행할 수 있다

## 자가 점검 퀴즈
1. 퍼플팀이 Red 팀과 Blue 팀의 독립 운영보다 효과적인 이유 3가지를 서술하시오.
2. ATT&CK Gap 분석에서 "부분 탐지"의 의미와 이를 개선하는 방법은?
3. 퍼플팀 연습에서 Red 팀이 Blue 팀에게 공격 기법을 사전 공개하는 것이 적절한 경우는?
4. 탐지 커버리지 100%가 현실적으로 불가능한 이유와 대안 전략은?
5. 퍼플팀 연습 결과를 경영진에게 보고할 때 포함해야 할 핵심 메트릭 5가지는?
