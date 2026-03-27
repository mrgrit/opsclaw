# Week 13: 위협 인텔리전스 (CTI) 활용

## 학습 목표
- 위협 인텔리전스(CTI)의 개념과 유형을 이해한다
- IOC(Indicator of Compromise)를 수집하고 활용한다
- Wazuh와 CTI 데이터를 연동하여 위협 헌팅을 수행한다
- STIX/TAXII 포맷의 위협 정보를 이해한다

---

## 1. 위협 인텔리전스 개론

### 1.1 CTI 정의와 유형

| 유형 | 대상 | 예시 | 활용 |
|------|------|------|------|
| 전략적 (Strategic) | 경영진 | 위협 동향, 공격 그룹 | 의사결정 |
| 전술적 (Tactical) | SOC 관리자 | TTPs, ATT&CK 매핑 | 탐지 전략 |
| 운영적 (Operational) | 분석관 | 특정 캠페인 정보 | 인시던트 대응 |
| 기술적 (Technical) | 보안 장비 | IP, Hash, 도메인 | 자동 차단 |

### 1.2 CTI 라이프사이클

```
수집 (Collection) -> 처리 (Processing) -> 분석 (Analysis)
                                              |
배포 (Dissemination) <- 생산 (Production) <- 분석 완료
        |
피드백 (Feedback) -> 수집 요구사항 갱신
```

### 1.3 IOC 유형

| IOC 유형 | 예시 | 탐지 위치 |
|----------|------|----------|
| IP 주소 | 45.33.32.156 | 방화벽, IPS, SIEM |
| 도메인 | evil.example.com | DNS 로그, 프록시 |
| URL | http://evil.com/malware.exe | 프록시, WAF |
| 파일 해시 | SHA256:abc123... | EDR, AV, SIEM |
| 이메일 주소 | attacker@phish.com | 메일 게이트웨이 |
| YARA 룰 | rule malware {...} | 파일 스캐너 |

---

## 2. IOC 수집과 관리

### 2.1 공개 CTI 소스에서 IOC 수집

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 << 'ENDSSH'
python3 << 'PYEOF'
# 교육용 IOC 데이터베이스 시뮬레이션
ioc_database = {
    "malicious_ips": [
        {"ip": "45.33.32.156", "type": "C2 Server", "country": "US", "confidence": 95},
        {"ip": "185.220.101.35", "type": "Tor Exit Node", "country": "DE", "confidence": 100},
        {"ip": "91.219.236.222", "type": "Botnet C2", "country": "RU", "confidence": 88},
        {"ip": "23.129.64.0/24", "type": "Tor Network", "country": "US", "confidence": 100},
    ],
    "malicious_domains": [
        {"domain": "evil-update.com", "type": "Phishing", "first_seen": "2026-03-01"},
        {"domain": "cdn-malware.net", "type": "Malware Distribution", "first_seen": "2026-02-15"},
        {"domain": "c2-beacon.xyz", "type": "C2 Domain", "first_seen": "2026-03-20"},
    ],
    "file_hashes": [
        {"sha256": "a1b2c3d4e5f6...", "name": "trojan.linux.coinminer", "type": "Coinminer"},
        {"sha256": "f6e5d4c3b2a1...", "name": "backdoor.linux.reverse", "type": "Backdoor"},
    ],
}

print("=== IOC 데이터베이스 ===")
print(f"\n악성 IP: {len(ioc_database['malicious_ips'])}건")
for ioc in ioc_database["malicious_ips"]:
    print(f"  {ioc['ip']:<25} {ioc['type']:<20} 신뢰도: {ioc['confidence']}%")

print(f"\n악성 도메인: {len(ioc_database['malicious_domains'])}건")
for ioc in ioc_database["malicious_domains"]:
    print(f"  {ioc['domain']:<25} {ioc['type']:<25} {ioc['first_seen']}")

print(f"\n악성 파일 해시: {len(ioc_database['file_hashes'])}건")
for ioc in ioc_database["file_hashes"]:
    print(f"  {ioc['sha256']:<20} {ioc['name']:<30} {ioc['type']}")
PYEOF
ENDSSH
```

### 2.2 로그에서 IOC 매칭

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.1 << 'ENDSSH'
echo "=== IOC 매칭: 네트워크 로그 vs 악성 IP ==="

MALICIOUS_IPS="45.33.32.156 185.220.101.35 91.219.236.222"

echo "--- Suricata 로그 IOC 매칭 ---"
for ip in $MALICIOUS_IPS; do
  COUNT=$(grep -c "$ip" /var/log/suricata/eve.json 2>/dev/null || echo "0")
  if [ "$COUNT" -gt "0" ]; then
    echo "[HIT] $ip - $COUNT건 발견"
  else
    echo "[MISS] $ip - 매칭 없음"
  fi
done

echo ""
echo "--- 현재 연결에서 IOC 매칭 ---"
for ip in $MALICIOUS_IPS; do
  if ss -tn 2>/dev/null | grep -q "$ip"; then
    echo "[ACTIVE] $ip - 현재 연결 중!"
  fi
done
echo "(현재 활성 IOC 연결 없음 = 정상)"
ENDSSH
```

### 2.3 Wazuh CDB 리스트 활용

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.100 << 'ENDSSH'
echo "=== Wazuh CDB 리스트 기반 IOC 탐지 ==="

cat << 'EXPLAIN'
Wazuh CDB 리스트로 IOC를 SIEM에 통합하는 방법:

1. CDB 리스트 생성 (/var/ossec/etc/lists/)
   # 형식: key:value
   45.33.32.156:C2 Server
   185.220.101.35:Tor Exit
   91.219.236.222:Botnet C2

2. ossec.conf에 리스트 등록
   <ruleset>
     <list>etc/lists/malicious_ips</list>
   </ruleset>

3. 커스텀 룰에서 CDB 매칭
   <rule id="100100" level="12">
     <if_sid>5710</if_sid>
     <list field="srcip" lookup="address_match">etc/lists/malicious_ips</list>
     <description>알려진 악성 IP에서 접근: $(srcip)</description>
   </rule>
EXPLAIN

echo ""
echo "--- 현재 Wazuh CDB 리스트 ---"
ls -la /var/ossec/etc/lists/ 2>/dev/null || echo "리스트 디렉토리 없음"
ENDSSH
```

---

## 3. STIX/TAXII 위협 정보 포맷

### 3.1 STIX 2.1 객체 이해

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 << 'ENDSSH'
python3 << 'PYEOF'
import json

stix_indicator = {
    "type": "indicator",
    "spec_version": "2.1",
    "id": "indicator--a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "created": "2026-03-27T00:00:00Z",
    "name": "C2 Server IP",
    "description": "Known command and control server",
    "indicator_types": ["malicious-activity"],
    "pattern": "[ipv4-addr:value = '45.33.32.156']",
    "pattern_type": "stix",
    "valid_from": "2026-03-01T00:00:00Z",
    "kill_chain_phases": [
        {"kill_chain_name": "mitre-attack", "phase_name": "command-and-control"}
    ]
}

print("=== STIX 2.1 Indicator 객체 ===")
print(json.dumps(stix_indicator, indent=2))

print("\n=== STIX 2.1 주요 객체 유형 ===")
stix_types = [
    ("indicator", "탐지 지표 (IOC 패턴)"),
    ("malware", "악성코드 정보"),
    ("attack-pattern", "공격 기법 (ATT&CK 연동)"),
    ("threat-actor", "위협 행위자/그룹"),
    ("campaign", "공격 캠페인"),
    ("vulnerability", "취약점 (CVE)"),
    ("relationship", "객체 간 관계"),
    ("sighting", "IOC 관측 기록"),
]

for stype, desc in stix_types:
    print(f"  {stype:<20} {desc}")
PYEOF
ENDSSH
```

---

## 4. 위협 헌팅 (Threat Hunting)

### 4.1 가설 기반 위협 헌팅

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.1 << 'ENDSSH'
echo "=== 위협 헌팅 실습 ==="
echo "가설: 내부 서버에서 외부 C2 서버로 비콘 통신이 발생하고 있다"
echo ""

echo "--- Hunt 1: 비정상 외부 연결 ---"
ss -tn 2>/dev/null | awk '{print $5}' | grep -v "^$\|127.0.0.1\|10.20.30\|192.168\|::1" | \
  sort | uniq -c | sort -rn | head -5
echo "(외부 연결 목록)"

echo ""
echo "--- Hunt 2: 비정상 DNS 쿼리 (긴 도메인 = 터널링 징후) ---"
grep -o "[a-zA-Z0-9.-]*\.[a-z]*" /var/log/syslog 2>/dev/null | \
  awk '{if(length($0) > 40) print "LONG:", $0}' | head -5 || echo "긴 DNS 없음 (정상)"

echo ""
echo "--- Hunt 3: 프로세스 체인 ---"
ps auxf 2>/dev/null | grep -A2 -E "nginx|apache|node" | head -15

echo ""
echo "--- Hunt 4: 비정상 위치 실행 파일 ---"
find /dev/shm /tmp /var/tmp -type f -executable 2>/dev/null | head -5 || echo "없음 (정상)"

echo ""
echo "--- Hunt 5: 예약 작업 ---"
crontab -l 2>/dev/null | grep -vE "^#|^$" | head -5
ENDSSH
```

### 4.2 Suricata 로그 기반 위협 헌팅

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.1 << 'ENDSSH'
echo "=== Suricata 로그 위협 헌팅 ==="

cat /var/log/suricata/eve.json 2>/dev/null | python3 -c "
import sys, json
from collections import Counter

http_events, alert_events = [], []
for line in sys.stdin:
    try:
        e = json.loads(line.strip())
        etype = e.get('event_type','')
        if etype == 'http': http_events.append(e)
        elif etype == 'alert': alert_events.append(e)
    except: pass

print(f'HTTP 이벤트: {len(http_events)}건')
print(f'Alert 이벤트: {len(alert_events)}건')

if http_events:
    uas = Counter(e.get('http',{}).get('http_user_agent','unknown') for e in http_events)
    print('\nUser-Agent 분포 (상위 5개):')
    for ua, cnt in uas.most_common(5):
        print(f'  [{cnt}] {ua[:60]}')

if alert_events:
    cats = Counter(e.get('alert',{}).get('category','unknown') for e in alert_events)
    print('\nAlert 카테고리:')
    for cat, cnt in cats.most_common(10):
        print(f'  [{cnt}] {cat}')
" 2>/dev/null || echo "Suricata 로그 없음"
ENDSSH
```

### 4.3 LLM 기반 위협 헌팅 가설 생성

```bash
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "위협 헌팅 전문가입니다. MITRE ATT&CK 기반으로 헌팅 가설을 생성합니다. 한국어로 답변하세요."},
      {"role": "user", "content": "Linux 웹서버 환경에서 수행할 위협 헌팅 가설 5개를 생성하세요.\n\n각 가설: 1) 가설 (ATT&CK TTP) 2) 데이터 소스 3) 탐지 쿼리 예시\n\n환경: Linux, Suricata IPS, Wazuh SIEM, Node.js 웹서버"}
    ],
    "temperature": 0.5
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

---

## 5. CTI 자동화와 연동

### 5.1 IOC 자동 업데이트 스크립트

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 << 'ENDSSH'
python3 << 'PYEOF'
import json
from datetime import datetime

def collect_iocs():
    """CTI 소스에서 IOC 수집 (시뮬레이션)"""
    return {
        "ips": [
            {"value": "45.33.32.156", "type": "c2", "confidence": 95},
            {"value": "185.220.101.35", "type": "tor", "confidence": 100},
        ],
        "domains": [
            {"value": "evil-update.com", "type": "phishing"},
            {"value": "c2-beacon.xyz", "type": "c2"},
        ],
    }

def generate_wazuh_cdb(iocs):
    """Wazuh CDB 형식"""
    return "\n".join(f"{ip['value']}:{ip['type']}" for ip in iocs["ips"])

def generate_suricata_rules(iocs):
    """Suricata 룰 형식"""
    rules = []
    for idx, ip_ioc in enumerate(iocs["ips"], 1):
        sid = 9000000 + idx
        rules.append(
            f'alert ip any any -> {ip_ioc["value"]} any '
            f'(msg:"CTI IOC: {ip_ioc["type"]} {ip_ioc["value"]}"; '
            f'sid:{sid}; rev:1;)'
        )
    return "\n".join(rules)

iocs = collect_iocs()
print(f"수집된 IOC: IP={len(iocs['ips'])}, Domain={len(iocs['domains'])}")

print("\n=== Wazuh CDB 출력 ===")
print(generate_wazuh_cdb(iocs))

print("\n=== Suricata 룰 출력 ===")
print(generate_suricata_rules(iocs))

print(f"\n업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
PYEOF
ENDSSH
```

---

## 핵심 정리

1. CTI는 전략적/전술적/운영적/기술적 4가지 유형으로 분류된다
2. IOC(IP, 도메인, 해시)를 SIEM/IPS에 연동하여 자동 탐지한다
3. STIX 2.1은 위협 정보 교환의 표준 포맷이다
4. 위협 헌팅은 가설 기반으로 능동적으로 위협을 탐색한다
5. Wazuh CDB 리스트로 IOC를 SIEM 경보에 통합할 수 있다
6. CTI 자동화로 수집-연동-탐지 사이클을 효율화한다

---

## 다음 주 예고
- Week 14: 자동화 관제 - OpsClaw Agent Daemon 자율 탐지 에이전트
