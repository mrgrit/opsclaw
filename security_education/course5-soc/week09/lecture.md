# Week 09: 인시던트 대응 절차

## 학습 목표

- 인시던트 대응의 6단계 프로세스를 이해한다
- NIST SP 800-61 기반 대응 절차를 설명할 수 있다
- 각 단계별 실제 수행 활동을 익힌다
- 실습 환경에서 대응 준비 상태를 점검한다

---

## 1. 인시던트 대응 개요

### 1.1 인시던트란?

**보안 인시던트** = 정보 자산의 기밀성, 무결성, 가용성을 위협하는 사건

| 이벤트 | 경보 | 인시던트 |
|--------|------|---------|
| 수백만 건/일 | 수십~수백 건/일 | 0~수 건/일 |
| 모든 로그 | 규칙 매칭 | 실제 위협 확인 |

### 1.2 인시던트 유형

| 유형 | 예시 |
|------|------|
| 비인가 접근 | SSH 무차별 대입, 계정 탈취 |
| 악성코드 | 랜섬웨어, 트로이목마, 웜 |
| 웹 공격 | SQL Injection, XSS, 웹셸 |
| DDoS | 서비스 거부 공격 |
| 내부자 위협 | 데이터 유출, 권한 남용 |
| 데이터 유출 | 개인정보, 영업비밀 유출 |

---

## 2. 대응 6단계 (NIST SP 800-61)

### 2.1 전체 프로세스

```
1. 준비 (Preparation)
   ↓
2. 탐지/분석 (Detection & Analysis)
   ↓
3. 격리/억제 (Containment)
   ↓
4. 근절 (Eradication)
   ↓
5. 복구 (Recovery)
   ↓
6. 사후 활동 (Post-Incident Activity)
```

---

## 3. 1단계: 준비 (Preparation)

### 3.1 준비 항목

| 항목 | 내용 |
|------|------|
| 대응팀 구성 | CERT/CSIRT 멤버, 연락처 |
| 대응 절차서 | 유형별 대응 매뉴얼 |
| 도구 준비 | 분석 도구, 포렌식 키트 |
| 통신 체계 | 보고 채널, 에스컬레이션 절차 |
| 교육/훈련 | 정기 모의 훈련 |

### 3.2 실습: 우리 환경의 준비 상태 점검

```bash
# 탐지 도구 상태
echo "=== 탐지 도구 ==="
echo -n "Wazuh Manager: "
sshpass -p1 ssh user@192.168.208.152 "systemctl is-active wazuh-manager 2>/dev/null"
echo -n "Suricata IPS: "
sshpass -p1 ssh user@192.168.208.150 "systemctl is-active suricata 2>/dev/null"

# 대응 도구 상태
echo ""
echo "=== 대응 도구 ==="
echo -n "방화벽(nftables): "
sshpass -p1 ssh user@192.168.208.150 "sudo nft list ruleset 2>/dev/null | head -1 && echo 'OK'"
echo -n "Active Response: "
sshpass -p1 ssh user@192.168.208.152 "ls /var/ossec/active-response/bin/ 2>/dev/null | wc -l"

# 로그 수집 상태
echo ""
echo "=== 로그 수집 ==="
for ip in 192.168.208.142 192.168.208.150 192.168.208.151; do
  echo -n "$ip Wazuh Agent: "
  sshpass -p1 ssh user@$ip "systemctl is-active wazuh-agent 2>/dev/null || echo 'N/A'"
done

# 백업 상태
echo ""
echo "=== 백업 ==="
sshpass -p1 ssh user@192.168.208.142 "ls /backup/ 2>/dev/null || echo '백업 디렉토리 없음'"
```

---

## 4. 2단계: 탐지 및 분석 (Detection & Analysis)

### 4.1 탐지 소스

| 소스 | 도구 | 위치 |
|------|------|------|
| 시스템 로그 | rsyslog/journald | 각 서버 |
| 네트워크 | Suricata IPS | secu |
| 웹 | BunkerWeb WAF | web |
| 통합 SIEM | Wazuh | siem |
| 위협 인텔리전스 | OpenCTI | siem:9400 |

### 4.2 초기 분석 체크리스트

```bash
# 인시던트 의심 시 수행하는 초기 분석

echo "=== 초기 분석 시작: $(date) ==="

# 1. 고위험 알림 확인
echo ""
echo "[1] 최근 고위험 알림"
sshpass -p1 ssh user@192.168.208.152 "cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c \"
import sys, json
for line in sys.stdin:
    try:
        a = json.loads(line)
        r = a.get('rule',{})
        if r.get('level',0) >= 10:
            print(f'  {a.get(\"timestamp\",\"\")} [{r[\"level\"]}] {r.get(\"description\",\"\")}')
    except: pass
\" 2>/dev/null | tail -5"

# 2. 비정상 프로세스 확인
echo ""
echo "[2] 의심 프로세스"
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "--- $ip ---"
  sshpass -p1 ssh user@$ip "ps aux --sort=-%cpu | head -5"
done

# 3. 네트워크 연결 확인
echo ""
echo "[3] 비정상 네트워크 연결"
sshpass -p1 ssh user@192.168.208.142 "ss -tnp | grep ESTABLISHED"

# 4. 최근 로그인
echo ""
echo "[4] 최근 로그인"
sshpass -p1 ssh user@192.168.208.142 "last | head -10"

# 5. 최근 파일 변경
echo ""
echo "[5] 최근 24시간 내 변경된 중요 파일"
sshpass -p1 ssh user@192.168.208.142 "find /etc -mtime -1 -type f 2>/dev/null | head -10"
```

### 4.3 인시던트 심각도 결정

| 등급 | 기준 | 대응 시간 |
|------|------|----------|
| Critical | 핵심 시스템 침해, 데이터 유출 | 즉시 (1시간 내) |
| High | 비인가 접근 성공, 악성코드 | 4시간 내 |
| Medium | 정책 위반, 스캐닝 | 24시간 내 |
| Low | 정보성 이벤트 | 다음 영업일 |

---

## 5. 3단계: 격리/억제 (Containment)

### 5.1 격리 전략

| 전략 | 방법 | 예시 |
|------|------|------|
| 네트워크 격리 | 방화벽으로 IP/서버 차단 | nftables에 차단 규칙 추가 |
| 계정 잠금 | 침해 계정 비활성화 | passwd -l username |
| 서비스 중지 | 침해 서비스 정지 | systemctl stop service |
| 세션 종료 | 활성 세션 강제 종료 | kill, pkill |

### 5.2 실습: 격리 명령어

```bash
# 의심 IP 차단 (secu 서버 방화벽)
# 주의: 실제 차단은 주의하여 수행
echo "=== IP 차단 예시 ==="
echo "sudo nft add rule inet filter input ip saddr 10.0.0.1 drop"
echo "(실제 실행하지 않음 - 시연용)"

# 계정 잠금
echo "=== 계정 잠금 예시 ==="
echo "sudo passwd -l suspicious_user"

# 활성 세션 확인 및 종료
sshpass -p1 ssh user@192.168.208.142 "who"
echo "강제 종료: sudo pkill -u suspicious_user"

# 의심 프로세스 확인
sshpass -p1 ssh user@192.168.208.142 "ps aux | grep -E 'nc |ncat |socat |python.*http' | grep -v grep"
```

---

## 6. 4단계: 근절 (Eradication)

### 6.1 근절 활동

```bash
# 1. 악성 파일 제거
echo "find / -name '*.php' -newer /tmp/reference_time -type f 2>/dev/null"

# 2. 백도어 확인
echo "=== cron 작업 확인 ==="
sshpass -p1 ssh user@192.168.208.142 "crontab -l 2>/dev/null; ls -la /etc/cron.d/ 2>/dev/null"

echo "=== authorized_keys 확인 ==="
sshpass -p1 ssh user@192.168.208.142 "cat ~/.ssh/authorized_keys 2>/dev/null || echo '없음'"

# 3. 비밀번호 변경
echo "=== 비밀번호 변경 필요 계정 ==="
sshpass -p1 ssh user@192.168.208.142 "awk -F: '\$3>=1000 && \$3<65534 {print \$1}' /etc/passwd"

# 4. 취약점 패치
echo "=== 패치 현황 ==="
sshpass -p1 ssh user@192.168.208.142 "apt list --upgradable 2>/dev/null | head -5"
```

---

## 7. 5단계: 복구 (Recovery)

### 7.1 복구 활동

```bash
# 1. 서비스 정상 동작 확인
echo "=== 서비스 상태 ==="
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "--- $ip ---"
  sshpass -p1 ssh user@$ip "systemctl list-units --type=service --state=failed --no-pager"
done

# 2. 모니터링 강화
echo "=== 모니터링 상태 ==="
sshpass -p1 ssh user@192.168.208.152 "systemctl is-active wazuh-manager 2>/dev/null"

# 3. 방화벽 규칙 확인
sshpass -p1 ssh user@192.168.208.150 "sudo nft list ruleset 2>/dev/null | wc -l"
```

---

## 8. 6단계: 사후 활동 (Lessons Learned)

### 8.1 사후 검토 보고서

```
=== 인시던트 사후 보고서 ===

1. 인시던트 요약
   - 유형: (SSH 무차별 대입 / 웹 공격 등)
   - 발생일시: YYYY-MM-DD HH:MM
   - 탐지일시: YYYY-MM-DD HH:MM
   - 종료일시: YYYY-MM-DD HH:MM
   - MTTD (탐지까지 시간): X시간
   - MTTR (복구까지 시간): X시간

2. 타임라인
   HH:MM - 공격 시작
   HH:MM - 탐지
   HH:MM - 분석 시작
   HH:MM - 격리 조치
   HH:MM - 근절 완료
   HH:MM - 복구 완료

3. 근본 원인 (Root Cause)
   - (취약점, 설정 오류, 인적 실수 등)

4. 영향 범위
   - 침해된 시스템: X대
   - 유출된 데이터: (있음/없음)
   - 서비스 중단 시간: X시간

5. 재발 방지 대책
   - 즉시 조치: (완료)
   - 단기 개선: (1개월 내)
   - 중장기 개선: (3개월 내)

6. 교훈 (Lessons Learned)
   - 잘 된 점:
   - 개선할 점:
   - 필요한 자원/도구:
```

---

## 9. 대응 플레이북 개념

### 9.1 유형별 대응 플레이북

```
[SSH 무차별 대입 플레이북]
1. 탐지: Wazuh Rule 5710 (Level 10+)
2. 분석: auth.log에서 출발지 IP, 시도 횟수, 성공 여부 확인
3. 격리: nftables에서 출발지 IP 차단
4. 근절: 비밀번호 변경, SSH 키 기반 인증 전환
5. 복구: SSH 서비스 정상 확인
6. 사후: MaxAuthTries 강화, fail2ban 도입 검토

[웹 공격 플레이북]
1. 탐지: Suricata Alert, WAF 차단 로그
2. 분석: 공격 유형(SQLi/XSS) 확인, 성공 여부
3. 격리: WAF 규칙 강화, 출발지 IP 차단
4. 근절: 취약점 패치, 입력값 검증
5. 복구: 웹 서비스 정상 확인
6. 사후: 보안 코딩 교육, 정기 모의해킹
```

---

## 10. 핵심 정리

1. **6단계** = 준비 → 탐지/분석 → 격리 → 근절 → 복구 → 사후활동
2. **준비** = 도구, 팀, 절차, 훈련이 핵심
3. **격리** = 네트워크 차단, 계정 잠금, 서비스 중지
4. **MTTD/MTTR** = 탐지/복구 시간 = SOC의 핵심 성과 지표
5. **사후 활동** = 교훈을 통한 지속적 개선

---

## 과제

1. 실습 환경의 인시던트 대응 준비 상태를 점검하고 보고하시오
2. "SSH 무차별 대입 공격" 시나리오에 대한 대응 플레이북을 작성하시오
3. 초기 분석 스크립트를 작성하여 인시던트 의심 시 즉시 실행할 수 있도록 하시오

---

## 참고 자료

- NIST SP 800-61 Rev.2: Computer Security Incident Handling Guide
- SANS Incident Handler's Handbook
- KISA 침해사고 대응 가이드
