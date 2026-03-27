# Week 09: 인시던트 대응 절차 (상세 버전)

## 학습 목표
- 인시던트 대응의 6단계 프로세스를 이해한다
- NIST SP 800-61 기반 대응 절차를 설명할 수 있다
- 각 단계별 실제 수행 활동을 익힌다
- 실습 환경에서 대응 준비 상태를 점검한다


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
sshpass -p1 ssh siem@10.20.30.100 "systemctl is-active wazuh-manager 2>/dev/null"
echo -n "Suricata IPS: "
sshpass -p1 ssh secu@10.20.30.1 "systemctl is-active suricata 2>/dev/null"

# 대응 도구 상태
echo ""
echo "=== 대응 도구 ==="
echo -n "방화벽(nftables): "
sshpass -p1 ssh secu@10.20.30.1 "sudo nft list ruleset 2>/dev/null | head -1 && echo 'OK'"
echo -n "Active Response: "
sshpass -p1 ssh siem@10.20.30.100 "ls /var/ossec/active-response/bin/ 2>/dev/null | wc -l"

# 로그 수집 상태
echo ""
echo "=== 로그 수집 ==="
for ip in 10.20.30.201 10.20.30.1 10.20.30.80; do
  echo -n "$ip Wazuh Agent: "
  sshpass -p1 ssh user@$ip "systemctl is-active wazuh-agent 2>/dev/null || echo 'N/A'"
done

# 백업 상태
echo ""
echo "=== 백업 ==="
sshpass -p1 ssh opsclaw@10.20.30.201 "ls /backup/ 2>/dev/null || echo '백업 디렉토리 없음'"
```

---

## 4. 2단계: 탐지 및 분석 (Detection & Analysis)

### 4.1 탐지 소스

| 소스 | 도구 | 위치 |
|------|------|------|
| 시스템 로그 | rsyslog/journald | 각 서버 |
| 네트워크 | Suricata IPS | secu |
| 웹 | Apache+ModSecurity WAF | web |
| 통합 SIEM | Wazuh | siem |
| 위협 인텔리전스 | OpenCTI | siem:9400 |

### 4.2 초기 분석 체크리스트

```bash
# 인시던트 의심 시 수행하는 초기 분석

echo "=== 초기 분석 시작: $(date) ==="

# 1. 고위험 알림 확인
echo ""
echo "[1] 최근 고위험 알림"
sshpass -p1 ssh siem@10.20.30.100 "cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c \"
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
for ip in 10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100; do
  echo "--- $ip ---"
  sshpass -p1 ssh user@$ip "ps aux --sort=-%cpu | head -5"
done

# 3. 네트워크 연결 확인
echo ""
echo "[3] 비정상 네트워크 연결"
sshpass -p1 ssh opsclaw@10.20.30.201 "ss -tnp | grep ESTABLISHED"

# 4. 최근 로그인
echo ""
echo "[4] 최근 로그인"
sshpass -p1 ssh opsclaw@10.20.30.201 "last | head -10"

# 5. 최근 파일 변경
echo ""
echo "[5] 최근 24시간 내 변경된 중요 파일"
sshpass -p1 ssh opsclaw@10.20.30.201 "find /etc -mtime -1 -type f 2>/dev/null | head -10"
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
sshpass -p1 ssh opsclaw@10.20.30.201 "who"
echo "강제 종료: sudo pkill -u suspicious_user"

# 의심 프로세스 확인
sshpass -p1 ssh opsclaw@10.20.30.201 "ps aux | grep -E 'nc |ncat |socat |python.*http' | grep -v grep"
```

---

## 6. 4단계: 근절 (Eradication)

### 6.1 근절 활동

```bash
# 1. 악성 파일 제거
echo "find / -name '*.php' -newer /tmp/reference_time -type f 2>/dev/null"

# 2. 백도어 확인
echo "=== cron 작업 확인 ==="
sshpass -p1 ssh opsclaw@10.20.30.201 "crontab -l 2>/dev/null; ls -la /etc/cron.d/ 2>/dev/null"

echo "=== authorized_keys 확인 ==="
sshpass -p1 ssh opsclaw@10.20.30.201 "cat ~/.ssh/authorized_keys 2>/dev/null || echo '없음'"

# 3. 비밀번호 변경
echo "=== 비밀번호 변경 필요 계정 ==="
sshpass -p1 ssh opsclaw@10.20.30.201 "awk -F: '\$3>=1000 && \$3<65534 {print \$1}' /etc/passwd"

# 4. 취약점 패치
echo "=== 패치 현황 ==="
sshpass -p1 ssh opsclaw@10.20.30.201 "apt list --upgradable 2>/dev/null | head -5"
```

---

## 7. 5단계: 복구 (Recovery)

### 7.1 복구 활동

```bash
# 1. 서비스 정상 동작 확인
echo "=== 서비스 상태 ==="
for ip in 10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100; do
  echo "--- $ip ---"
  sshpass -p1 ssh user@$ip "systemctl list-units --type=service --state=failed --no-pager"
done

# 2. 모니터링 강화
echo "=== 모니터링 상태 ==="
sshpass -p1 ssh siem@10.20.30.100 "systemctl is-active wazuh-manager 2>/dev/null"

# 3. 방화벽 규칙 확인
sshpass -p1 ssh secu@10.20.30.1 "sudo nft list ruleset 2>/dev/null | wc -l"
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


---

---

## 심화: 보안관제(SOC) 실무 보충

### 경보 분석 워크플로

```
[1단계] 경보 수신
    → Wazuh Dashboard에서 경보 확인
    → 심각도(level), 출처(src), 대상(dst) 즉시 파악

[2단계] 초기 분류 (Triage, 5분 이내)
    → 오탐(False Positive)인가? → 기존 사례와 비교
    → 실제 위협인가? → IOC 확인 (악성 IP, 해시)
    → 긴급도 결정: P1(즉시) / P2(4시간) / P3(24시간) / P4(일반)

[3단계] 심층 분석 (Investigation)
    → 관련 로그 추가 수집 (시간 범위 확대)
    → ATT&CK 기법 매핑
    → 영향 범위 파악 (어떤 서버, 어떤 데이터)

[4단계] 대응 (Response)
    → 격리: 감염 서버 네트워크 분리
    → 차단: 공격자 IP 방화벽 차단
    → 복구: 백업에서 복원, 패치 적용

[5단계] 사후 분석 (Post-Incident)
    → 타임라인 작성 (attack→detect→respond→recover)
    → 탐지 룰 개선
    → 보고서 작성
```

### Wazuh 로그 분석 실습

```bash
# siem 서버에서 최근 경보 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100 "
  echo '=== 최근 경보 (level >= 7) ==='
  sudo cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | \
    python3 -c '
import sys, json
for line in sys.stdin:
    try:
        a = json.loads(line.strip())
        if a.get("rule",{}).get("level",0) >= 7:
            print(f"[{a[\"rule\"][\"level\"]}] {a[\"rule\"].get(\"description\",\"?\")[:60]} src={a.get(\"srcip\",\"?\")}")
    except: pass
' 2>/dev/null | tail -10
" 2>/dev/null
```

### SIGMA 룰 작성 가이드

```yaml
# SIGMA 룰 기본 구조
title: SSH Brute Force Detection     # 룰 이름
id: 12345678-abcd-efgh-...           # 고유 ID (UUID)
status: experimental                  # experimental/test/stable
description: |                        # 상세 설명
    5분 내 동일 IP에서 10회 이상 SSH 인증 실패 탐지
author: Student Name                  # 작성자
date: 2026/03/27                      # 작성일

logsource:                            # 어떤 로그를 볼 것인가
    product: linux
    service: sshd

detection:                            # 어떤 패턴을 찾을 것인가
    selection:
        eventid: 4625                 # 또는 sshd 실패 이벤트
    filter:                           # 제외 조건
        srcip: "10.20.30.*"           # 내부 IP는 제외
    condition: selection and not filter
    timeframe: 5m                     # 시간 범위
    count: 10                         # 최소 횟수

level: high                           # 심각도
tags:                                 # ATT&CK 매핑
    - attack.credential_access
    - attack.t1110.001
falsepositives:                       # 오탐 가능성
    - 자동화 스크립트의 반복 접속
    - 비밀번호 정책 변경 후 재접속
```

### TTD/TTR 측정 실습

```bash
# 공격→탐지 시간(TTD) 측정 시나리오
echo "=== 공격 시작 시각 기록 ==="
ATTACK_TIME=$(date +%s)
echo "공격 시작: $(date)"

# (여기서 공격 실행)

echo "=== SIEM 경보 확인 ==="
# (경보 발생 시각 확인)
DETECT_TIME=$(date +%s)
TTD=$((DETECT_TIME - ATTACK_TIME))
echo "TTD (탐지 소요 시간): ${TTD}초"
```


---

## 자가 점검 퀴즈 (10문항)

이번 주차의 핵심 내용을 점검한다. 8/10 이상 정답을 목표로 한다.

**Q1.** "Week 09: 인시던트 대응 절차"에서 가장 핵심적인 학습 목표는?
- (a) 데이터베이스 최적화  (b) **보안관제/SOC의 원리와 실습**  (c) UI 개발  (d) 네트워크 속도

**Q2.** "1. 인시던트 대응 개요"의 보안 관점에서의 의의는?
- (a) 성능 향상  (b) **보안 위협 이해 또는 방어 역량 강화**  (c) 비용 절감  (d) 사용성 개선

**Q3.** "2. 대응 6단계 (NIST SP 800-61)"에서 사용하는 주요 도구/기법은?
- (a) 워드프로세서  (b) **보안관제/SOC 전용 도구/명령**  (c) 게임 엔진  (d) 그래픽 도구

**Q4.** 이번 실습에서 OpsClaw evidence가 제공하는 가치는?
- (a) 속도  (b) **작업 증적의 자동 기록과 감사 추적**  (c) 화면 출력  (d) 파일 압축

**Q5.** "3. 1단계: 준비 (Preparation)"의 실무 활용 방안은?
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
