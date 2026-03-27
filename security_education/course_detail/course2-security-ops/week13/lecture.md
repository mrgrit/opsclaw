# Week 13: OpenCTI (2) — 위협 인텔리전스 활용 (상세 버전)

## 학습 목표
- IOC(침해 지표)를 체계적으로 관리할 수 있다
- 공격 그룹을 분석하고 프로파일링할 수 있다
- 위협 헌팅의 기본 프로세스를 수행할 수 있다
- OpenCTI 데이터를 실제 보안 운영에 활용할 수 있다
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

# Week 13: OpenCTI (2) — 위협 인텔리전스 활용

## 학습 목표

- IOC(침해 지표)를 체계적으로 관리할 수 있다
- 공격 그룹을 분석하고 프로파일링할 수 있다
- 위협 헌팅의 기본 프로세스를 수행할 수 있다
- OpenCTI 데이터를 실제 보안 운영에 활용할 수 있다

---

## 1. IOC(Indicator of Compromise) 관리

### 1.1 IOC의 종류

| 유형 | 설명 | 예시 |
|------|------|------|
| IP 주소 | C2 서버, 스캐너 | 1.2.3.4 |
| 도메인 | 피싱, 악성 사이트 | evil.example.com |
| URL | 악성코드 배포 | http://evil.com/malware.exe |
| 파일 해시 | 악성 파일 식별 | MD5, SHA256 |
| 이메일 | 피싱 발송자 | attacker@phish.com |
| YARA 룰 | 파일 패턴 | rule Emotet { ... } |

### 1.2 IOC 수명주기

```
수집 → 검증 → 등록 → 배포 → 탐지 → 만료/갱신
```

| 단계 | 설명 |
|------|------|
| 수집 | 피드, 보고서, 인시던트에서 IOC 수집 |
| 검증 | 오탐 확인, 신뢰도 평가 |
| 등록 | OpenCTI에 STIX 형식으로 등록 |
| 배포 | SIEM, IPS, 방화벽으로 전달 |
| 탐지 | 보안 장비에서 IOC 매칭 |
| 만료 | 유효기간 지나면 비활성화 |

---

## 2. 실습 환경 접속

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.100

# API 토큰 설정 (대시보드에서 확인한 값)
OPENCTI_TOKEN="your-api-token-here"
```

---

## 3. IOC 등록 및 관리

### 3.1 API로 IOC 생성

```bash
# 악성 IP 지표 생성
curl -s -X POST http://10.20.30.100:9400/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENCTI_TOKEN" \
  -d '{
    "query": "mutation { indicatorAdd(input: { name: \"Malicious C2 Server\", pattern: \"[ipv4-addr:value = '"'"'203.0.113.50'"'"']\", pattern_type: \"stix\", x_opencti_main_observable_type: \"IPv4-Addr\", valid_from: \"2026-03-27T00:00:00.000Z\" }) { id name } }"
  }' | python3 -m json.tool
```

### 3.2 대량 IOC 등록

실무에서는 CSV나 STIX 번들로 대량 등록한다:

```bash
# IOC 목록에서 STIX 번들 자동 생성
cat << 'PYEOF' > /tmp/create_stix_bundle.py
import json, uuid
from datetime import datetime

iocs = [
    ("Lazarus C2 #1", "ipv4-addr", "203.0.113.10"),
    ("Lazarus C2 #2", "ipv4-addr", "203.0.113.11"),
    ("Lazarus C2 #3", "ipv4-addr", "203.0.113.12"),
    ("Phishing Domain #1", "domain-name", "login-secure-update.example.com"),
    ("Phishing Domain #2", "domain-name", "account-verify-now.example.com"),
    ("Malware Hash - Backdoor", "file:hashes.SHA-256", "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2"),
]

now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")
objects = []

for name, obs_type, value in iocs:
    indicator_id = f"indicator--{uuid.uuid4()}"
    if "hashes" in obs_type:
        pattern = f"[file:hashes.'SHA-256' = '{value}']"
    else:
        pattern = f"[{obs_type}:value = '{value}']"

    objects.append({
        "type": "indicator",
        "spec_version": "2.1",
        "id": indicator_id,
        "created": now,
        "modified": now,
        "name": name,
        "pattern": pattern,
        "pattern_type": "stix",
        "valid_from": now,
        "labels": ["malicious-activity"],
        "confidence": 85
    })

bundle = {
    "type": "bundle",
    "id": f"bundle--{uuid.uuid4()}",
    "objects": objects
}

with open("/tmp/lazarus_iocs.json", "w") as f:
    json.dump(bundle, f, indent=2)

print(f"Generated {len(objects)} IOCs")
PYEOF

python3 /tmp/create_stix_bundle.py
cat /tmp/lazarus_iocs.json | python3 -m json.tool | head -30
```

---

## 4. 공격 그룹 분석

### 4.1 Threat Actor 등록

```bash
# 위협 행위자 STIX 번들 생성
cat << 'STIXEOF' > /tmp/threat_actor.json
{
  "type": "bundle",
  "id": "bundle--ta-lab-001",
  "objects": [
    {
      "type": "threat-actor",
      "spec_version": "2.1",
      "id": "threat-actor--lab-lazarus",
      "created": "2026-03-27T00:00:00.000Z",
      "modified": "2026-03-27T00:00:00.000Z",
      "name": "Lab-Lazarus Group",
      "description": "실습용 위협 행위자. 북한 연계 APT 그룹을 모방한 시나리오.",
      "threat_actor_types": ["nation-state"],
      "aliases": ["Hidden Cobra", "ZINC"],
      "goals": ["Financial gain", "Espionage"],
      "sophistication": "advanced",
      "resource_level": "government",
      "primary_motivation": "organizational-gain"
    },
    {
      "type": "malware",
      "spec_version": "2.1",
      "id": "malware--lab-backdoor",
      "created": "2026-03-27T00:00:00.000Z",
      "modified": "2026-03-27T00:00:00.000Z",
      "name": "Lab-DreamBot",
      "description": "실습용 백도어 악성코드",
      "malware_types": ["backdoor", "remote-access-trojan"],
      "is_family": true
    },
    {
      "type": "attack-pattern",
      "spec_version": "2.1",
      "id": "attack-pattern--lab-spearphish",
      "created": "2026-03-27T00:00:00.000Z",
      "modified": "2026-03-27T00:00:00.000Z",
      "name": "Spearphishing Attachment",
      "description": "표적 피싱 메일에 악성 첨부파일을 포함하여 전달",
      "external_references": [
        {
          "source_name": "mitre-attack",
          "external_id": "T1566.001"
        }
      ]
    },
    {
      "type": "relationship",
      "spec_version": "2.1",
      "id": "relationship--lab-001",
      "created": "2026-03-27T00:00:00.000Z",
      "modified": "2026-03-27T00:00:00.000Z",
      "relationship_type": "uses",
      "source_ref": "threat-actor--lab-lazarus",
      "target_ref": "malware--lab-backdoor"
    },
    {
      "type": "relationship",
      "spec_version": "2.1",
      "id": "relationship--lab-002",
      "created": "2026-03-27T00:00:00.000Z",
      "modified": "2026-03-27T00:00:00.000Z",
      "relationship_type": "uses",
      "source_ref": "threat-actor--lab-lazarus",
      "target_ref": "attack-pattern--lab-spearphish"
    }
  ]
}
STIXEOF
```

### 4.2 관계 그래프 확인

OpenCTI 웹 UI에서:
1. Threats > Threat Actors 메뉴
2. "Lab-Lazarus Group" 클릭
3. Knowledge 탭 → 관계 그래프 확인

```
Lab-Lazarus Group
  ├── uses → Lab-DreamBot (malware)
  ├── uses → Spearphishing Attachment (attack-pattern)
  └── indicates → IOC (IP, Domain, Hash)
```

### 4.3 공격 그룹 프로파일 작성

분석 보고서 형식:

| 항목 | 내용 |
|------|------|
| 그룹명 | Lab-Lazarus Group |
| 별칭 | Hidden Cobra, ZINC |
| 국적/소속 | 북한 (nation-state) |
| 동기 | 금전적 이득, 정보 수집 |
| 기술 수준 | 고급 (advanced) |
| 주요 TTPs | T1566.001 (Spearphishing), T1059 (Command Execution) |
| 주요 도구 | Lab-DreamBot (RAT) |
| IOC | 203.0.113.10-12, login-secure-update.example.com |
| 표적 산업 | 금융, 암호화폐 거래소 |

---

## 5. 위협 헌팅 (Threat Hunting)

### 5.1 위협 헌팅이란?

기존 보안 장비의 알림에 의존하지 않고, **능동적으로 위협을 탐색**하는 활동이다.

```
가설 설정 → 데이터 수집 → 분석 → 결론
```

### 5.2 헌팅 시나리오: Lazarus IOC 매칭

**가설**: "우리 네트워크에서 Lab-Lazarus의 C2 서버와 통신하는 호스트가 있을 수 있다."

**Step 1: IOC 목록 추출**

```bash
# OpenCTI에서 Lazarus 관련 IP IOC 추출
curl -s -X POST http://10.20.30.100:9400/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENCTI_TOKEN" \
  -d '{
    "query": "{ indicators(search: \"Lazarus\", first: 50) { edges { node { name pattern } } } }"
  }' | python3 -c "
import sys, json, re
data = json.load(sys.stdin)
for edge in data.get('data',{}).get('indicators',{}).get('edges',[]):
    node = edge['node']
    m = re.search(r\"value\s*=\s*'([^']+)'\", node.get('pattern',''))
    if m:
        print(f\"{m.group(1)}  # {node['name']}\")
"
```

**Step 2: Suricata 로그에서 IOC 검색**

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.1

# Suricata 로그에서 C2 IP 검색
echo 1 | sudo -S grep -E "203\.0\.113\.(10|11|12)" /var/log/suricata/eve.json | \
  python3 -c "
import sys, json
for line in sys.stdin:
    try:
        e = json.loads(line)
        print(f\"{e.get('timestamp','')} {e.get('src_ip','')} -> {e.get('dest_ip','')} {e.get('event_type','')}\")
    except: pass
" | head -20
```

**Step 3: Wazuh 로그에서 IOC 검색**

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.100

echo 1 | sudo -S grep -E "203\.0\.113\.(10|11|12)" /var/ossec/logs/alerts/alerts.json | \
  python3 -c "
import sys, json
for line in sys.stdin:
    try:
        e = json.loads(line)
        r = e.get('rule',{})
        print(f\"{e.get('timestamp','')} [{r.get('level','')}] {r.get('description','')}\")
    except: pass
" | head -10
```

**Step 4: 결론 작성**

```bash
cat << 'EOF' > /tmp/hunting_report.txt
=== 위협 헌팅 보고서 ===
날짜: 2026-03-27
분석가: [이름]
가설: Lab-Lazarus C2 서버 통신 탐지

IOC 검색 범위:
  - 203.0.113.10, 203.0.113.11, 203.0.113.12
  - login-secure-update.example.com

검색 결과:
  - Suricata 로그: 매칭 없음
  - Wazuh 알림: 매칭 없음
  - 방화벽 로그: 매칭 없음

결론: 현재 네트워크에서 해당 IOC와 통신하는 호스트는 발견되지 않음.
권장조치: IOC를 Suricata 룰과 nftables 차단 목록에 등록하여 선제 방어.
EOF

cat /tmp/hunting_report.txt
```

---

## 6. IOC를 보안 장비에 배포

### 6.1 Suricata 룰로 변환

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.1

# OpenCTI IOC를 Suricata 룰로 변환
echo 1 | sudo -S tee -a /etc/suricata/rules/local.rules << 'EOF'
# Lab-Lazarus C2 Server Detection
alert ip $HOME_NET any -> 203.0.113.10 any (msg:"CTI - Lab-Lazarus C2 #1"; sid:9200001; rev:1; classtype:trojan-activity;)
alert ip $HOME_NET any -> 203.0.113.11 any (msg:"CTI - Lab-Lazarus C2 #2"; sid:9200002; rev:1; classtype:trojan-activity;)
alert ip $HOME_NET any -> 203.0.113.12 any (msg:"CTI - Lab-Lazarus C2 #3"; sid:9200003; rev:1; classtype:trojan-activity;)
alert dns $HOME_NET any -> any any (msg:"CTI - Lab-Lazarus Phishing Domain"; dns.query; content:"login-secure-update.example.com"; nocase; sid:9200004; rev:1; classtype:trojan-activity;)
EOF

echo 1 | sudo -S kill -USR2 $(pidof suricata)
```

### 6.2 nftables 차단 목록으로 변환

```bash
# 악성 IP 차단
echo 1 | sudo -S nft add set inet filter cti_blocklist '{ type ipv4_addr; }'
echo 1 | sudo -S nft add element inet filter cti_blocklist \
  '{ 203.0.113.10, 203.0.113.11, 203.0.113.12 }'
echo 1 | sudo -S nft add rule inet filter input ip saddr @cti_blocklist drop
echo 1 | sudo -S nft add rule inet filter output ip daddr @cti_blocklist drop
```

### 6.3 Wazuh CDB List로 변환

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.100

# CDB 리스트 생성
echo 1 | sudo -S tee /var/ossec/etc/lists/cti-malicious-ips << 'EOF'
203.0.113.10:Lazarus-C2
203.0.113.11:Lazarus-C2
203.0.113.12:Lazarus-C2
EOF

# ossec.conf에 리스트 등록
# <ruleset><list>etc/lists/cti-malicious-ips</list></ruleset>

# Wazuh 룰에서 CDB 활용
# <rule id="100050" level="12">
#   <list field="srcip" lookup="address_match_key">etc/lists/cti-malicious-ips</list>
#   <description>CTI IOC 매칭: $(srcip) - Lazarus C2</description>
# </rule>
```

---

## 7. 자동화 파이프라인

### 7.1 IOC 자동 동기화 스크립트

```bash
cat << 'PYEOF' > /tmp/sync_iocs.py
#!/usr/bin/env python3
"""OpenCTI IOC를 Suricata 룰과 nftables 차단 목록으로 동기화"""
import json, re, subprocess, requests

OPENCTI_URL = "http://10.20.30.100:9400/graphql"
OPENCTI_TOKEN = "your-api-token-here"

# 1. OpenCTI에서 IOC 가져오기
query = '{ indicators(first: 500) { edges { node { name pattern pattern_type } } } }'
resp = requests.post(OPENCTI_URL,
    headers={"Authorization": f"Bearer {OPENCTI_TOKEN}", "Content-Type": "application/json"},
    json={"query": query})

data = resp.json()
ips = []
domains = []

for edge in data.get('data',{}).get('indicators',{}).get('edges',[]):
    pattern = edge['node'].get('pattern','')
    m_ip = re.search(r"ipv4-addr:value\s*=\s*'([^']+)'", pattern)
    m_domain = re.search(r"domain-name:value\s*=\s*'([^']+)'", pattern)
    if m_ip:
        ips.append(m_ip.group(1))
    if m_domain:
        domains.append(m_domain.group(1))

print(f"수집된 IOC: IP {len(ips)}개, Domain {len(domains)}개")

# 2. Suricata 룰 생성
sid_base = 9300000
rules = []
for i, ip in enumerate(ips):
    rules.append(f'alert ip $HOME_NET any -> {ip} any (msg:"CTI-AUTO - Malicious IP {ip}"; sid:{sid_base+i}; rev:1;)')
for i, dom in enumerate(domains):
    rules.append(f'alert dns $HOME_NET any -> any any (msg:"CTI-AUTO - Malicious Domain {dom}"; dns.query; content:"{dom}"; nocase; sid:{sid_base+len(ips)+i}; rev:1;)')

with open("/tmp/cti_auto_rules.rules", "w") as f:
    f.write("\n".join(rules))

print(f"생성된 Suricata 룰: {len(rules)}개")
print("파일: /tmp/cti_auto_rules.rules")
PYEOF

python3 /tmp/sync_iocs.py
```

---

## 8. 실습 과제

### 과제 1: IOC 등록

1. 실습용 악성 IP 5개, 도메인 3개, 파일 해시 2개를 STIX 번들로 생성
2. OpenCTI에 업로드
3. API로 등록된 IOC를 조회하여 확인

### 과제 2: 공격 그룹 프로파일

1. 실습용 위협 행위자를 생성 (이름, 동기, 기술 수준 포함)
2. 행위자와 악성코드, 공격 기법 간의 관계를 생성
3. 웹 UI에서 관계 그래프를 확인

### 과제 3: 위협 헌팅

1. 등록한 IOC를 기반으로 Suricata/Wazuh 로그에서 매칭을 검색
2. IOC를 Suricata 룰로 변환하여 적용
3. 헌팅 결과 보고서를 작성

---

## 9. 핵심 정리

| 개념 | 설명 |
|------|------|
| IOC | 침해 지표 (IP, 도메인, 해시) |
| IOC 수명주기 | 수집 → 검증 → 등록 → 배포 → 탐지 → 만료 |
| Threat Actor | 위협 행위자 프로파일 |
| Relationship | STIX 객체 간 관계 (uses, targets) |
| Threat Hunting | 능동적 위협 탐색 |
| IOC 배포 | CTI → Suricata/nftables/Wazuh |
| CDB List | Wazuh IOC 룩업 리스트 |

---

## 다음 주 예고

Week 14에서는 모든 보안 시스템을 통합하는 아키텍처를 다룬다:
- FW → IPS → WAF → SIEM → CTI 통합
- 트래픽 흐름과 보안 계층
- 종합 모니터링


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

**Q1.** 이번 주차 "Week 13: OpenCTI (2) — 위협 인텔리전스 활용"의 핵심 목적은 무엇인가?
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

