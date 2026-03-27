# Week 13: CTI 활용 - 위협 인텔리전스

## 학습 목표

- CTI(Cyber Threat Intelligence)의 개념과 유형을 이해한다
- OpenCTI 플랫폼을 사용하여 위협 정보를 조회할 수 있다
- IOC(Indicator of Compromise)를 활용한 위협 헌팅을 수행한다
- 위협 인텔리전스를 SOC 운영에 통합하는 방법을 이해한다

---

## 1. CTI 개요

### 1.1 정의

**CTI** = Cyber Threat Intelligence = 사이버 위협에 대한 **맥락 있는 정보**

단순 데이터가 아니라, 의사결정에 도움이 되는 **분석된 정보**이다.

```
데이터 (Data): "IP 10.0.0.1이 포트 22에 접속했다"
정보 (Information): "IP 10.0.0.1이 SSH 무차별 대입을 시도했다"
인텔리전스 (Intelligence): "이 IP는 APT28 그룹과 연관되며,
  동유럽 기반 공격 캠페인의 일부로, 에너지 분야를 표적으로 한다"
```

### 1.2 CTI 수준

| 수준 | 대상 | 내용 | 예시 |
|------|------|------|------|
| 전략적 (Strategic) | 경영진 | 위협 동향, 리스크 | APT 그룹 동향 보고서 |
| 전술적 (Tactical) | 보안팀 | TTPs, 공격 패턴 | ATT&CK 기법 분석 |
| 운영적 (Operational) | SOC | 특정 공격 캠페인 | 캠페인 상세 분석 |
| 기술적 (Technical) | SIEM/장비 | IOC | IP, 해시, 도메인 |

### 1.3 IOC 유형

| 유형 | 예시 | 활용 |
|------|------|------|
| IP 주소 | 185.220.101.x | 방화벽 차단, SIEM 탐지 |
| 도메인 | evil-c2.example.com | DNS 차단, 프록시 |
| URL | http://evil.com/malware.exe | 웹 필터 |
| 파일 해시 | SHA256: abc123... | 파일 스캔, EDR |
| 이메일 | attacker@phishing.com | 메일 필터 |
| YARA 규칙 | rule malware {...} | 파일/메모리 스캔 |

---

## 2. OpenCTI 플랫폼

### 2.1 OpenCTI란?

- **오픈소스** 위협 인텔리전스 관리 플랫폼
- STIX/TAXII 표준 지원
- 위협 그룹, 악성코드, IOC를 체계적으로 관리
- 그래프 기반 관계 분석

### 2.2 접속 방법

```
URL: http://192.168.208.152:9400
사용자/비밀번호: (수업 시간에 안내)
```

### 2.3 주요 기능

| 메뉴 | 기능 |
|------|------|
| Dashboard | 위협 현황 요약 |
| Analysis | 보고서, 관찰 내용 |
| Events | 인시던트, 관찰된 데이터 |
| Observations | 기술적 IOC (IP, 해시, 도메인) |
| Threats | 위협 그룹, 캠페인, 악성코드 |
| Arsenal | 공격 도구, 취약점 |
| Techniques | ATT&CK 기법 매핑 |

---

## 3. IOC 기반 위협 헌팅

### 3.1 위협 헌팅이란?

**Threat Hunting** = 기존 탐지 규칙에 잡히지 않는 위협을 **능동적으로** 찾는 것

```
기존 SOC: 경보 발생 → 분석 (수동적, Reactive)
위협 헌팅: 가설 수립 → 증거 검색 → 발견 (능동적, Proactive)
```

### 3.2 헌팅 프로세스

```
1. 가설 수립: "최근 APT 캠페인의 IOC가 우리 환경에 있을 수 있다"
2. 데이터 수집: 로그, 네트워크, 파일 시스템 검색
3. 분석: IOC 매칭, 이상 행위 확인
4. 결과: 발견 시 인시던트 대응, 미발견 시 탐지 규칙 개선
```

### 3.3 실습: IP IOC 헌팅

```bash
# 가설: 알려진 악성 IP가 우리 환경에 접근했을 수 있다

# 1단계: IOC 목록 준비 (예시 - 실제로는 CTI 피드에서 가져옴)
SUSPECT_IPS="10.0.0.1 172.16.0.1 203.0.113.50"

# 2단계: auth.log에서 IOC IP 검색
echo "=== auth.log IOC 검색 ==="
for ip in $SUSPECT_IPS; do
  for server in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
    result=$(sshpass -p1 ssh user@$server "grep '$ip' /var/log/auth.log 2>/dev/null | wc -l")
    if [ "$result" -gt 0 ] 2>/dev/null; then
      echo "  [!] $ip 발견: $server ($result건)"
    fi
  done
done

# 3단계: Suricata 로그에서 IOC IP 검색
echo ""
echo "=== Suricata IOC 검색 ==="
for ip in $SUSPECT_IPS; do
  result=$(sshpass -p1 ssh user@192.168.208.150 "grep '$ip' /var/log/suricata/fast.log 2>/dev/null | wc -l")
  if [ "$result" -gt 0 ] 2>/dev/null; then
    echo "  [!] $ip 발견: Suricata ($result건)"
  fi
done

# 4단계: 웹 로그에서 IOC IP 검색
echo ""
echo "=== 웹 로그 IOC 검색 ==="
for ip in $SUSPECT_IPS; do
  result=$(sshpass -p1 ssh user@192.168.208.151 "grep '$ip' /var/log/nginx/access.log 2>/dev/null | wc -l")
  if [ "$result" -gt 0 ] 2>/dev/null; then
    echo "  [!] $ip 발견: 웹 로그 ($result건)"
  fi
done
```

### 3.4 실습: 파일 해시 헌팅

```bash
# 시스템의 실행 파일 해시를 수집하여 IOC와 비교
echo "=== 파일 해시 수집 ==="
sshpass -p1 ssh user@192.168.208.142 "
  find /usr/local/bin /opt -type f -executable 2>/dev/null | while read f; do
    sha256sum \"\$f\" 2>/dev/null
  done | head -20
"

# 특정 해시 검색 (IOC 해시)
# IOC_HASH="abc123..."
# sshpass -p1 ssh user@192.168.208.142 "sha256sum /path/to/file | grep '$IOC_HASH'"
```

### 3.5 실습: 도메인/DNS 헌팅

```bash
# Suricata의 DNS 로그에서 의심 도메인 검색
sshpass -p1 ssh user@192.168.208.150 "cat /var/log/suricata/eve.json 2>/dev/null | python3 -c \"
import sys, json
from collections import Counter
domains = Counter()
for line in sys.stdin:
    try:
        e = json.loads(line)
        if e.get('event_type') == 'dns':
            d = e.get('dns',{}).get('rrname','')
            if d: domains[d] += 1
    except: pass
print('=== DNS 쿼리 Top 20 ===')
for d, c in domains.most_common(20):
    print(f'  {c:4d}: {d}')
\" 2>/dev/null"

# DGA(Domain Generation Algorithm) 의심 도메인 탐지
# 긴 랜덤 문자열 도메인
sshpass -p1 ssh user@192.168.208.150 "cat /var/log/suricata/eve.json 2>/dev/null | python3 -c \"
import sys, json, re
for line in sys.stdin:
    try:
        e = json.loads(line)
        if e.get('event_type') == 'dns':
            d = e.get('dns',{}).get('rrname','')
            # 도메인 길이가 20자 이상이고 숫자+알파벳 혼합
            parts = d.split('.')
            if parts and len(parts[0]) > 20:
                print(f'  DGA 의심: {d}')
    except: pass
\" 2>/dev/null | head -10"
```

---

## 4. 위협 인텔리전스 피드 통합

### 4.1 Wazuh와 CTI 통합

```bash
# Wazuh CDB 리스트 (차단 IP 목록)
sshpass -p1 ssh user@192.168.208.152 "ls /var/ossec/etc/lists/ 2>/dev/null"

# 기존 CDB 리스트 내용
sshpass -p1 ssh user@192.168.208.152 "head -10 /var/ossec/etc/lists/amazon-ip-ranges 2>/dev/null || echo 'CDB 리스트 없음'"
```

### 4.2 IOC 자동 업데이트 개념

```
[OpenCTI] → STIX/TAXII 피드 → [Wazuh CDB 리스트] → [탐지 규칙]
         → [nftables 차단 목록] → [방화벽 자동 차단]
```

---

## 5. Wazuh에서 CTI 활용

### 5.1 Wazuh VirusTotal 통합

```bash
# Wazuh 설정에서 VirusTotal 통합 확인
sshpass -p1 ssh user@192.168.208.152 "grep -A10 'virustotal' /var/ossec/etc/ossec.conf 2>/dev/null"
```

### 5.2 MITRE ATT&CK 매핑 활용

```bash
# ATT&CK 매핑된 알림 조회
sshpass -p1 ssh user@192.168.208.152 "cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c \"
import sys, json
from collections import Counter
tactics = Counter()
techniques = Counter()
for line in sys.stdin:
    try:
        a = json.loads(line)
        mitre = a.get('rule',{}).get('mitre',{})
        for t in mitre.get('tactic',[]):
            tactics[t] += 1
        for t in mitre.get('technique',[]):
            techniques[t] += 1
    except: pass
if tactics:
    print('=== ATT&CK 전술 ===')
    for t, c in tactics.most_common():
        print(f'  {c:4d}: {t}')
if techniques:
    print()
    print('=== ATT&CK 기법 ===')
    for t, c in techniques.most_common(10):
        print(f'  {c:4d}: {t}')
\" 2>/dev/null"
```

---

## 6. 종합 헌팅 스크립트

```bash
#!/bin/bash
echo "============================================"
echo " 위협 헌팅 실행 - $(date)"
echo "============================================"

# IOC 목록 (실제 환경에서는 CTI 피드에서 가져옴)
echo "[1] IP IOC 검색"
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "--- $ip ---"
  echo -n "  외부 연결: "
  sshpass -p1 ssh user@$ip "ss -tnp state established 2>/dev/null | grep -v '192.168\|10.20\|127.0' | wc -l"
done

echo ""
echo "[2] 비정상 DNS 쿼리"
sshpass -p1 ssh user@192.168.208.150 "cat /var/log/suricata/eve.json 2>/dev/null | python3 -c \"
import sys, json
from collections import Counter
domains = Counter()
for line in sys.stdin:
    try:
        e = json.loads(line)
        if e.get('event_type') == 'dns':
            d = e.get('dns',{}).get('rrname','')
            if d and len(d.split('.')[0]) > 15:
                domains[d] += 1
    except: pass
for d, c in domains.most_common(5):
    print(f'  {c:4d}: {d}')
\" 2>/dev/null"

echo ""
echo "[3] 고위험 Wazuh 알림"
sshpass -p1 ssh user@192.168.208.152 "cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c \"
import sys, json
for line in sys.stdin:
    try:
        a = json.loads(line)
        r = a.get('rule',{})
        if r.get('level',0) >= 12:
            print(f'  [{r[\"level\"]}] {r.get(\"description\",\"\")}')
    except: pass
\" 2>/dev/null | tail -5"

echo ""
echo "[4] 의심 실행 파일"
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  result=$(sshpass -p1 ssh user@$ip "find /tmp /dev/shm -type f -executable 2>/dev/null | wc -l")
  if [ "$result" -gt 0 ] 2>/dev/null; then
    echo "  [!] $ip: /tmp에 실행 파일 $result개"
  fi
done
```

---

## 7. 핵심 정리

1. **CTI** = 맥락 있는 위협 정보 (데이터 > 정보 > 인텔리전스)
2. **IOC** = IP, 도메인, 해시 등 기술적 지표
3. **OpenCTI** = 오픈소스 CTI 관리 플랫폼 (siem:9400)
4. **위협 헌팅** = IOC 기반 능동적 위협 검색
5. **통합** = CTI를 SIEM/방화벽에 자동 연동하여 탐지력 강화

---

## 과제

1. OpenCTI에 접속하여 주요 위협 그룹 3개를 조사하시오
2. IOC 헌팅 스크립트를 실행하고 결과를 보고하시오
3. 위협 헌팅 가설을 1개 수립하고, 검증 과정과 결과를 문서화하시오

---

## 참고 자료

- OpenCTI Documentation (https://docs.opencti.io)
- MISP Threat Intelligence Platform
- SANS Threat Hunting Techniques
- STIX/TAXII 표준 (https://oasis-open.github.io/cti-documentation/)
