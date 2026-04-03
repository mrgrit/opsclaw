# Week 12: 블루팀 운영 — SOC 구축, SOAR 자동화, IR 플레이북

## 학습 목표
- SOC(Security Operations Center)의 구성 요소와 운영 프로세스를 이해한다
- SOAR(Security Orchestration, Automation and Response) 자동화를 구현할 수 있다
- IR(Incident Response) 플레이북을 설계하고 OpsClaw로 자동화할 수 있다
- Wazuh SIEM 기반 알림 파이프라인을 구성할 수 있다
- SOC 메트릭(MTTD, MTTR)을 측정하고 개선할 수 있다

## 선수 지식
- 공방전 기초 과정 이수
- Week 06-08 방어/포렌식/위협 헌팅 이해
- SIEM 운영 기본

## 실습 환경

| 호스트 | IP | 역할 | 접속 |
|--------|-----|------|------|
| opsclaw | 10.20.30.201 | SOAR Control Plane | `ssh opsclaw@10.20.30.201` |
| secu | 10.20.30.1 | 방화벽/IPS | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 보호 대상 | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | Wazuh SIEM (SOC 핵심) | `sshpass -p1 ssh siem@10.20.30.100` |

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:35 | SOC 구축 이론 | 강의 |
| 0:35-1:10 | Wazuh 알림 파이프라인 구성 | 실습 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | IR 플레이북 설계 | 실습 |
| 2:00-2:40 | OpsClaw SOAR 자동화 실습 | 실습 |
| 2:40-2:50 | 휴식 | - |
| 2:50-3:30 | SOC 메트릭 분석 토론 + 퀴즈 | 토론 |

---

# Part 1: SOC 구축 이론 (35분)

## 1.1 SOC 구성 요소

```
                    [SOC Manager]
                         |
    ┌────────────────────┼────────────────────┐
    |                    |                    |
[Tier 1: Analyst]  [Tier 2: Analyst]  [Tier 3: Expert]
 알림 분류/필터링    심층 분석/조사      포렌식/헌팅
    |                    |                    |
    └────────────────────┼────────────────────┘
                         |
              [SIEM + SOAR Platform]
              (Wazuh + OpsClaw)
```

## 1.2 SOC 운영 프로세스

| 단계 | 활동 | 도구 |
|------|------|------|
| 1. 모니터링 | 알림 수신/분류 | SIEM (Wazuh) |
| 2. 분석 | 참/거짓 양성 판별 | 로그 분석, 위협 인텔 |
| 3. 대응 | 차단/격리/복구 | SOAR (OpsClaw) |
| 4. 보고 | 인시던트 문서화 | 보고서 템플릿 |
| 5. 개선 | 규칙 업데이트 | Lessons Learned |

## 1.3 핵심 SOC 메트릭

| 메트릭 | 정의 | 목표치 |
|--------|------|--------|
| MTTD | Mean Time to Detect (평균 탐지 시간) | < 1시간 |
| MTTR | Mean Time to Respond (평균 대응 시간) | < 4시간 |
| FPR | False Positive Rate (오탐률) | < 20% |
| Alert Volume | 일일 알림 수 | 관리 가능 수준 |

---

# Part 2: Wazuh 알림 파이프라인 (35분)

## 실습 2.1: Wazuh 커스텀 규칙 설정

> **목적**: 공격 시나리오에 맞는 탐지 규칙을 구성한다
> **배우는 것**: Wazuh 규칙 작성, 알림 레벨 설정

```bash
# Wazuh 커스텀 규칙 추가 (siem)
cat > /var/ossec/etc/rules/local_rules.xml << 'EOF'
<group name="custom_soc">
  <!-- SSH 브루트포스 탐지 (5회 이상) -->
  <rule id="100401" level="10" frequency="5" timeframe="120">
    <if_matched_sid>5710</if_matched_sid>
    <description>SOC Alert: SSH Brute Force Attack (5+ failures in 2min)</description>
    <mitre><id>T1110.001</id></mitre>
  </rule>

  <!-- 웹 SQL Injection 탐지 -->
  <rule id="100402" level="12">
    <if_sid>31100</if_sid>
    <url>union|select|insert|drop|update|delete</url>
    <description>SOC Alert: SQL Injection Attempt Detected</description>
    <mitre><id>T1190</id></mitre>
  </rule>

  <!-- 의심 프로세스 실행 -->
  <rule id="100403" level="10">
    <decoded_as>auditd</decoded_as>
    <field name="audit.exe">/usr/bin/nc|/usr/bin/ncat|/usr/bin/nmap</field>
    <description>SOC Alert: Suspicious Tool Execution</description>
    <mitre><id>T1059</id></mitre>
  </rule>
</group>
EOF

# 규칙 적용
systemctl restart wazuh-manager
```

## 실습 2.2: 알림 → Slack 연동

```bash
# Wazuh Active Response → OpsClaw → Slack 알림
curl -X POST http://localhost:8000/projects/{id}/dispatch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{"command":"cat /var/ossec/logs/alerts/alerts.json | tail -5 | jq .rule","subagent_url":"http://10.20.30.100:8002"}'
```

---

# Part 3: IR 플레이북 설계 (40분)

## 3.1 IR 플레이북 구조

```yaml
# playbook_ssh_bruteforce.yml
name: SSH Brute Force Response
trigger: Wazuh Rule 100401
severity: High
steps:
  1_identify:
    action: "공격 소스 IP 식별"
    command: "grep 'Failed password' /var/log/auth.log | awk '{print $(NF-3)}' | sort | uniq -c | sort -rn | head -5"
  2_contain:
    action: "공격 IP 차단"
    command: "nft add element inet filter blackhole { <attacker_ip> }"
    approval: auto  # 자동 실행
  3_investigate:
    action: "성공한 로그인 확인"
    command: "grep 'Accepted' /var/log/auth.log | grep <attacker_ip>"
  4_eradicate:
    action: "의심 세션 종료"
    command: "pkill -u <compromised_user>"
    approval: manual  # 수동 승인 필요
  5_recover:
    action: "비밀번호 초기화"
    command: "passwd --expire <compromised_user>"
  6_report:
    action: "인시던트 보고서 생성"
```

## 실습 3.1: OpsClaw IR 플레이북 실행

> **목적**: IR 플레이북을 OpsClaw execute-plan으로 자동화한다
> **배우는 것**: SOAR 자동화, 단계별 대응

```bash
# IR 플레이북 자동 실행
curl -X POST http://localhost:8000/projects/{id}/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {"order":1,"instruction_prompt":"grep \"Failed password\" /var/log/auth.log | awk \"{print $(NF-3)}\" | sort | uniq -c | sort -rn | head -5","risk_level":"low","subagent_url":"http://10.20.30.80:8002"},
      {"order":2,"instruction_prompt":"fail2ban-client status sshd","risk_level":"low","subagent_url":"http://10.20.30.80:8002"},
      {"order":3,"instruction_prompt":"last -20 | head -10","risk_level":"low","subagent_url":"http://10.20.30.80:8002"}
    ],
    "subagent_url":"http://localhost:8002"
  }'
```

---

# Part 4: SOAR 자동화 및 메트릭 (40분)

## 4.1 SOAR 자동화 워크플로우

```
[Wazuh 알림] → [OpsClaw 프로젝트 생성] → [IR 플레이북 실행]
     ↓                                          ↓
[알림 분류]                              [자동 대응 + 수동 승인]
     ↓                                          ↓
[Slack 알림]                             [완료 보고서 생성]
```

## 실습 4.1: MTTD/MTTR 측정

> **목적**: SOC 메트릭을 측정하고 개선 포인트를 식별한다
> **배우는 것**: SOC 운영 효율성 측정

```bash
# OpsClaw 프로젝트 타임라인으로 MTTR 계산
curl -H "X-API-Key: $OPSCLAW_API_KEY" \
  http://localhost:8000/projects/{id}/replay

# PoW 블록 타임스탬프로 대응 시간 분석
curl -H "X-API-Key: $OPSCLAW_API_KEY" \
  "http://localhost:8000/pow/blocks?limit=10" | \
  jq '[.[] | {task: .task_hash, ts: .timestamp}]'
```

---

## 검증 체크리스트
- [ ] SOC의 3-Tier 구조를 설명할 수 있다
- [ ] Wazuh 커스텀 규칙을 작성하고 적용할 수 있다
- [ ] IR 플레이북을 YAML/문서로 설계할 수 있다
- [ ] OpsClaw로 IR 플레이북을 자동 실행할 수 있다
- [ ] MTTD/MTTR 메트릭을 측정하고 해석할 수 있다

## 자가 점검 퀴즈
1. SOC Tier 1 분석가의 핵심 역할과 에스컬레이션 기준을 설명하시오.
2. SOAR가 SOC 운영 효율성을 개선하는 구체적인 방법 3가지는?
3. IR 플레이북에서 "자동 실행"과 "수동 승인" 단계를 구분하는 기준은?
4. MTTD를 단축하기 위한 기술적/조직적 방안 각 2가지를 제시하시오.
5. Alert Fatigue(알림 피로)를 줄이기 위한 전략 3가지를 서술하시오.
