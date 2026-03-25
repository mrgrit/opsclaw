# Blue Team: SIEM 기반 탐지 + 대응

## 개요

Red Team의 4 Tier 공격에 대해 **모든 탐지가 Wazuh SIEM을 통해 시작**되어야 함.
방어 = 탐지 룰 생성, 시그니처 작성, 대응 플레이북 구축.
방화벽 차단으로 원천 봉쇄하는 것은 방어로 인정하지 않음.

---

## 방어 체인 (필수 프로세스)

```
1. Wazuh SIEM 경보 확인 (alerts.json)
2. 경보 분석 → 공격 유형 식별 (ATT&CK ID 매핑)
3. 탐지 룰 생성:
   - SIGMA 룰 (SIEM 범용)
   - Suricata 시그니처 (IPS)
   - ModSecurity 룰 (WAF)
   - AuditD/Sysmon 룰 (호스트)
4. 룰 배포 + 활성화
5. 동일 공격 재실행 → 새 룰로 탐지 성공 검증
6. 인시던트 보고서 작성
```

---

## Tier 1 방어: Web Application 공격 대응

### 1-1. SQLi 탐지 강화

```yaml
# SIGMA 룰: SQL Injection 탐지 (웹 로그 기반)
title: SQL Injection Attempt via Web Parameter
id: custom-sqli-detect-001
status: experimental
logsource:
  category: webserver
  product: apache
detection:
  selection:
    cs-uri-query|contains:
      - 'UNION+SELECT'
      - 'UNION%20SELECT'
      - 'information_schema'
      - 'LOAD_FILE'
      - "'+OR+'"
  condition: selection
level: high
tags:
  - attack.initial_access
  - attack.t1190
```

```
# Suricata 시그니처: SQLi 패턴
alert http any any -> $HOME_NET any (msg:"CUSTOM SQLi - UNION SELECT detected"; \
  flow:established,to_server; \
  content:"UNION"; nocase; content:"SELECT"; nocase; distance:0; within:20; \
  sid:1000001; rev:1; classtype:web-application-attack;)

alert http any any -> $HOME_NET any (msg:"CUSTOM SQLi - information_schema access"; \
  flow:established,to_server; \
  content:"information_schema"; nocase; \
  sid:1000002; rev:1; classtype:web-application-attack;)
```

```
# ModSecurity 룰: 웹쉘 업로드 탐지
SecRule FILES_NAMES "@rx \.(php|phtml|php5|phar)$" \
  "id:2000001,phase:2,deny,status:403,\
   msg:'PHP file upload attempt - potential webshell',\
   tag:'attack-webshell',severity:CRITICAL"
```

### 1-2. 웹쉘 탐지

```yaml
# SIGMA 룰: 웹쉘 실행 탐지 (Sysmon 프로세스 기반)
title: Web Shell Command Execution
id: custom-webshell-001
status: experimental
logsource:
  product: linux
  category: process_creation
detection:
  selection:
    ParentImage|endswith:
      - '/apache2'
      - '/httpd'
      - '/nginx'
    Image|endswith:
      - '/bash'
      - '/sh'
      - '/python3'
  condition: selection
level: critical
tags:
  - attack.execution
  - attack.t1059.004
  - attack.persistence
  - attack.t1505.003
```

---

## Tier 2 방어: 네트워크 공격 대응

### 2-1. DNS 터널링 탐지

```
# Suricata 시그니처: 긴 DNS 쿼리 (터널링 징후)
alert dns any any -> any any (msg:"CUSTOM DNS Tunneling - Long subdomain"; \
  dns.query; content:"."; offset:40; \
  sid:1000010; rev:1; classtype:policy-violation;)

alert dns any any -> any any (msg:"CUSTOM DNS Tunneling - High frequency"; \
  flow:to_server; threshold:type both,track by_src,count 50,seconds 60; \
  sid:1000011; rev:1; classtype:policy-violation;)
```

```yaml
# SIGMA 룰: DNS 터널링 패턴
title: Potential DNS Tunneling Activity
id: custom-dns-tunnel-001
logsource:
  product: suricata
  category: dns
detection:
  selection:
    dns.query|re: '^[a-z0-9]{30,}\.'
  condition: selection
level: high
tags:
  - attack.command_and_control
  - attack.t1572
```

### 2-2. ICMP 터널링 탐지

```
# Suricata: 대용량 ICMP 페이로드
alert icmp any any -> $HOME_NET any (msg:"CUSTOM ICMP Tunnel - Large payload"; \
  dsize:>512; \
  sid:1000020; rev:1; classtype:policy-violation;)
```

### 2-3. HTTP C2 비콘 탐지

```yaml
# SIGMA 룰: HTTP 비콘 패턴 (주기적 접근)
title: Potential HTTP C2 Beacon
id: custom-c2-beacon-001
logsource:
  category: webserver
detection:
  selection:
    cs-cookie|contains: '='
    cs-uri|endswith:
      - '.png'
      - '.gif'
      - '.jpg'
  timeframe: 5m
  condition: selection | count() > 10
level: high
tags:
  - attack.command_and_control
  - attack.t1071.001
```

---

## Tier 3 방어: 권한 상승 + 지속성 대응

### 3-1. SUID 악용 탐지

```yaml
# SIGMA 룰: SUID 바이너리 탐색 (find -perm)
title: SUID Binary Enumeration
id: custom-suid-enum-001
logsource:
  product: linux
  category: process_creation
detection:
  selection:
    CommandLine|contains:
      - '-perm -4000'
      - '-perm -u+s'
      - '-perm /4000'
  condition: selection
level: medium
tags:
  - attack.discovery
  - attack.t1548.001
```

### 3-2. 지속성 메커니즘 탐지

```yaml
# Wazuh 커스텀 룰: crontab 변경 탐지
# /var/ossec/etc/rules/local_rules.xml
<group name="custom_persistence">
  <rule id="100010" level="12">
    <decoded_as>syscheck</decoded_as>
    <field name="file">/var/spool/cron|/etc/cron</field>
    <description>Crontab modification detected - potential persistence</description>
    <mitre>
      <id>T1053.003</id>
    </mitre>
  </rule>

  <rule id="100011" level="14">
    <decoded_as>syscheck</decoded_as>
    <field name="file">/etc/passwd|/etc/shadow</field>
    <description>Account file modification - potential account manipulation</description>
    <mitre>
      <id>T1136.001</id>
    </mitre>
  </rule>
</group>
```

---

## Tier 4 방어: 탐지 우회 공격 대응

### 4-1. Agent 무력화 대응

```yaml
# Wazuh Manager 측 룰: Agent 비활성 탐지
# 이미 내장 룰 존재 (rule_id: 504, 505) — alert level 상향
<group name="custom_agent_monitor">
  <rule id="100020" level="15">
    <if_sid>504</if_sid>
    <description>CRITICAL: Wazuh agent disconnected - possible evasion (T1562.001)</description>
    <mitre>
      <id>T1562.001</id>
    </mitre>
  </rule>
</group>
```

### 4-2. 난독화 실행 탐지

```yaml
# SIGMA 룰: Base64 decode → 실행 체인
title: Base64 Encoded Command Execution
id: custom-obfuscation-001
logsource:
  product: linux
  category: process_creation
detection:
  selection:
    CommandLine|contains:
      - 'base64 -d | bash'
      - 'base64 -d | sh'
      - "eval \"$("
      - '/dev/shm/'
  condition: selection
level: high
tags:
  - attack.defense_evasion
  - attack.t1027
```

---

## OpsClaw 실행 방식 (Blue Team Project)

```bash
# Blue Team 프로젝트 — Playbook으로 체계적 대응
BLUE_PRJ=$(curl -s -X POST http://localhost:8000/projects \
  -d '{"name":"blue-tier1-response","request_text":"Tier 1 공격 탐지 대응","master_mode":"external"}')

# execute-plan으로 탐지 + 분석 + 룰 배포
curl -s -X POST "http://localhost:8000/projects/$PRJ_ID/execute-plan" \
  -d '{
    "tasks": [
      {"order":1,"title":"SIEM 경보 수집","instruction_prompt":"sshpass -p 1 ssh siem@192.168.0.109 \"cat /var/ossec/logs/alerts/alerts.json | tail -50\"","risk_level":"low"},
      {"order":2,"title":"공격 유형 분석","instruction_prompt":"sshpass -p 1 ssh siem@192.168.0.109 \"grep -i sqli /var/ossec/logs/alerts/alerts.json | tail -10\"","risk_level":"low"},
      {"order":3,"title":"SIGMA 룰 배포","instruction_prompt":"sshpass -p 1 ssh siem@192.168.0.109 \"echo 1 | sudo -S cp /tmp/sigma_sqli.yml /opt/sigma/rules/custom/\"","risk_level":"medium"},
      {"order":4,"title":"Suricata 시그니처 배포","instruction_prompt":"sshpass -p 1 ssh secu@192.168.0.111 \"echo 1 | sudo -S cp /tmp/custom.rules /var/lib/suricata/rules/ && sudo suricata-update\"","risk_level":"high"},
      {"order":5,"title":"검증 — 동일 공격 재실행","instruction_prompt":"curl -s http://10.20.30.80/?id=1+UNION+SELECT+1,2,3--","risk_level":"low"}
    ],
    "subagent_url":"http://localhost:8002",
    "parallel":false
  }'
# → 모든 방어 행위가 PoW 블록으로 기록
# → experience로 자동 승급 (reward threshold 충족 시)
```

---

## 비교: OpsClaw vs Claude Code vs Codex

| 방어 활동 | OpsClaw | Claude Code | Codex |
|----------|---------|-------------|-------|
| 경보 수집 | execute-plan 태스크 | 직접 SSH | 직접 SSH |
| 룰 생성 | Playbook step으로 체계화 | 수동 작성 | 수동 작성 |
| 룰 배포 | parallel dispatch (여러 서버 동시) | 순차 SSH | 순차 |
| 검증 | execute-plan → PoW 기록 | 수동 확인 | 수동 확인 |
| 증적 | PoW 블록 + evidence + experience | 터미널 로그 | 세션 로그 |
| 재사용 | RAG로 다음 Tier 방어에 경험 주입 | 없음 | 없음 |
