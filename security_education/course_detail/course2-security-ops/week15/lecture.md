# Week 15: 기말고사 — 보안 인프라 구축 (상세 버전)

## 학습 목표

- 각 개념의 보안 관점에서의 위험과 대응 방안을 분석할 수 있다
- OpsClaw를 활용하여 실습 작업을 자동화하고 증적을 관리할 수 있다
- 실제 보안 사고 사례와 연결하여 학습 내용을 적용할 수 있다


## 실습 환경 (공통)

| 서버 | IP | 역할 | 접속 |
|------|-----|------|------|
| opsclaw | 10.20.30.201 | Control Plane (OpsClaw) | `ssh opsclaw@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS (nftables, Suricata) | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 웹서버 (JuiceShop:3000, Apache:80) | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh:443, OpenCTI:9400) | `sshpass -p1 ssh siem@10.20.30.100` |
| dgx-spark | 192.168.0.105 | AI/GPU (Ollama:11434) | 원격 API만 |

**OpsClaw API:** `http://localhost:8000` / Key: `opsclaw-api-key-2026`


## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | 이론 강의 (Part 1) | 강의 |
| 0:40-1:10 | 이론 심화 + 사례 분석 (Part 2) | 강의/토론 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | 실습 (Part 3) | 실습 |
| 2:00-2:40 | 심화 실습 + 도구 활용 (Part 4) | 실습 |
| 2:40-2:50 | 휴식 | - |
| 2:50-3:20 | 응용 실습 + OpsClaw 연동 (Part 5) | 실습 |
| 3:20-3:40 | 복습 퀴즈 + 과제 안내 (Part 6) | 퀴즈 |

---


---

## 용어 해설 (보안 솔루션 운영 과목)

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **방화벽** | Firewall | 네트워크 트래픽을 규칙에 따라 허용/차단하는 시스템 | 건물 출입 통제 시스템 |
| **체인** | Chain (nftables) | 패킷 처리 규칙의 묶음 (input, forward, output) | 심사 단계 |
| **룰/규칙** | Rule | 특정 조건의 트래픽을 어떻게 처리할지 정의 | "택배 기사만 출입 허용" |
| **시그니처** | Signature | 알려진 공격 패턴을 식별하는 규칙 (IPS/AV) | 수배범 얼굴 사진 |
| **NFQUEUE** | Netfilter Queue | 커널에서 사용자 영역으로 패킷을 넘기는 큐 | 의심 택배를 별도 검사대로 보내는 것 |
| **FIM** | File Integrity Monitoring | 파일 변조 감시 (해시 비교) | CCTV로 금고 감시 |
| **SCA** | Security Configuration Assessment | 보안 설정 점검 (CIS 벤치마크 기반) | 건물 안전 점검표 |
| **Active Response** | Active Response | 탐지 시 자동 대응 (IP 차단 등) | 침입 감지 시 자동 잠금 |
| **디코더** | Decoder (Wazuh) | 로그를 파싱하여 구조화하는 규칙 | 외국어 통역사 |
| **CRS** | Core Rule Set (ModSecurity) | 범용 웹 공격 탐지 규칙 모음 | 표준 보안 검사 매뉴얼 |
| **CTI** | Cyber Threat Intelligence | 사이버 위협 정보 (IOC, TTPs) | 범죄 정보 공유 시스템 |
| **IOC** | Indicator of Compromise | 침해 지표 (악성 IP, 해시, 도메인 등) | 수배범의 지문, 차량번호 |
| **STIX** | Structured Threat Information eXpression | 위협 정보 표준 포맷 | 범죄 보고서 표준 양식 |
| **TAXII** | Trusted Automated eXchange of Intelligence Information | CTI 자동 교환 프로토콜 | 경찰서 간 수배 정보 공유 시스템 |
| **NAT** | Network Address Translation | 내부 IP를 외부 IP로 변환 | 회사 대표번호 (내선→외선) |
| **masquerade** | masquerade (nftables) | 나가는 패킷의 소스 IP를 게이트웨이 IP로 변환 | 회사 이름으로 편지 보내기 |


# 본 강의 내용

# Week 15: 기말고사 — 보안 인프라 구축

## 시험 개요

- **유형**: 종합 실기 시험 (hands-on practical exam)
- **시간**: 120분
- **범위**: Week 02~14 전체 (nftables, Suricata, BunkerWeb, Wazuh, OpenCTI)
- **환경**: secu(10.20.30.1), web(10.20.30.80), siem(10.20.30.100)
- **배점**: 총 100점

---

## 시험 환경

| 서버 | IP | 접속 |
|------|-----|------|
| secu | 10.20.30.1 | `sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.1` |
| web | 10.20.30.80 | `sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80` |
| siem | 10.20.30.100 | `sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.100` |

**전제 조건**: 시험 시작 시 모든 보안 설정이 초기화되어 있다. 처음부터 구축해야 한다.

---

## Part 1: 네트워크 방화벽 구축 (25점)

### 문제 1-1: secu 서버 방화벽 구성 (15점)

secu 서버에 **화이트리스트 정책** 방화벽을 구축하라.

**테이블 이름**: `inet final_filter`

**요구사항:**

1. (3점) 기본 정책: input=drop, forward=drop, output=accept
2. (3점) conntrack (established, related 허용 / invalid 차단)
3. (2점) 루프백 허용
4. (3점) 허용 서비스:
   - SSH (22/tcp) — 전체 허용
   - HTTP (80/tcp), HTTPS (443/tcp) — 내부(10.20.30.0/24)에서만
   - Wazuh Agent → Manager (1514/tcp) — siem(10.20.30.100)으로만
5. (2점) ICMP ping 허용
6. (2점) 차단 로그: prefix `[FW-DROP]`

**정답 예시:**

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.1

echo 1 | sudo -S nft add table inet final_filter

# input chain
echo 1 | sudo -S nft add chain inet final_filter input \
  '{ type filter hook input priority 0; policy drop; }'
echo 1 | sudo -S nft add rule inet final_filter input ct state established,related accept
echo 1 | sudo -S nft add rule inet final_filter input ct state invalid drop
echo 1 | sudo -S nft add rule inet final_filter input iif lo accept
echo 1 | sudo -S nft add rule inet final_filter input tcp dport 22 accept
echo 1 | sudo -S nft add rule inet final_filter input ip saddr 10.20.30.0/24 tcp dport { 80, 443 } accept
echo 1 | sudo -S nft add rule inet final_filter input icmp type echo-request accept
echo 1 | sudo -S nft add rule inet final_filter input log prefix "[FW-DROP] " level warn

# forward chain
echo 1 | sudo -S nft add chain inet final_filter forward \
  '{ type filter hook forward priority 0; policy drop; }'
echo 1 | sudo -S nft add rule inet final_filter forward ct state established,related accept
echo 1 | sudo -S nft add rule inet final_filter forward ip saddr 10.20.30.0/24 accept

# output chain
echo 1 | sudo -S nft add chain inet final_filter output \
  '{ type filter hook output priority 0; policy accept; }'
```

### 문제 1-2: NAT 구성 (10점)

**테이블 이름**: `inet final_nat`

1. (5점) 내부(10.20.30.0/24) → 외부: masquerade
2. (5점) 외부 8080 → web(10.20.30.80):80 포트 포워딩

**정답 예시:**

```bash
echo 1 | sudo -S nft add table inet final_nat
echo 1 | sudo -S nft add chain inet final_nat prerouting \
  '{ type nat hook prerouting priority -100; policy accept; }'
echo 1 | sudo -S nft add chain inet final_nat postrouting \
  '{ type nat hook postrouting priority 100; policy accept; }'
echo 1 | sudo -S nft add rule inet final_nat postrouting ip saddr 10.20.30.0/24 masquerade
echo 1 | sudo -S nft add rule inet final_nat prerouting tcp dport 8080 dnat to 10.20.30.80:80
echo 1 | sudo -S sysctl -w net.ipv4.ip_forward=1

# 룰셋 저장
echo 1 | sudo -S nft list ruleset > /tmp/final_nftables.conf
```

---

## Part 2: Suricata IPS 구성 (20점)

### 문제 2-1: NFQUEUE 연동 (5점)

nftables에서 forward 트래픽을 NFQUEUE로 전달하여 Suricata가 검사하도록 구성하라.

```bash
echo 1 | sudo -S nft add table inet final_ips
echo 1 | sudo -S nft add chain inet final_ips forward \
  '{ type filter hook forward priority -1; policy accept; }'
echo 1 | sudo -S nft add rule inet final_ips forward queue num 0 bypass
```

### 문제 2-2: 탐지 룰 작성 (10점)

다음 5개 공격을 탐지하는 룰을 `/etc/suricata/rules/local.rules`에 작성하라:

1. (2점) SQL Injection (URI에 `union select`)
2. (2점) XSS (URI에 `<script`)
3. (2점) 디렉터리 트래버설 (URI에 `../`)
4. (2점) 스캐너 탐지 (User-Agent에 `nikto` 또는 `sqlmap`)
5. (2점) /etc/passwd 접근 차단 (**drop**)

**정답 예시:**

```bash
echo 1 | sudo -S tee /etc/suricata/rules/local.rules << 'EOF'
alert http $HOME_NET any -> any any (msg:"FINAL - SQL Injection"; flow:to_server,established; http.uri; content:"union"; nocase; content:"select"; nocase; distance:0; sid:9500001; rev:1;)

alert http $HOME_NET any -> any any (msg:"FINAL - XSS"; flow:to_server,established; http.uri; content:"<script"; nocase; sid:9500002; rev:1;)

alert http $HOME_NET any -> any any (msg:"FINAL - Directory Traversal"; flow:to_server,established; http.uri; content:"../"; sid:9500003; rev:1;)

alert http any any -> $HOME_NET any (msg:"FINAL - Scanner nikto"; flow:to_server,established; http.user_agent; content:"nikto"; nocase; sid:9500004; rev:1;)
alert http any any -> $HOME_NET any (msg:"FINAL - Scanner sqlmap"; flow:to_server,established; http.user_agent; content:"sqlmap"; nocase; sid:9500005; rev:1;)

drop http any any -> $HOME_NET any (msg:"FINAL - Block /etc/passwd"; flow:to_server,established; http.uri; content:"/etc/passwd"; sid:9500006; rev:1;)
EOF
```

### 문제 2-3: 검증 및 적용 (5점)

```bash
# 검증
echo 1 | sudo -S suricata -T -c /etc/suricata/suricata.yaml

# 리로드
echo 1 | sudo -S kill -USR2 $(pidof suricata)

# 테스트
curl -s "http://10.20.30.80/?q=1%20union%20select%201" > /dev/null
curl -s "http://10.20.30.80/?q=%3Cscript%3E" > /dev/null
curl -s -A "sqlmap/1.0" "http://10.20.30.80/" > /dev/null

# 결과 확인
echo 1 | sudo -S tail -10 /var/log/suricata/fast.log
```

---

## Part 3: Wazuh SIEM 구성 (25점)

### 문제 3-1: Agent 연결 확인 (5점)

secu, web 서버의 Wazuh Agent가 Manager에 연결되어 있는지 확인하라. 연결이 끊어져 있으면 복구하라.

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.100

echo 1 | sudo -S /var/ossec/bin/agent_control -l
```

### 문제 3-2: 커스텀 탐지 룰 (10점)

`/var/ossec/etc/rules/local_rules.xml`에 다음 룰을 작성하라:

1. (3점) root SSH 직접 로그인 — Level 10
2. (3점) 위험한 sudo 명령 (rm -rf, chmod 777) — Level 12
3. (4점) SSH 실패 10회 후 성공 — Level 14 (침입 의심)

**정답 예시:**

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.100

echo 1 | sudo -S tee /var/ossec/etc/rules/local_rules.xml << 'EOF'
<group name="final_exam,">

  <rule id="100100" level="10">
    <if_sid>5715</if_sid>
    <user>root</user>
    <description>FINAL: root SSH 직접 로그인 감지</description>
    <group>authentication_success,</group>
  </rule>

  <rule id="100101" level="5">
    <decoded_as>sudo</decoded_as>
    <match>COMMAND=</match>
    <description>FINAL: sudo 명령 실행</description>
  </rule>

  <rule id="100102" level="12">
    <if_sid>100101</if_sid>
    <match>rm -rf|chmod 777</match>
    <description>FINAL: 위험한 sudo 명령 실행 감지</description>
    <group>audit,</group>
  </rule>

  <rule id="100103" level="14">
    <if_sid>5715</if_sid>
    <if_matched_sid>5710</if_matched_sid>
    <same_source_ip />
    <description>FINAL: SSH 다수 실패 후 로그인 성공 - 침입 의심</description>
    <group>authentication_success,attack,</group>
  </rule>

</group>
EOF

# 검증
echo 1 | sudo -S /var/ossec/bin/wazuh-analysisd -t

# 재시작
echo 1 | sudo -S systemctl restart wazuh-manager
```

### 문제 3-3: FIM 설정 (5점)

secu 서버에서 다음 경로를 FIM 실시간 감시하도록 설정하라:

- `/etc/passwd`, `/etc/shadow`
- `/etc/nftables.conf`
- `/etc/suricata/rules/`

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.1

# ossec.conf에 syscheck 추가 (기존 설정에 병합)
echo 1 | sudo -S tee -a /var/ossec/etc/ossec.conf << 'FEOF'
<ossec_config>
  <syscheck>
    <directories realtime="yes" check_all="yes">/etc/passwd,/etc/shadow</directories>
    <directories realtime="yes" check_all="yes" report_changes="yes">/etc/nftables.conf</directories>
    <directories realtime="yes" check_all="yes" report_changes="yes">/etc/suricata/rules</directories>
  </syscheck>
</ossec_config>
FEOF

echo 1 | sudo -S systemctl restart wazuh-agent
```

### 문제 3-4: Active Response (5점)

SSH 브루트포스(Rule 5712) 탐지 시 공격자 IP를 10분간 자동 차단하도록 Active Response를 설정하라.

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.100

# ossec.conf에 Active Response 추가
echo 1 | sudo -S tee -a /var/ossec/etc/ossec.conf << 'AREOF'
<ossec_config>
  <command>
    <name>firewall-drop</name>
    <executable>firewall-drop</executable>
    <timeout_allowed>yes</timeout_allowed>
  </command>

  <active-response>
    <command>firewall-drop</command>
    <location>local</location>
    <rules_id>5712</rules_id>
    <timeout>600</timeout>
  </active-response>
</ossec_config>
AREOF

echo 1 | sudo -S systemctl restart wazuh-manager
```

---

## Part 4: CTI 연동 (15점)

### 문제 4-1: IOC 등록 (5점)

다음 IOC를 STIX 번들로 생성하여 OpenCTI에 등록하라:

| IOC | 유형 | 이름 |
|-----|------|------|
| 198.51.100.10 | IPv4 | APT-C2-Server-1 |
| 198.51.100.20 | IPv4 | APT-C2-Server-2 |
| malware-update.example.com | Domain | APT-Phishing-Domain |

**정답 예시:**

```bash
cat << 'STIXEOF' > /tmp/final_iocs.json
{
  "type": "bundle",
  "id": "bundle--final-exam-001",
  "objects": [
    {
      "type": "indicator",
      "spec_version": "2.1",
      "id": "indicator--final-001",
      "created": "2026-03-27T00:00:00.000Z",
      "modified": "2026-03-27T00:00:00.000Z",
      "name": "APT-C2-Server-1",
      "pattern": "[ipv4-addr:value = '198.51.100.10']",
      "pattern_type": "stix",
      "valid_from": "2026-03-27T00:00:00.000Z",
      "labels": ["malicious-activity"]
    },
    {
      "type": "indicator",
      "spec_version": "2.1",
      "id": "indicator--final-002",
      "created": "2026-03-27T00:00:00.000Z",
      "modified": "2026-03-27T00:00:00.000Z",
      "name": "APT-C2-Server-2",
      "pattern": "[ipv4-addr:value = '198.51.100.20']",
      "pattern_type": "stix",
      "valid_from": "2026-03-27T00:00:00.000Z",
      "labels": ["malicious-activity"]
    },
    {
      "type": "indicator",
      "spec_version": "2.1",
      "id": "indicator--final-003",
      "created": "2026-03-27T00:00:00.000Z",
      "modified": "2026-03-27T00:00:00.000Z",
      "name": "APT-Phishing-Domain",
      "pattern": "[domain-name:value = 'malware-update.example.com']",
      "pattern_type": "stix",
      "valid_from": "2026-03-27T00:00:00.000Z",
      "labels": ["malicious-activity"]
    }
  ]
}
STIXEOF
```

### 문제 4-2: IOC를 보안 장비에 배포 (10점)

등록한 IOC를 다음 보안 장비에 배포하라:

1. (4점) Suricata 룰로 변환하여 적용
2. (3점) nftables 차단 목록에 추가
3. (3점) Wazuh CDB 리스트로 변환

**정답 예시:**

```bash
# 1. Suricata 룰
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.1

echo 1 | sudo -S tee -a /etc/suricata/rules/local.rules << 'EOF'
alert ip $HOME_NET any -> 198.51.100.10 any (msg:"FINAL-CTI: APT C2 #1"; sid:9600001; rev:1; classtype:trojan-activity;)
alert ip $HOME_NET any -> 198.51.100.20 any (msg:"FINAL-CTI: APT C2 #2"; sid:9600002; rev:1; classtype:trojan-activity;)
alert dns $HOME_NET any -> any any (msg:"FINAL-CTI: APT Phishing Domain"; dns.query; content:"malware-update.example.com"; nocase; sid:9600003; rev:1;)
EOF
echo 1 | sudo -S kill -USR2 $(pidof suricata)

# 2. nftables 차단
echo 1 | sudo -S nft add set inet final_filter cti_block '{ type ipv4_addr; }'
echo 1 | sudo -S nft add element inet final_filter cti_block '{ 198.51.100.10, 198.51.100.20 }'
echo 1 | sudo -S nft insert rule inet final_filter input ip saddr @cti_block drop
echo 1 | sudo -S nft insert rule inet final_filter output ip daddr @cti_block drop

# 3. Wazuh CDB
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.100
echo 1 | sudo -S tee /var/ossec/etc/lists/final-cti-ips << 'EOF'
198.51.100.10:APT-C2-1
198.51.100.20:APT-C2-2
EOF
```

---

## Part 5: 종합 검증 (15점)

### 문제 5-1: 공격 시뮬레이션 및 탐지 확인 (10점)

다음 공격을 실행하고, 각 보안 계층에서 탐지/차단되는 것을 확인하라.

```bash
# 공격 1: SQL Injection
curl -s "http://10.20.30.80/?id=1%20UNION%20SELECT%201,2" > /dev/null

# 공격 2: XSS
curl -s "http://10.20.30.80/?q=%3Cscript%3Ealert(1)%3C/script%3E" > /dev/null

# 공격 3: 스캐너
curl -s -A "nikto/2.1.6" "http://10.20.30.80/" > /dev/null

# 공격 4: C2 통신 시도 (차단 확인)
curl -s --connect-timeout 3 "http://198.51.100.10/" > /dev/null 2>&1
```

**채점 기준:**

| 확인 항목 | 배점 |
|-----------|------|
| nftables 로그에 C2 IP 차단 기록 | 2점 |
| Suricata fast.log에 SQL Injection 탐지 | 2점 |
| Suricata fast.log에 XSS 탐지 | 2점 |
| BunkerWeb 403 응답 확인 | 2점 |
| Wazuh 알림에 탐지 기록 | 2점 |

### 문제 5-2: 인시던트 대응 보고서 (5점)

공격 시뮬레이션의 결과를 바탕으로 인시던트 대응 보고서를 작성하라.

**필수 포함 항목:**

1. (1점) 탐지 시간 및 공격 유형 요약
2. (1점) 공격자 IP 및 타겟 정보
3. (1점) 각 보안 계층의 탐지/차단 결과
4. (1점) 수행한 대응 조치
5. (1점) 향후 개선 권장사항

**보고서 템플릿:**

```bash
cat << 'REPORTEOF' > /tmp/final_incident_report.txt
========================================
인시던트 대응 보고서
========================================
날짜: 2026-03-27
작성자: [학번/이름]
인시던트 ID: FINAL-2026-001

1. 요약
   - 탐지 시간: [HH:MM]
   - 공격 유형: SQL Injection, XSS, 스캐너, C2 통신 시도
   - 심각도: 높음

2. 공격 정보
   - 공격자 IP: [IP]
   - 타겟: web (10.20.30.80) HTTP 서비스
   - 공격 벡터: HTTP 파라미터 조작, 악성 User-Agent

3. 탐지 결과
   - nftables: C2 IP(198.51.100.10) 차단 확인 ☑
   - Suricata: SQL Injection(SID:9500001), XSS(SID:9500002) 탐지 ☑
   - BunkerWeb: 403 Forbidden 응답으로 공격 차단 ☑
   - Wazuh: 알림 생성 확인, Level [X] ☑

4. 대응 조치
   - 공격자 IP를 CTI IOC로 등록
   - nftables 차단 목록에 추가
   - Suricata 룰 강화

5. 권장사항
   - WAF Paranoia Level 상향 검토
   - SSH 키 기반 인증으로 전환
   - 정기적 CTI IOC 업데이트 자동화
========================================
REPORTEOF

cat /tmp/final_incident_report.txt
```

---

## 채점 기준 요약

| Part | 내용 | 배점 |
|------|------|------|
| 1 | 네트워크 방화벽 (nftables) | 25점 |
| 2 | Suricata IPS | 20점 |
| 3 | Wazuh SIEM (룰, FIM, AR) | 25점 |
| 4 | CTI 연동 (IOC 등록, 배포) | 15점 |
| 5 | 종합 검증 + 보고서 | 15점 |
| **합계** | | **100점** |

---

## 시험 종료 후 정리

```bash
# secu 서버 정리
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.1 << 'CLEANUP'
echo 1 | sudo -S nft delete table inet final_filter 2>/dev/null
echo 1 | sudo -S nft delete table inet final_nat 2>/dev/null
echo 1 | sudo -S nft delete table inet final_ips 2>/dev/null
echo 1 | sudo -S sed -i '/FINAL/d' /etc/suricata/rules/local.rules 2>/dev/null
echo 1 | sudo -S kill -USR2 $(pidof suricata) 2>/dev/null
CLEANUP

# siem 서버 정리
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.100 << 'CLEANUP2'
echo 1 | sudo -S cp /var/ossec/etc/rules/local_rules.xml /tmp/local_rules_backup.xml
CLEANUP2
```

---

## 자주 하는 실수 및 주의사항

| 실수 | 결과 | 예방법 |
|------|------|--------|
| SSH 허용 전 policy drop | 연결 끊김 | conntrack + SSH 허용을 가장 먼저 |
| Suricata sid 중복 | 룰 로드 실패 | 고유 sid 범위 사용 |
| Wazuh rule id 중복 | analysisd 오류 | 100000+ 범위에서 순차 부여 |
| ossec.conf XML 문법 오류 | Manager 시작 실패 | analysisd -t로 검증 |
| FIM 경로 오타 | 감시 미동작 | 절대 경로 사용 |
| Active Response timeout 미설정 | 영구 차단 | 반드시 timeout 지정 |
| ip_forward 미활성화 | NAT/포워딩 미동작 | sysctl 확인 |
| 룰 리로드 안 함 | 새 룰 미적용 | kill -USR2 또는 restart |

---

## 학기 총 정리

이번 학기에 배운 내용:

| 주차 | 주제 | 핵심 기술 |
|------|------|-----------|
| 02-03 | nftables 방화벽 | 테이블/체인/룰, NAT, 화이트리스트 |
| 04-06 | Suricata IPS | NFQUEUE, 룰 작성, 운영/튜닝 |
| 07 | BunkerWeb WAF | ModSecurity CRS, 커스텀 룰 |
| 08 | 중간고사 | FW + IPS 종합 |
| 09-11 | Wazuh SIEM | 룰/디코더, FIM, SCA, Active Response |
| 12-13 | OpenCTI | STIX/TAXII, IOC 관리, 위협 헌팅 |
| 14 | 통합 아키텍처 | 심층 방어, 상관분석, 인시던트 대응 |
| 15 | 기말고사 | 전체 보안 인프라 구축 |

**핵심 교훈**: 단일 보안 장비로는 충분하지 않다. **심층 방어 + 통합 모니터링 + 위협 인텔리전스**를 결합해야 실효적인 보안을 달성할 수 있다.


---

## 심화 학습: 개념 확장

### 핵심 개념 상세 해설

이 주차에서 다루는 핵심 개념들을 더 깊이 살펴본다.

#### 개념 1: 동작 원리 (Course 2)

이 주차에서 다루는 기술의 동작 방식을 단계별로 분해하여 이해한다.

```
[1단계] 입력/요청 → 시스템이 데이터를 수신
[2단계] 처리 → 내부 로직에 의한 데이터 처리
[3단계] 출력/응답 → 결과 반환 또는 상태 변경
[4단계] 기록 → 로그/증적 생성
```

> **왜 이 순서가 중요한가?**
> 각 단계에서 보안 검증이 누락되면 취약점이 발생한다.
> 1단계: 입력값 검증 미흡 → Injection
> 2단계: 인가 확인 누락 → Broken Access Control
> 3단계: 에러 정보 노출 → Information Disclosure
> 4단계: 로깅 실패 → Monitoring Failures

#### 개념 2: 보안 관점에서의 위험 분석

| 위험 요소 | 발생 조건 | 영향도 | 대응 방안 |
|----------|---------|--------|---------|
| 설정 미흡 | 기본 설정 사용 | 높음 | 보안 하드닝 가이드 적용 |
| 패치 누락 | 업데이트 미적용 | 높음 | 정기 패치 관리 프로세스 |
| 접근 제어 부재 | 인증/인가 미구현 | 매우 높음 | RBAC, MFA 적용 |
| 로깅 미흡 | 감사 로그 미수집 | 중간 | SIEM 연동, 로그 정책 |

#### 개념 3: 실제 사례 분석

**사례 1: 유사 취약점이 실제 피해로 이어진 경우**

실제 보안 사고에서 이 주차의 주제가 어떻게 악용되었는지 살펴본다.
공격자는 동일한 기법을 사용하여 대규모 데이터 유출, 서비스 장애, 금전적 피해를 초래하였다.

**교훈:**
- 기본적인 보안 조치의 중요성
- 탐지 체계의 필수성
- 사고 대응 절차의 사전 수립 필요성

### 도구 비교표

| 도구 | 용도 | 장점 | 단점 | 라이선스 |
|------|------|------|------|---------|
| 도구 A | 기본 점검 | 간편, 빠름 | 기능 제한 | 오픈소스 |
| 도구 B | 심층 분석 | 상세 결과 | 학습 곡선 | 상용/무료 |
| 도구 C | 자동화 | CI/CD 연동 | 오탐 가능 | 오픈소스 |


---

## 보충 실습

### 보충 실습 1: 기본 동작 확인

이론에서 배운 내용을 직접 확인하는 기초 실습이다.

```bash
# Step 1: 현재 상태 확인
echo "=== 현재 상태 ==="
# (해당 주차에 맞는 확인 명령)

# Step 2: 설정/변경 적용
echo "=== 변경 적용 ==="
# (해당 주차에 맞는 실습 명령)

# Step 3: 결과 검증
echo "=== 결과 확인 ==="
# (변경 결과 확인 명령)
```

> **트러블슈팅:**
> - 명령이 실패하면: 권한(sudo), 경로, 서비스 상태를 먼저 확인
> - 예상과 다른 결과: 이전 실습의 설정이 남아있을 수 있으므로 초기화 후 재시도
> - 타임아웃: 네트워크 연결 또는 서비스 가동 상태 확인

### 보충 실습 2: 탐지/모니터링 관점

공격자가 아닌 **방어자 관점**에서 동일한 활동을 모니터링하는 실습이다.

```bash
# siem 서버에서 관련 로그 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100 \
  "sudo cat /var/ossec/logs/alerts/alerts.json | tail -5" 2>/dev/null

# Suricata 알림 확인 (해당 시)
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \
  "sudo tail -20 /var/log/suricata/fast.log" 2>/dev/null
```

> **왜 방어자 관점도 배우는가?**
> 공격 기법만 알면 "스크립트 키디"에 불과하다.
> 공격이 어떻게 탐지되는지 이해해야 진정한 보안 전문가이다.
> 이 과목의 모든 공격 실습에는 대응하는 탐지/방어 관점이 포함된다.

### 보충 실습 3: OpsClaw 자동화

이번 주차의 핵심 실습을 OpsClaw execute-plan으로 자동화한다.

```bash
# 프로젝트 생성 (이번 주차용)
RESULT=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"name":"weekXX-lab","request_text":"이번 주차 실습 자동화","master_mode":"external"}')
PID=$(echo $RESULT | python3 -c "import sys,json; print(json.load(sys.stdin)['project']['id'])")

# Stage 전환
curl -s -X POST "http://localhost:8000/projects/$PID/plan" -H "X-API-Key: opsclaw-api-key-2026" > /dev/null
curl -s -X POST "http://localhost:8000/projects/$PID/execute" -H "X-API-Key: opsclaw-api-key-2026" > /dev/null

# 실습 태스크 실행 (해당 주차에 맞게 수정)
curl -s -X POST "http://localhost:8000/projects/$PID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "tasks": [
      {"order":1,"title":"실습 태스크 1","instruction_prompt":"echo 실습1","risk_level":"low","subagent_url":"http://localhost:8002"},
      {"order":2,"title":"실습 태스크 2","instruction_prompt":"echo 실습2","risk_level":"low","subagent_url":"http://10.20.30.80:8002"}
    ],
    "subagent_url":"http://localhost:8002",
    "parallel":true
  }'

# Evidence 확인
curl -s "http://localhost:8000/projects/$PID/evidence/summary" \
  -H "X-API-Key: opsclaw-api-key-2026" | python3 -m json.tool
```


---

## 자가 점검 퀴즈 (10문항)

이번 주차의 핵심 내용을 점검한다. 8/10 이상 정답을 목표로 한다.

**Q1.** 이번 주차 "Week 15: 기말고사 — 보안 인프라 구축"의 핵심 목적은 무엇인가?
- (a) 네트워크 속도 향상  (b) **보안 솔루션 기법/개념의 이해와 실습**  (c) 데이터베이스 관리  (d) UI 디자인

**Q2.** 이 주제에서 방화벽/IPS의 역할은?
- (a) 성능 최적화  (b) 비용 절감  (c) **체계적 분류와 대응 기준 제공**  (d) 사용자 편의

**Q3.** 실습에서 사용한 주요 도구/명령어의 1차 목적은?
- (a) 파일 복사  (b) **SIEM 수행 및 결과 확인**  (c) 메모리 관리  (d) 화면 출력

**Q4.** OpsClaw를 통해 실습을 실행하는 가장 큰 이점은?
- (a) 속도  (b) **모든 실행의 자동 증적(evidence) 기록**  (c) 무료  (d) 간편함

**Q5.** 이 주제의 보안 위험이 높은 이유는?
- (a) 비용이 많이 들어서  (b) 복잡해서  (c) **악용 시 시스템/데이터에 직접적 피해**  (d) 법적 문제

**Q6.** 방어/대응의 핵심 원칙은?
- (a) 모든 트래픽 차단  (b) **최소 권한 + 탐지 + 대응의 조합**  (c) 서버 재시작  (d) 비밀번호 변경

**Q7.** 실습 결과를 분석할 때 가장 먼저 확인해야 하는 것은?
- (a) 서버 이름  (b) **exit_code (성공/실패 여부)**  (c) 파일 크기  (d) 날짜

**Q8.** 이 주제와 관련된 MITRE ATT&CK 전술은?
- (a) Impact만  (b) Reconnaissance만  (c) **주제에 해당하는 전술(들)**  (d) 해당 없음

**Q9.** 실무에서 이 기법/도구를 사용할 때 가장 주의할 점은?
- (a) 속도  (b) **법적 허가와 범위 준수**  (c) 비용  (d) 보고서 양식

**Q10.** 다음 주차와의 연결 포인트는?
- (a) 관련 없음  (b) **이번 주 결과를 다음 주에서 활용/심화**  (c) 완전히 다른 주제  (d) 복습만

**정답:** Q1:b, Q2:c, Q3:b, Q4:b, Q5:c, Q6:b, Q7:b, Q8:c, Q9:b, Q10:b

---

## 과제 (다음 주까지)

### 과제 1: 이론 정리 보고서 (30점)

이번 주차의 핵심 개념을 자신의 말로 정리하라.

| 항목 | 배점 |
|------|------|
| 핵심 개념 정의 및 설명 | 10점 |
| 실습 결과 캡처 및 해석 | 10점 |
| 보안 관점 분석 (공격↔방어) | 10점 |

### 과제 2: 실습 수행 보고서 (40점)

이번 주차의 모든 실습을 수행하고 결과를 보고서로 작성하라.

| 항목 | 배점 |
|------|------|
| 실습 명령어 및 실행 결과 캡처 | 15점 |
| 결과 해석 및 보안 의미 분석 | 15점 |
| 트러블슈팅 경험 (있는 경우) | 10점 |

### 과제 3: OpsClaw 자동화 (30점)

이번 주차의 핵심 실습을 OpsClaw execute-plan으로 자동화하라.

| 항목 | 배점 |
|------|------|
| 프로젝트 생성 + stage 전환 | 5점 |
| execute-plan 태스크 설계 (3개 이상) | 10점 |
| evidence/summary 결과 | 5점 |
| replay 타임라인 결과 | 5점 |
| 자동화의 이점 분석 (직접 실행 대비) | 5점 |

**제출:** 보고서(PDF 또는 MD) + OpsClaw project_id


---

## 검증 체크리스트

이번 주차의 학습을 완료하려면 다음 항목을 모두 확인하라:

- [ ] 이론 강의 내용 이해 (핵심 용어 설명 가능)
- [ ] 기본 실습 모두 수행 완료
- [ ] 보충 실습 1 (기본 동작 확인) 완료
- [ ] 보충 실습 2 (탐지/모니터링 관점) 수행
- [ ] 보충 실습 3 (OpsClaw 자동화) 수행
- [ ] 자가 점검 퀴즈 8/10 이상 정답
- [ ] 과제 1 (이론 정리) 작성
- [ ] 과제 2 (실습 보고서) 작성
- [ ] 과제 3 (OpsClaw 자동화) 완료

