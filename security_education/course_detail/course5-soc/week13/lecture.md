# Week 13: 위협 인텔리전스 (CTI) 활용 (상세 버전)

## 학습 목표
- 위협 인텔리전스(CTI)의 개념과 유형을 이해한다
- IOC(Indicator of Compromise)를 수집하고 활용한다
- Wazuh와 CTI 데이터를 연동하여 위협 헌팅을 수행한다
- STIX/TAXII 포맷의 위협 정보를 이해한다


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

## 용어 해설 (보안관제/SOC 과목)

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **SOC** | Security Operations Center | 보안 관제 센터 (24/7 모니터링) | 경찰 112 상황실 |
| **관제** | Monitoring/Surveillance | 보안 이벤트를 실시간 감시하는 활동 | CCTV 관제 |
| **경보** | Alert | 보안 이벤트가 탐지 규칙에 매칭되어 발생한 알림 | 화재 경보기 울림 |
| **이벤트** | Event | 시스템에서 발생한 모든 활동 기록 | 일어난 일 하나하나 |
| **인시던트** | Incident | 보안 정책을 위반한 이벤트 (실제 위협) | 실제 화재 발생 |
| **오탐** | False Positive | 정상 활동을 공격으로 잘못 탐지 | 화재 경보기가 요리 연기에 울림 |
| **미탐** | False Negative | 실제 공격을 놓침 | 도둑이 CCTV에 안 잡힘 |
| **TTD** | Time to Detect | 공격 발생~탐지까지 걸리는 시간 | 화재 발생~경보 울림 시간 |
| **TTR** | Time to Respond | 탐지~대응까지 걸리는 시간 | 경보~소방차 도착 시간 |
| **SIGMA** | SIGMA | SIEM 벤더에 무관한 범용 탐지 룰 포맷 | 국제 표준 수배서 양식 |
| **Tier 1/2/3** | SOC Tiers | 관제 인력 수준 (L1:모니터링, L2:분석, L3:전문가) | 일반의→전문의→교수 |
| **트리아지** | Triage | 경보를 우선순위별로 분류하는 작업 | 응급실 환자 분류 |
| **플레이북** | Playbook (IR) | 인시던트 유형별 대응 절차 매뉴얼 | 화재 대응 매뉴얼 |
| **포렌식** | Forensics | 사이버 범죄 수사를 위한 증거 수집·분석 | 범죄 현장 감식 |
| **IOC** | Indicator of Compromise | 침해 지표 (악성 IP, 도메인, 해시) | 수배범의 지문, 차량번호 |
| **TTP** | Tactics, Techniques, Procedures | 공격자의 전술·기법·절차 | 범인의 범행 수법 |
| **위협 헌팅** | Threat Hunting | 탐지 룰에 걸리지 않는 위협을 능동적으로 찾는 활동 | 잠복 수사 |
| **syslog** | syslog | 시스템 로그를 원격 전송하는 프로토콜 (UDP 514) | 모든 부서 보고서를 본사로 모으는 시스템 |


---

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
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 << 'ENDSSH'
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
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 << 'ENDSSH'
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
sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100 << 'ENDSSH'
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
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 << 'ENDSSH'
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
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 << 'ENDSSH'
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
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 << 'ENDSSH'
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
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 << 'ENDSSH'
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


---


---

## 자가 점검 퀴즈 (10문항)

이번 주차의 핵심 내용을 점검한다. 8/10 이상 정답을 목표로 한다.

**Q1.** "Week 13: 위협 인텔리전스 (CTI) 활용"에서 가장 핵심적인 학습 목표는?
- (a) 데이터베이스 최적화  (b) **보안관제/SOC의 원리와 실습**  (c) UI 개발  (d) 네트워크 속도

**Q2.** "1. 위협 인텔리전스 개론"의 보안 관점에서의 의의는?
- (a) 성능 향상  (b) **보안 위협 이해 또는 방어 역량 강화**  (c) 비용 절감  (d) 사용성 개선

**Q3.** "2. IOC 수집과 관리"에서 사용하는 주요 도구/기법은?
- (a) 워드프로세서  (b) **보안관제/SOC 전용 도구/명령**  (c) 게임 엔진  (d) 그래픽 도구

**Q4.** 이번 실습에서 OpsClaw evidence가 제공하는 가치는?
- (a) 속도  (b) **작업 증적의 자동 기록과 감사 추적**  (c) 화면 출력  (d) 파일 압축

**Q5.** "3. STIX/TAXII 위협 정보 포맷"의 실무 활용 방안은?
- (a) 개인 블로그  (b) **보안 점검, 대응, 보고서 작성에 활용**  (c) 게임 개발  (d) 영상 편집

**Q6.** 이 주차에서 탐지/대응의 핵심 원칙은?
- (a) 모든 기능 비활성화  (b) **최소 권한 + 모니터링 + 대응의 조합**  (c) 무조건 차단  (d) 설정 변경 금지

**Q7.** 실습 결과를 평가할 때 가장 중요한 기준은?
- (a) 파일 크기  (b) **보안 효과성과 정확성**  (c) 실행 속도  (d) 줄 수

**Q8.** 이 주제가 전체 보안관제/SOC 커리큘럼에서 차지하는 위치는?
- (a) 독립적 주제  (b) **이전 주차의 심화/다음 주차의 기반**  (c) 선택 과목  (d) 부록

**Q9.** 실무에서 이 기법을 적용할 때 주의할 점은?
- (a) 속도  (b) **법적 허가, 범위 준수, 증적 관리**  (c) 디자인  (d) 비용

**Q10.** 이번 주차 학습의 성과를 어떻게 측정하는가?
- (a) 시간  (b) **실습 완료율 + 퀴즈 점수 + 과제 품질**  (c) 줄 수  (d) 파일 수

**정답:** Q1:b, Q2:b, Q3:b, Q4:b, Q5:b, Q6:b, Q7:b, Q8:b, Q9:b, Q10:b

---

## 과제 (다음 주까지)


## 검증 체크리스트

이번 주차의 학습을 완료하려면 다음 항목을 모두 확인하라:


