# Week 10: 리스크 평가 실습

## 학습 목표

- 리스크 평가의 전체 프로세스를 이해한다
- 자산 식별, 위협 분석, 취약점 분석을 수행할 수 있다
- 리스크 매트릭스를 작성하고 리스크를 산정할 수 있다
- 리스크 처리 계획을 수립한다

---

## 1. 리스크 평가 개요

### 1.1 프로세스

```
자산 식별 → 위협 식별 → 취약점 식별 → 리스크 산정 → 리스크 평가 → 리스크 처리
```

### 1.2 관련 표준

| 표준 | 내용 |
|------|------|
| ISO 27005 | 정보보안 리스크 관리 가이드라인 |
| ISO 31000 | 범용 리스크 관리 프레임워크 |
| NIST SP 800-30 | 리스크 평가 수행 가이드 |
| ISMS-P 1.2 | 위험 관리 (1.2.1~1.2.3) |

### 1.3 핵심 용어

| 용어 | 정의 |
|------|------|
| 자산 (Asset) | 보호해야 할 가치가 있는 것 |
| 위협 (Threat) | 자산에 손해를 끼칠 수 있는 잠재적 원인 |
| 취약점 (Vulnerability) | 위협에 의해 이용될 수 있는 약점 |
| 리스크 (Risk) | 위협이 취약점을 이용하여 자산에 손해를 끼칠 가능성 |
| 영향 (Impact) | 리스크가 실현되었을 때의 결과 |
| 가능성 (Likelihood) | 리스크가 실현될 확률 |

---

## 2. 단계 1: 자산 식별

### 2.1 자산 분류

| 분류 | 예시 |
|------|------|
| 정보 자산 | 데이터베이스, 설정 파일, 로그 |
| 소프트웨어 자산 | OS, 애플리케이션, 미들웨어 |
| 하드웨어 자산 | 서버, 네트워크 장비, 저장장치 |
| 서비스 자산 | 웹 서비스, API, 모니터링 |
| 인적 자산 | 관리자, 운영자, 사용자 |

### 2.2 실습: 자산 인벤토리 수집

```bash
# 하드웨어 자산 정보 수집
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "========== $ip =========="
  sshpass -p1 ssh user@$ip "
    echo '[호스트명]' && hostname
    echo '[OS]' && cat /etc/os-release | grep PRETTY_NAME
    echo '[CPU]' && lscpu | grep 'Model name'
    echo '[메모리]' && free -h | grep Mem
    echo '[디스크]' && df -h / | tail -1
    echo '[커널]' && uname -r
  " 2>/dev/null
done
```

```bash
# 소프트웨어 자산 수집
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "========== $ip: 실행 서비스 =========="
  sshpass -p1 ssh user@$ip "systemctl list-units --type=service --state=running --no-pager | grep -v 'loaded units' | tail -n +2 | head -15"
done
```

```bash
# 네트워크 자산 (열린 포트 = 서비스)
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "========== $ip: 열린 포트 =========="
  sshpass -p1 ssh user@$ip "ss -tlnp 2>/dev/null | grep LISTEN"
done
```

### 2.3 자산 가치 평가

| 등급 | 점수 | 기준 |
|------|------|------|
| 상 (High) | 3 | 서비스 중단 시 전체 시스템 영향, 기밀 데이터 포함 |
| 중 (Medium) | 2 | 일부 기능 영향, 내부 데이터 |
| 하 (Low) | 1 | 대체 가능, 공개 데이터 |

```
자산 목록 (실습 환경):
| 자산명 | 유형 | 서버 | 가치 | 사유 |
|--------|------|------|------|------|
| PostgreSQL DB | 정보 | opsclaw | 3(상) | 전체 운영 데이터 |
| Manager API | 서비스 | opsclaw | 3(상) | 중앙 제어 서비스 |
| Wazuh SIEM | 서비스 | siem | 3(상) | 보안 모니터링 핵심 |
| Suricata IPS | 소프트웨어 | secu | 2(중) | 네트워크 보호 |
| JuiceShop | 서비스 | web | 1(하) | 테스트용 취약 앱 |
| nftables 방화벽 | 소프트웨어 | secu | 3(상) | 네트워크 경계 보호 |
| SSH 서비스 | 서비스 | 전체 | 2(중) | 원격 관리 접근 |
```

---

## 3. 단계 2: 위협 식별

### 3.1 위협 분류

| 유형 | 위협 | 예시 |
|------|------|------|
| 의도적 (외부) | 해킹, 악성코드, DDoS | 외부 공격자의 SSH 무차별 대입 |
| 의도적 (내부) | 내부자 위협, 데이터 유출 | 관리자 권한 남용 |
| 비의도적 | 설정 오류, 실수 | 방화벽 규칙 잘못 설정 |
| 환경적 | 하드웨어 장애, 자연재해 | 디스크 고장 |

### 3.2 실습: 실제 위협 증거 수집

```bash
# SSH 무차별 대입 시도 (외부 위협)
sshpass -p1 ssh user@192.168.208.142 "grep 'Failed password' /var/log/auth.log 2>/dev/null | wc -l"
sshpass -p1 ssh user@192.168.208.142 "grep 'Failed password' /var/log/auth.log 2>/dev/null | awk '{print \$(NF-3)}' | sort | uniq -c | sort -rn | head -5"

# Suricata 탐지 이벤트 (네트워크 위협)
sshpass -p1 ssh user@192.168.208.150 "wc -l /var/log/suricata/fast.log 2>/dev/null || echo '0'"
sshpass -p1 ssh user@192.168.208.150 "tail -5 /var/log/suricata/fast.log 2>/dev/null"

# Wazuh 고위험 알림 (복합 위협)
sshpass -p1 ssh user@192.168.208.152 "cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c \"
import sys, json
levels = {}
for line in sys.stdin:
    try:
        a = json.loads(line)
        l = a.get('rule',{}).get('level',0)
        levels[l] = levels.get(l,0)+1
    except: pass
for l in sorted(levels.keys(), reverse=True)[:5]:
    print(f'  Level {l}: {levels[l]}건')
\" 2>/dev/null"
```

### 3.3 위협 가능성 평가

| 등급 | 점수 | 기준 |
|------|------|------|
| 높음 (High) | 3 | 이미 발생했거나 매우 높은 확률 |
| 중간 (Medium) | 2 | 발생 가능성 있음 |
| 낮음 (Low) | 1 | 거의 발생하지 않음 |

---

## 4. 단계 3: 취약점 식별

### 4.1 실습: 기술적 취약점 점검

```bash
# 취약점 1: 비밀번호 정책 미설정
sshpass -p1 ssh user@192.168.208.142 "grep PASS_MAX_DAYS /etc/login.defs | grep -v '^#'"

# 취약점 2: root 로그인 허용
sshpass -p1 ssh user@192.168.208.142 "grep PermitRootLogin /etc/ssh/sshd_config | grep -v '^#'"

# 취약점 3: 불필요한 포트 개방
sshpass -p1 ssh user@192.168.208.142 "ss -tlnp | grep LISTEN | wc -l"

# 취약점 4: 패치 미적용
sshpass -p1 ssh user@192.168.208.142 "apt list --upgradable 2>/dev/null | wc -l"

# 취약점 5: auditd 미설치
sshpass -p1 ssh user@192.168.208.142 "systemctl is-active auditd 2>/dev/null || echo '미설치'"

# 취약점 6: TMOUT 미설정
sshpass -p1 ssh user@192.168.208.142 "grep TMOUT /etc/profile /etc/bash.bashrc 2>/dev/null || echo '미설정'"

# 취약점 7: 커널 보안 파라미터
sshpass -p1 ssh user@192.168.208.142 "sysctl net.ipv4.conf.all.accept_redirects 2>/dev/null"
```

---

## 5. 단계 4: 리스크 산정

### 5.1 리스크 산정 공식

```
리스크 = 자산 가치 x 위협 가능성 x 취약점 심각도
```

또는 간단히:

```
리스크 = 영향도(Impact) x 가능성(Likelihood)
```

### 5.2 리스크 매트릭스 (5x5)

```
        가능성 →
영향도   1(매우낮음) 2(낮음) 3(보통) 4(높음) 5(매우높음)
  ↓
5(치명적)    5       10      15      20       25
4(높음)      4        8      12      16       20
3(보통)      3        6       9      12       15
2(낮음)      2        4       6       8       10
1(미미)      1        2       3       4        5
```

| 리스크 점수 | 등급 | 조치 |
|------------|------|------|
| 20~25 | 매우 높음 (Critical) | 즉시 조치 필수 |
| 12~19 | 높음 (High) | 우선 조치 |
| 6~11 | 보통 (Medium) | 계획적 조치 |
| 1~5 | 낮음 (Low) | 수용 또는 모니터링 |

### 5.3 실습 환경 리스크 산정 예시

| 자산 | 위협 | 취약점 | 영향도 | 가능성 | 리스크 | 등급 |
|------|------|--------|--------|--------|--------|------|
| PostgreSQL | SQL Injection | 웹앱 입력값 미검증 | 5 | 3 | 15 | High |
| SSH 서비스 | 무차별 대입 | 비밀번호 인증 허용 | 4 | 4 | 16 | High |
| Manager API | 비인가 접근 | 인증 미흡 | 5 | 2 | 10 | Medium |
| 방화벽 | 설정 오류 | 변경관리 미흡 | 5 | 2 | 10 | Medium |
| 로그 데이터 | 증거 인멸 | 중앙 로그 미전송 | 3 | 2 | 6 | Medium |

---

## 6. 단계 5: 리스크 처리

### 6.1 처리 옵션 결정

| 리스크 | 처리 방법 | 구체적 조치 |
|--------|----------|------------|
| SSH 무차별 대입 (16) | 감소 | 키 기반 인증, fail2ban, MaxAuthTries 제한 |
| SQL Injection (15) | 감소 | WAF 강화, 입력값 검증 |
| API 비인가 접근 (10) | 감소 | API Key 인증 (이미 M28에서 구현) |
| 방화벽 설정 오류 (10) | 감소 | 변경관리 절차 수립, 백업 |
| 로그 증거 인멸 (6) | 감소 | Wazuh로 중앙 로그 수집 |

### 6.2 잔여 리스크 (Residual Risk)

조치 후에도 남는 리스크를 산정하고, 경영진이 **수용** 여부를 결정한다.

---

## 7. 종합 실습: 리스크 평가 워크시트

다음을 직접 수행하고 완성하시오:

```bash
# 1단계: 자산 확인
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "=== $ip ==="
  sshpass -p1 ssh user@$ip "hostname; ss -tlnp 2>/dev/null | grep LISTEN | wc -l; echo '서비스 수'"
done

# 2단계: 위협 증거
echo "=== SSH 공격 시도 ==="
sshpass -p1 ssh user@192.168.208.142 "grep 'Failed' /var/log/auth.log 2>/dev/null | wc -l"

echo "=== IPS 탐지 ==="
sshpass -p1 ssh user@192.168.208.150 "wc -l /var/log/suricata/fast.log 2>/dev/null"

# 3단계: 취약점 확인
echo "=== 미패치 현황 ==="
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "$ip: $(sshpass -p1 ssh user@$ip 'apt list --upgradable 2>/dev/null | wc -l') 패키지"
done
```

---

## 8. 핵심 정리

1. **리스크 = 영향도 x 가능성** (또는 자산가치 x 위협 x 취약점)
2. **자산 식별** = 보호 대상을 파악하고 가치를 평가
3. **위협 식별** = 실제 로그를 통해 위협 증거를 수집
4. **리스크 매트릭스** = 정량적으로 우선순위를 결정
5. **처리 계획** = 감소/전가/회피/수용 중 선택

---

## 과제

1. 실습 환경의 자산 목록을 10개 이상 작성하고 가치를 평가하시오
2. 각 자산에 대한 위협과 취약점을 식별하시오
3. 리스크 매트릭스를 완성하고 상위 5개 리스크에 대한 처리 계획을 수립하시오

---

## 참고 자료

- ISO 27005:2022 Information Security Risk Management
- NIST SP 800-30 Risk Assessment Guide
- KISA 위험관리 가이드
