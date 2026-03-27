# Week 10: Wazuh SIEM (2) — 탐지 룰

## 학습 목표

- Wazuh 룰의 XML 구조를 이해한다
- local_rules.xml에 커스텀 룰을 작성할 수 있다
- 디코더(decoder)의 역할을 이해하고 작성할 수 있다
- wazuh-logtest로 룰을 검증할 수 있다

---

## 1. Wazuh 룰 처리 흐름

```
로그 수신 → 디코더 (파싱) → 룰 매칭 → 알림 생성
```

| 단계 | 설명 |
|------|------|
| **디코더** | 원시 로그를 파싱하여 필드를 추출 (srcip, user, action 등) |
| **룰** | 추출된 필드를 조건과 비교하여 알림 생성 |

---

## 2. 실습 환경 접속

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.100
```

---

## 3. 기본 룰 구조

### 3.1 룰 파일 위치

```bash
echo 1 | sudo -S ls /var/ossec/ruleset/rules/ | head -20
echo 1 | sudo -S ls /var/ossec/etc/rules/
```

| 경로 | 설명 |
|------|------|
| `/var/ossec/ruleset/rules/` | Wazuh 기본 룰 (수정 금지) |
| `/var/ossec/etc/rules/local_rules.xml` | **커스텀 룰 (여기에 작성)** |

### 3.2 룰 XML 문법

```xml
<group name="그룹명,">
  <rule id="100001" level="5">
    <decoded_as>sshd</decoded_as>
    <match>Failed password</match>
    <description>SSH 로그인 실패</description>
  </rule>
</group>
```

| 요소 | 설명 |
|------|------|
| `id` | 룰 고유 ID (커스텀: 100000~) |
| `level` | 알림 레벨 (0~15) |
| `decoded_as` | 디코더 이름 매칭 |
| `match` | 로그 문자열 매칭 |
| `regex` | 정규표현식 매칭 |
| `srcip` | 출발지 IP 조건 |
| `user` | 사용자 조건 |
| `frequency` | 빈도 조건 (X초 내 Y회) |
| `timeframe` | 빈도 계산 시간 범위 |
| `if_sid` | 부모 룰 ID (연쇄 룰) |
| `if_matched_sid` | 빈도 기반 부모 룰 |
| `description` | 알림 설명 |
| `group` | 룰 그룹 (MITRE 매핑 등) |

---

## 4. 기본 룰 살펴보기

### 4.1 SSH 룰

```bash
echo 1 | sudo -S cat /var/ossec/ruleset/rules/0095-sshd_rules.xml | head -40
```

**예시:**
```xml
<group name="syslog,sshd,">
  <rule id="5710" level="5">
    <if_sid>5700</if_sid>
    <match>illegal user|invalid user</match>
    <description>sshd: Attempt to login using a non-existent user</description>
    <group>authentication_failed,</group>
  </rule>

  <rule id="5712" level="10" frequency="8" timeframe="120" ignore="60">
    <if_matched_sid>5710</if_matched_sid>
    <description>sshd: brute force trying to get access to the system. Non existent user.</description>
    <group>authentication_failures,</group>
  </rule>
</group>
```

> Rule 5712는 Rule 5710이 120초 내 8회 발생하면 Level 10 알림을 생성한다 (브루트포스 탐지).

### 4.2 웹 공격 룰

```bash
echo 1 | sudo -S cat /var/ossec/ruleset/rules/0260-nginx_rules.xml | head -30
```

---

## 5. 커스텀 룰 작성

### 5.1 local_rules.xml 확인

```bash
echo 1 | sudo -S cat /var/ossec/etc/rules/local_rules.xml
```

### 5.2 룰 1: 특정 사용자 로그인 감시

```bash
echo 1 | sudo -S tee /var/ossec/etc/rules/local_rules.xml << 'EOF'
<group name="local,custom,">

  <!-- 룰 1: root 사용자 SSH 로그인 -->
  <rule id="100001" level="10">
    <if_sid>5715</if_sid>
    <user>root</user>
    <description>경고: root 사용자 SSH 직접 로그인 감지</description>
    <group>authentication_success,pci_dss_10.2.5,</group>
  </rule>

  <!-- 룰 2: 업무시간 외 로그인 (22시~06시) -->
  <rule id="100002" level="8">
    <if_sid>5715</if_sid>
    <time>22:00-06:00</time>
    <description>주의: 업무시간 외 SSH 로그인 감지</description>
    <group>authentication_success,</group>
  </rule>

  <!-- 룰 3: sudo 실행 감시 -->
  <rule id="100003" level="5">
    <decoded_as>sudo</decoded_as>
    <match>COMMAND=</match>
    <description>sudo 명령 실행 감지</description>
    <group>audit,sudo,</group>
  </rule>

  <!-- 룰 4: 위험한 sudo 명령 -->
  <rule id="100004" level="12">
    <if_sid>100003</if_sid>
    <match>rm -rf|mkfs|dd if=|chmod 777|iptables -F</match>
    <description>심각: 위험한 sudo 명령 실행 감지</description>
    <group>audit,sudo,</group>
  </rule>

  <!-- 룰 5: 다수 인증 실패 후 성공 (침입 의심) -->
  <rule id="100005" level="12">
    <if_sid>5715</if_sid>
    <if_matched_sid>5710</if_matched_sid>
    <same_source_ip />
    <description>심각: 다수 인증 실패 후 로그인 성공 - 침입 의심</description>
    <group>authentication_success,attack,</group>
  </rule>

  <!-- 룰 6: Suricata 알림 연동 (높은 심각도) -->
  <rule id="100006" level="10">
    <decoded_as>json</decoded_as>
    <field name="event_type">alert</field>
    <field name="alert.severity">1</field>
    <description>Suricata 고심각도 알림 감지</description>
    <group>ids,suricata,</group>
  </rule>

  <!-- 룰 7: 새로운 서비스 포트 열림 -->
  <rule id="100007" level="7">
    <decoded_as>syslog</decoded_as>
    <match>Listening on</match>
    <description>새로운 네트워크 서비스 시작 감지</description>
    <group>service_start,</group>
  </rule>

  <!-- 룰 8: 패키지 설치 감시 -->
  <rule id="100008" level="7">
    <decoded_as>dpkg-decoder</decoded_as>
    <match>install </match>
    <description>새로운 패키지 설치 감지</description>
    <group>audit,software,</group>
  </rule>

</group>
EOF
```

### 5.3 룰 검증

```bash
echo 1 | sudo -S /var/ossec/bin/wazuh-analysisd -t
```

**예상 출력 (정상):**
```
wazuh-analysisd: Configuration check passed. Exiting.
```

오류가 있으면 해당 줄 번호와 메시지가 출력된다.

---

## 6. wazuh-logtest로 룰 테스트

### 6.1 logtest 실행

```bash
echo 1 | sudo -S /var/ossec/bin/wazuh-logtest
```

대화형 프롬프트가 나타난다. 로그 메시지를 입력하면 어떤 디코더와 룰이 매칭되는지 보여준다.

### 6.2 테스트 예시: SSH 로그인 실패

```
Type one log per line

Mar 27 10:30:15 secu sshd[12345]: Failed password for invalid user admin from 10.20.30.80 port 54321 ssh2
```

**예상 출력:**
```
**Phase 1: Completed pre-decoding.
       full event: 'Mar 27 10:30:15 secu sshd[12345]: Failed password for invalid user admin from 10.20.30.80 port 54321 ssh2'
       hostname: 'secu'
       program_name: 'sshd'

**Phase 2: Completed decoding.
       name: 'sshd'
       parent: 'sshd'
       srcip: '10.20.30.80'
       srcuser: 'admin'

**Phase 3: Completed filtering (rules).
       id: '5710'
       level: '5'
       description: 'sshd: Attempt to login using a non-existent user.'
       groups: '['syslog', 'sshd', 'authentication_failed']'
```

### 6.3 테스트 예시: root SSH 로그인 성공

```
Mar 27 10:35:00 secu sshd[12346]: Accepted password for root from 10.20.30.80 port 54322 ssh2
```

**예상 출력:**
```
**Phase 3: Completed filtering (rules).
       id: '100001'
       level: '10'
       description: '경고: root 사용자 SSH 직접 로그인 감지'
```

### 6.4 테스트 예시: 위험한 sudo 명령

```
Mar 27 10:40:00 secu sudo: user : TTY=pts/0 ; PWD=/home/user ; USER=root ; COMMAND=/bin/rm -rf /tmp/test
```

Ctrl+C로 logtest를 종료한다.

---

## 7. 디코더 (Decoder)

### 7.1 디코더란?

디코더는 원시 로그 메시지에서 구조화된 필드를 추출하는 파서이다.

```
원시 로그:  "Mar 27 10:30:15 secu sshd[12345]: Failed password for admin from 10.20.30.80"
           ↓ 디코더
추출 필드:  program=sshd, srcuser=admin, srcip=10.20.30.80
```

### 7.2 기본 디코더 확인

```bash
echo 1 | sudo -S cat /var/ossec/ruleset/decoders/0310-ssh_decoders.xml | head -30
```

### 7.3 커스텀 디코더 작성

애플리케이션 로그용 커스텀 디코더:

```bash
echo 1 | sudo -S tee /var/ossec/etc/decoders/local_decoder.xml << 'EOF'
<decoder name="opsclaw-app">
  <program_name>opsclaw</program_name>
</decoder>

<decoder name="opsclaw-app-fields">
  <parent>opsclaw-app</parent>
  <regex>user=(\S+) action=(\S+) target=(\S+) status=(\S+)</regex>
  <order>user, action, extra_data, status</order>
</decoder>

<decoder name="opsclaw-login">
  <parent>opsclaw-app</parent>
  <regex>LOGIN (\S+) from (\S+) status=(\S+)</regex>
  <order>user, srcip, status</order>
</decoder>
EOF
```

### 7.4 디코더와 연동된 룰

```bash
# local_rules.xml에 추가
echo 1 | sudo -S tee -a /var/ossec/etc/rules/local_rules.xml << 'RULEEOF'

<group name="opsclaw,">
  <rule id="100010" level="3">
    <decoded_as>opsclaw-app</decoded_as>
    <description>OpsClaw 애플리케이션 이벤트</description>
  </rule>

  <rule id="100011" level="5">
    <if_sid>100010</if_sid>
    <status>failed</status>
    <description>OpsClaw 로그인 실패</description>
  </rule>

  <rule id="100012" level="10" frequency="5" timeframe="120">
    <if_matched_sid>100011</if_matched_sid>
    <same_source_ip />
    <description>OpsClaw 브루트포스 공격 의심</description>
  </rule>
</group>
RULEEOF
```

### 7.5 디코더 테스트

```bash
echo 1 | sudo -S /var/ossec/bin/wazuh-logtest
```

입력:
```
Mar 27 11:00:00 siem opsclaw: LOGIN admin from 10.20.30.80 status=failed
```

**예상 출력:**
```
**Phase 2: Completed decoding.
       name: 'opsclaw-login'
       parent: 'opsclaw-app'
       srcip: '10.20.30.80'
       srcuser: 'admin'
       status: 'failed'

**Phase 3: Completed filtering (rules).
       id: '100011'
       level: '5'
       description: 'OpsClaw 로그인 실패'
```

---

## 8. 고급 룰 기법

### 8.1 복합 조건 (AND)

```xml
<rule id="100020" level="10">
  <if_sid>5715</if_sid>
  <srcip>!10.20.30.0/24</srcip>
  <user>root</user>
  <description>외부 IP에서 root SSH 접근</description>
</rule>
```

### 8.2 정규표현식 매칭

```xml
<rule id="100021" level="7">
  <decoded_as>syslog</decoded_as>
  <regex>CRON\[\d+\]: \(root\) CMD</regex>
  <description>root cron job 실행</description>
</rule>
```

### 8.3 연쇄 룰 (Composite)

```xml
<!-- 기본: 파일 변경 감지 -->
<rule id="100030" level="7">
  <if_sid>550</if_sid>
  <match>/etc/passwd</match>
  <description>passwd 파일 변경 감지</description>
</rule>

<!-- 연쇄: passwd 변경 후 새 프로세스 -->
<rule id="100031" level="12" timeframe="300">
  <if_sid>100030</if_sid>
  <description>passwd 변경 후 5분 이내 — 계정 추가 의심</description>
</rule>
```

### 8.4 MITRE ATT&CK 매핑

```xml
<rule id="100040" level="10">
  <if_sid>5712</if_sid>
  <description>SSH 브루트포스 공격</description>
  <mitre>
    <id>T1110.001</id>
  </mitre>
</rule>
```

---

## 9. 룰 적용 및 확인

### 9.1 설정 검증

```bash
echo 1 | sudo -S /var/ossec/bin/wazuh-analysisd -t
```

### 9.2 Manager 재시작

```bash
echo 1 | sudo -S systemctl restart wazuh-manager
echo 1 | sudo -S systemctl status wazuh-manager
```

### 9.3 알림 모니터링

```bash
echo 1 | sudo -S tail -f /var/ossec/logs/alerts/alerts.json | \
  python3 -c "
import sys, json
for line in sys.stdin:
    try:
        e = json.loads(line)
        r = e.get('rule',{})
        if int(r.get('id',0)) >= 100000:
            print(f\"[CUSTOM] Level {r['level']:>2} | Rule {r['id']} | {r['description']}\")
    except: pass
"
```

---

## 10. 실습 과제

### 과제 1: 커스텀 룰 작성

다음 이벤트를 탐지하는 룰을 작성하라:

1. `su` 명령으로 root 전환 시 Level 8 알림
2. `/etc/shadow` 파일 읽기 시도 시 Level 10 알림
3. 10분 내 SSH 로그인 실패 20회 시 Level 14 알림

### 과제 2: 커스텀 디코더 작성

다음 형식의 로그를 파싱하는 디코더를 작성하라:

```
Mar 27 12:00:00 web nginx: ACCESS src=10.20.30.80 method=GET uri=/admin status=403
```

추출할 필드: srcip, extra_data(method), url, status

### 과제 3: logtest 검증

작성한 디코더와 룰을 wazuh-logtest로 검증하라.

---

## 11. 핵심 정리

| 개념 | 설명 |
|------|------|
| Decoder | 원시 로그 → 구조화 필드 추출 |
| Rule | 필드 조건 매칭 → 알림 생성 |
| local_rules.xml | 커스텀 룰 파일 |
| local_decoder.xml | 커스텀 디코더 파일 |
| `if_sid` | 부모 룰 기반 연쇄 |
| `if_matched_sid` | 빈도 기반 연쇄 |
| `frequency/timeframe` | X초 내 Y회 발생 조건 |
| `wazuh-logtest` | 대화형 룰 테스트 도구 |
| `wazuh-analysisd -t` | 설정 검증 |
| 커스텀 ID 범위 | 100000~ |

---

## 다음 주 예고

Week 11에서는 Wazuh의 고급 기능을 다룬다:
- FIM (File Integrity Monitoring)
- SCA (Security Configuration Assessment)
- Active Response (자동 대응)
