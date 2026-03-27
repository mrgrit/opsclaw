# Week 10: 인시던트 대응 (1) - 웹 공격

## 학습 목표

- SQL Injection 공격의 탐지부터 대응까지 전 과정을 수행한다
- 웹 로그에서 공격 증거를 수집하고 분석한다
- WAF/IPS를 활용한 차단 조치를 수행한다
- 웹 공격 인시던트 대응 보고서를 작성한다

---

## 1. 시나리오: JuiceShop 웹 공격

### 1.1 환경

- **대상**: web 서버 (192.168.208.151) - OWASP JuiceShop
- **방어**: BunkerWeb WAF, Suricata IPS (secu), Wazuh SIEM
- JuiceShop은 **의도적으로 취약한** 웹 애플리케이션이다

### 1.2 공격 시나리오

```
공격자 → [Suricata IPS] → [BunkerWeb WAF] → [JuiceShop]
                  ↓                ↓                ↓
              fast.log        access.log        app.log
                  ↓                ↓                ↓
              [Wazuh SIEM] ← 로그 수집 ← [Wazuh Agent]
```

---

## 2. 탐지 (Detection)

### 2.1 Suricata에서 탐지

```bash
# SQL Injection 관련 Suricata 알림
sshpass -p1 ssh user@192.168.208.150 "grep -iE 'sql|injection|sqli' /var/log/suricata/fast.log 2>/dev/null | tail -10"

# 웹 공격 전체 알림
sshpass -p1 ssh user@192.168.208.150 "grep -iE 'web|http|xss|rfi|lfi' /var/log/suricata/fast.log 2>/dev/null | tail -10"

# eve.json에서 HTTP 이벤트
sshpass -p1 ssh user@192.168.208.150 "cat /var/log/suricata/eve.json 2>/dev/null | python3 -c \"
import sys, json
for line in sys.stdin:
    try:
        e = json.loads(line)
        if e.get('event_type') == 'alert':
            a = e.get('alert',{})
            cat = a.get('category','')
            if 'web' in cat.lower() or 'sql' in cat.lower() or 'xss' in cat.lower():
                print(f'  [{a.get(\"severity\",\"\")}] {a.get(\"signature\",\"\")}')
                print(f'    {e.get(\"src_ip\",\"\")}:{e.get(\"src_port\",\"\")} -> {e.get(\"dest_ip\",\"\")}:{e.get(\"dest_port\",\"\")}')
    except: pass
\" 2>/dev/null | tail -20"
```

### 2.2 WAF에서 탐지

```bash
# WAF 차단 로그 (403 응답)
sshpass -p1 ssh user@192.168.208.151 "grep ' 403 ' /var/log/nginx/access.log 2>/dev/null | tail -10"
sshpass -p1 ssh user@192.168.208.151 "grep ' 403 ' /var/log/bunkerweb/access.log 2>/dev/null | tail -10"

# WAF 에러 로그
sshpass -p1 ssh user@192.168.208.151 "tail -10 /var/log/nginx/error.log 2>/dev/null"
```

### 2.3 웹 로그에서 탐지

```bash
# SQL Injection 패턴 검색
sshpass -p1 ssh user@192.168.208.151 "grep -iE \"union.*select|or.*1=1|'.*or.*'|drop.*table|insert.*into|sleep\(|benchmark\(\" \
  /var/log/nginx/access.log 2>/dev/null | tail -10"

# XSS 패턴 검색
sshpass -p1 ssh user@192.168.208.151 "grep -iE '<script|javascript:|onerror=|onload=|alert\(' \
  /var/log/nginx/access.log 2>/dev/null | tail -10"

# Path Traversal 패턴 검색
sshpass -p1 ssh user@192.168.208.151 "grep -iE '\.\.\/|%2e%2e|/etc/passwd|/etc/shadow' \
  /var/log/nginx/access.log 2>/dev/null | tail -10"
```

---

## 3. 분석 (Analysis)

### 3.1 공격자 식별

```bash
# 공격 요청을 보낸 IP 목록
sshpass -p1 ssh user@192.168.208.151 "grep -iE 'union|select|script|alert|\.\./' /var/log/nginx/access.log 2>/dev/null | \
  awk '{print \$1}' | sort | uniq -c | sort -rn | head -5"
```

### 3.2 공격 타임라인 구성

```bash
# 특정 공격자 IP의 전체 활동 추적
ATTACKER_IP="10.0.0.1"  # 실제 발견된 IP로 변경

echo "=== $ATTACKER_IP 활동 타임라인 ==="

echo "[웹 접근]"
sshpass -p1 ssh user@192.168.208.151 "grep '$ATTACKER_IP' /var/log/nginx/access.log 2>/dev/null | head -20"

echo ""
echo "[IPS 탐지]"
sshpass -p1 ssh user@192.168.208.150 "grep '$ATTACKER_IP' /var/log/suricata/fast.log 2>/dev/null"

echo ""
echo "[Wazuh 알림]"
sshpass -p1 ssh user@192.168.208.152 "cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c \"
import sys, json
for line in sys.stdin:
    try:
        a = json.loads(line)
        if '$ATTACKER_IP' in str(a):
            r = a.get('rule',{})
            print(f'  {a.get(\"timestamp\",\"\")} [{r.get(\"level\",0)}] {r.get(\"description\",\"\")}')
    except: pass
\" 2>/dev/null"
```

### 3.3 공격 성공 여부 판단

```bash
# 공격 요청의 응답 코드 분석
sshpass -p1 ssh user@192.168.208.151 "grep -iE 'union|select|script' /var/log/nginx/access.log 2>/dev/null | \
  awk '{print \$9}' | sort | uniq -c | sort -rn"

# 200 응답 = 공격 성공 가능성
# 403 응답 = WAF에 의해 차단
# 500 응답 = 서버 오류 (공격이 부분적으로 작동)
```

### 3.4 공격 영향 분석

```bash
# 데이터베이스 접근 여부 확인 (JuiceShop SQLite)
sshpass -p1 ssh user@192.168.208.151 "find / -name '*.sqlite' -o -name '*.db' 2>/dev/null | head -5"

# 서버 리소스 영향
sshpass -p1 ssh user@192.168.208.151 "uptime; free -h | grep Mem; df -h / | tail -1"
```

---

## 4. 격리/억제 (Containment)

### 4.1 공격자 IP 차단

```bash
# 방화벽에서 차단 (secu 서버)
echo "=== IP 차단 명령 (시연) ==="
echo "sshpass -p1 ssh user@192.168.208.150 'sudo nft add rule inet filter input ip saddr $ATTACKER_IP drop'"
echo ""
echo "현재 차단 규칙:"
sshpass -p1 ssh user@192.168.208.150 "sudo nft list ruleset 2>/dev/null | grep 'drop' | head -5"
```

### 4.2 WAF 규칙 강화

```bash
# BunkerWeb/nginx WAF 설정 확인
sshpass -p1 ssh user@192.168.208.151 "cat /etc/nginx/conf.d/*.conf 2>/dev/null | head -20"
sshpass -p1 ssh user@192.168.208.151 "ls /etc/bunkerweb/ 2>/dev/null"
```

### 4.3 웹 서비스 상태 확인

```bash
# 웹 서비스 정상 동작 확인
sshpass -p1 ssh user@192.168.208.151 "curl -s -o /dev/null -w '%{http_code}' http://localhost/ 2>/dev/null"
```

---

## 5. 근절 및 복구

### 5.1 근절

```bash
# 웹셸 여부 확인 (의심 파일 검색)
sshpass -p1 ssh user@192.168.208.151 "find /var/www -name '*.php' -newer /etc/hostname -type f 2>/dev/null"
sshpass -p1 ssh user@192.168.208.151 "find /tmp -type f -executable 2>/dev/null"

# 서버 프로세스 확인 (비정상 프로세스)
sshpass -p1 ssh user@192.168.208.151 "ps aux | grep -E 'nc |ncat |python.*http|perl.*socket' | grep -v grep"
```

### 5.2 복구

```bash
# 서비스 상태 확인
sshpass -p1 ssh user@192.168.208.151 "systemctl status nginx bunkerweb 2>/dev/null | grep Active"

# 로그 수집 정상 확인
sshpass -p1 ssh user@192.168.208.151 "systemctl is-active wazuh-agent 2>/dev/null"
```

---

## 6. 증거 수집 및 보존

```bash
# 증거 보존 (타임스탬프 포함 복사)
EVIDENCE="/tmp/web_incident_$(date +%Y%m%d_%H%M)"

echo "증거 수집: $EVIDENCE"

# 웹 로그
sshpass -p1 ssh user@192.168.208.151 "cat /var/log/nginx/access.log" 2>/dev/null > /tmp/web_access_evidence.txt

# IPS 로그
sshpass -p1 ssh user@192.168.208.150 "cat /var/log/suricata/fast.log" 2>/dev/null > /tmp/suricata_evidence.txt

# Wazuh 알림
sshpass -p1 ssh user@192.168.208.152 "cat /var/ossec/logs/alerts/alerts.json" 2>/dev/null > /tmp/wazuh_evidence.txt

# 해시값 생성
sha256sum /tmp/*_evidence.txt 2>/dev/null
```

---

## 7. ATT&CK 매핑

| 단계 | ATT&CK 전술 | 기법 | 증거 |
|------|------------|------|------|
| 정찰 | TA0043 | T1595 Active Scanning | 대량 404, 디렉토리 스캔 |
| 초기접근 | TA0001 | T1190 Exploit Public-Facing App | SQLi 요청 |
| 실행 | TA0002 | T1059 Command and Script Interpreter | SQL 명령 실행 |
| 자격증명 | TA0006 | T1212 Exploitation for Credential Access | DB에서 인증정보 추출 |
| 유출 | TA0010 | T1048 Exfiltration Over Alternative Protocol | HTTP 응답으로 데이터 유출 |

---

## 8. 인시던트 대응 보고서

```
=== 웹 공격 인시던트 대응 보고서 ===

1. 인시던트 요약
   - 유형: SQL Injection
   - 대상: JuiceShop (192.168.208.151)
   - 공격자: X.X.X.X
   - 발생: 2026-XX-XX XX:XX
   - 탐지: 2026-XX-XX XX:XX (Suricata/Wazuh)
   - 격리: 2026-XX-XX XX:XX (방화벽 차단)
   - 종료: 2026-XX-XX XX:XX

2. 공격 타임라인
   - XX:XX 디렉토리 스캐닝 시작
   - XX:XX SQL Injection 시도 시작
   - XX:XX Suricata에서 탐지
   - XX:XX SOC 분석원 확인
   - XX:XX 방화벽에서 IP 차단

3. 영향 분석
   - 공격 성공 여부:
   - 데이터 유출:
   - 서비스 영향:

4. 조치 내역
   - 격리: IP 차단
   - 근절: (해당 사항)
   - 복구: 서비스 정상 확인

5. 재발 방지
   - WAF 규칙 강화
   - 입력값 검증
   - 정기 취약점 점검

6. ATT&CK 매핑
   (위 표 참조)
```

---

## 9. 핵심 정리

1. **웹 공격 탐지** = Suricata + WAF + 웹 로그 3중 확인
2. **분석** = 공격자 식별, 타임라인, 성공 여부 판단
3. **격리** = 방화벽 차단, WAF 강화
4. **증거 보존** = 로그 복사 + 해시값으로 무결성 보장
5. **ATT&CK 매핑** = T1190(Exploit Public-Facing App)이 핵심

---

## 과제

1. 웹 서버 로그에서 공격 시도를 탐지하고 공격자 IP를 식별하시오
2. 공격 타임라인을 구성하시오
3. 인시던트 대응 보고서를 작성하시오

---

## 참고 자료

- OWASP Top 10 2021
- OWASP JuiceShop Solutions
- SANS Web Application Incident Handling
