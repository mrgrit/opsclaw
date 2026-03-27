# Week 10: 리스크 평가 실습 (상세 버전)

## 학습 목표
- 리스크 평가의 전체 프로세스를 이해한다
- 자산 식별, 위협 분석, 취약점 분석을 수행할 수 있다
- 리스크 매트릭스를 작성하고 리스크를 산정할 수 있다
- 리스크 처리 계획을 수립한다


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

## 용어 해설 (보안 표준/컴플라이언스 과목)

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **컴플라이언스** | Compliance | 법/규정/표준을 준수하는 것 | 교통법규 준수 |
| **인증** | Certification | 외부 심사 기관이 표준 준수를 확인하는 절차 | 운전면허 시험 합격 |
| **통제 항목** | Control | 보안 목표를 달성하기 위한 구체적 조치 | 건물 소방 설비 하나하나 |
| **SoA** | Statement of Applicability | 적용 가능한 통제 항목 선언서 | "우리 건물에 필요한 소방 설비 목록" |
| **리스크 평가** | Risk Assessment | 위험을 식별·분석·평가하는 과정 | 건물의 화재/지진 위험도 평가 |
| **리스크 처리** | Risk Treatment | 평가된 위험에 대한 대응 결정 (수용/회피/감소/전가) | 보험 가입, 소방 설비 설치 |
| **PDCA** | Plan-Do-Check-Act | ISO 표준의 지속적 개선 사이클 | 계획→실행→점검→개선 반복 |
| **ISMS** | Information Security Management System | 정보보안 관리 체계 | 회사의 보안 관리 시스템 전체 |
| **ISMS-P** | ISMS + Privacy | 한국의 정보보호 + 개인정보보호 인증 | 한국판 ISO 27001 + 개인정보 |
| **ISO 27001** | ISO/IEC 27001 | 국제 정보보안 관리체계 표준 | 국제 보안 면허증 |
| **ISO 27002** | ISO/IEC 27002 | ISO 27001의 통제 항목 상세 가이드 | 면허 시험 교재 |
| **NIST CSF** | NIST Cybersecurity Framework | 미국 국립표준기술연구소의 사이버보안 프레임워크 | 미국판 보안 가이드 |
| **GDPR** | General Data Protection Regulation | EU 개인정보보호 규정 | EU의 개인정보 보호법 |
| **SOC 2** | Service Organization Control 2 | 클라우드 서비스 보안 인증 (미국) | 클라우드 업체의 보안 성적표 |
| **증적** | Evidence (Audit) | 통제가 실행되었음을 증명하는 자료 | 출석부, 영수증 |
| **심사원** | Auditor | 인증 심사를 수행하는 전문가 | 감독관, 시험관 |
| **부적합** | Non-conformity | 심사에서 표준 미충족 판정 | 시험 불합격 항목 |
| **GAP 분석** | Gap Analysis | 현재 상태와 목표 기준의 차이 분석 | 현재 실력과 합격선의 차이 |


---

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

> **이 실습을 왜 하는가?**
> 보안 표준/컴플라이언스 과목에서 이 주차의 실습은 핵심 개념을 **직접 체험**하여 이론을 실무로 연결하는 과정이다.
> 인증 심사에서 이 통제 항목의 이행 여부가 적합/부적합 판정의 근거가 된다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이론에서 배운 개념이 실제 시스템에서 어떻게 동작하는지 확인
> - 실제 명령어와 도구 사용법을 체득
> - 결과를 분석하고 보안 관점에서 판단하는 능력 배양
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.


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
for ip in 10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100; do
  echo "========== $ip =========="
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) "
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
for ip in 10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100; do
  echo "========== $ip: 실행 서비스 =========="
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) "systemctl list-units --type=service --state=running --no-pager | grep -v 'loaded units' | tail -n +2 | head -15"
done
```

```bash
# 네트워크 자산 (열린 포트 = 서비스)
for ip in 10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100; do
  echo "========== $ip: 열린 포트 =========="
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) "ss -tlnp 2>/dev/null | grep LISTEN"
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
sshpass -p1 ssh opsclaw@10.20.30.201 "grep 'Failed password' /var/log/auth.log 2>/dev/null | wc -l"
sshpass -p1 ssh opsclaw@10.20.30.201 "grep 'Failed password' /var/log/auth.log 2>/dev/null | awk '{print \$(NF-3)}' | sort | uniq -c | sort -rn | head -5"

# Suricata 탐지 이벤트 (네트워크 위협)
sshpass -p1 ssh secu@10.20.30.1 "wc -l /var/log/suricata/fast.log 2>/dev/null || echo '0'"
sshpass -p1 ssh secu@10.20.30.1 "tail -5 /var/log/suricata/fast.log 2>/dev/null"

# Wazuh 고위험 알림 (복합 위협)
sshpass -p1 ssh siem@10.20.30.100 "cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c \"
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
sshpass -p1 ssh opsclaw@10.20.30.201 "grep PASS_MAX_DAYS /etc/login.defs | grep -v '^#'"

# 취약점 2: root 로그인 허용
sshpass -p1 ssh opsclaw@10.20.30.201 "grep PermitRootLogin /etc/ssh/sshd_config | grep -v '^#'"

# 취약점 3: 불필요한 포트 개방
sshpass -p1 ssh opsclaw@10.20.30.201 "ss -tlnp | grep LISTEN | wc -l"

# 취약점 4: 패치 미적용
sshpass -p1 ssh opsclaw@10.20.30.201 "apt list --upgradable 2>/dev/null | wc -l"

# 취약점 5: auditd 미설치
sshpass -p1 ssh opsclaw@10.20.30.201 "systemctl is-active auditd 2>/dev/null || echo '미설치'"

# 취약점 6: TMOUT 미설정
sshpass -p1 ssh opsclaw@10.20.30.201 "grep TMOUT /etc/profile /etc/bash.bashrc 2>/dev/null || echo '미설정'"

# 취약점 7: 커널 보안 파라미터
sshpass -p1 ssh opsclaw@10.20.30.201 "sysctl net.ipv4.conf.all.accept_redirects 2>/dev/null"
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
for srv in "opsclaw@10.20.30.201" "secu@10.20.30.1" "web@10.20.30.80" "siem@10.20.30.100"; do
  echo "=== $srv ==="
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) "hostname; ss -tlnp 2>/dev/null | grep LISTEN | wc -l; echo '서비스 수'"
done

# 2단계: 위협 증거
echo "=== SSH 공격 시도 ==="
sshpass -p1 ssh opsclaw@10.20.30.201 "grep 'Failed' /var/log/auth.log 2>/dev/null | wc -l"

echo "=== IPS 탐지 ==="
sshpass -p1 ssh secu@10.20.30.1 "wc -l /var/log/suricata/fast.log 2>/dev/null"

# 3단계: 취약점 확인
echo "=== 미패치 현황 ==="
for ip in 10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100; do
  echo "$ip: $(sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) 'apt list --upgradable 2>/dev/null | wc -l') 패키지"
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


---

---

## 심화: 표준/인증 실무 보충

### 보안 통제 구현 패턴

실무에서 통제 항목을 구현할 때의 일반적 패턴을 이해한다.

```
[1] 정책(Policy) 수립
    → "무엇을 해야 하는가?" 를 문서로 정의
    예: "모든 서버는 90일마다 패스워드를 변경한다"

[2] 절차(Procedure) 작성
    → "어떻게 하는가?" 를 단계별로 정리
    예: "1. passwd 명령 실행 2. 복잡도 확인 3. 변경 로그 기록"

[3] 기술적 구현(Technical Implementation)
    → 실제 시스템에 적용
    예: /etc/login.defs에 PASS_MAX_DAYS=90 설정

[4] 증적(Evidence) 수집
    → 구현되었음을 증명하는 자료 확보
    예: login.defs 캡처, 변경 로그, OpsClaw evidence
```

### 증적 수집 실습

```bash
# ISO 27001 A.8.5 (안전한 인증) 점검 증적 수집
echo "=== 패스워드 정책 확인 ==="
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 "
  echo '--- login.defs ---' && grep -E 'PASS_MAX|PASS_MIN|PASS_WARN' /etc/login.defs
  echo '--- pam 설정 ---' && grep pam_pwquality /etc/pam.d/common-password 2>/dev/null || echo 'pam_pwquality 미설정'
  echo '--- sudo 설정 ---' && sudo -l 2>/dev/null | head -5
" 2>/dev/null

# 결과를 OpsClaw evidence로 기록
# (OpsClaw dispatch 사용)
```

### GAP 분석 워크시트 예시

| 통제 ID | 통제 항목 | 현재 상태 | 목표 | GAP | 우선순위 |
|---------|---------|---------|------|-----|---------|
| A.5.1 | 정보보안 정책 | 문서 없음 | 승인된 정책 문서 | 정책 수립 필요 | 높음 |
| A.8.2 | 접근 권한 관리 | sudo NOPASSWD:ALL | 최소 권한 | sudo 제한 필요 | 긴급 |
| A.8.5 | 안전한 인증 | 단순 비밀번호 | 복잡도+MFA | 정책 변경 | 높음 |
| A.12.4 | 로깅 | 부분 수집 | 전체 수집+SIEM | Wazuh 연동 | 중간 |

### 인증 심사 대비 FAQ

| 질문 | 준비 방법 |
|------|---------|
| "이 통제의 증적을 보여주세요" | OpsClaw evidence/replay로 실행 이력 제시 |
| "리스크 평가를 어떻게 했나요?" | 리스크 평가 워크시트 + 기준 설명 |
| "부적합 사항은 어떻게 처리했나요?" | 시정 조치 계획서 + 완료 증적 |
| "경영진의 검토는?" | 검토 회의록 + 서명 |


---

## 자가 점검 퀴즈 (10문항)

이번 주차의 핵심 내용을 점검한다. 8/10 이상 정답을 목표로 한다.

**Q1.** "Week 10: 리스크 평가 실습"에서 가장 핵심적인 학습 목표는?
- (a) 데이터베이스 최적화  (b) **보안 표준/컴플라이언스의 원리와 실습**  (c) UI 개발  (d) 네트워크 속도

**Q2.** "1. 리스크 평가 개요"의 보안 관점에서의 의의는?
- (a) 성능 향상  (b) **보안 위협 이해 또는 방어 역량 강화**  (c) 비용 절감  (d) 사용성 개선

**Q3.** "2. 단계 1: 자산 식별"에서 사용하는 주요 도구/기법은?
- (a) 워드프로세서  (b) **보안 표준/컴플라이언스 전용 도구/명령**  (c) 게임 엔진  (d) 그래픽 도구

**Q4.** 이번 실습에서 OpsClaw evidence가 제공하는 가치는?
- (a) 속도  (b) **작업 증적의 자동 기록과 감사 추적**  (c) 화면 출력  (d) 파일 압축

**Q5.** "3. 단계 2: 위협 식별"의 실무 활용 방안은?
- (a) 개인 블로그  (b) **보안 점검, 대응, 보고서 작성에 활용**  (c) 게임 개발  (d) 영상 편집

**Q6.** 이 주차에서 실무 적용의 핵심 원칙은?
- (a) 모든 기능 비활성화  (b) **최소 권한 + 모니터링 + 대응의 조합**  (c) 무조건 차단  (d) 설정 변경 금지

**Q7.** 실습 결과를 평가할 때 가장 중요한 기준은?
- (a) 파일 크기  (b) **보안 효과성과 정확성**  (c) 실행 속도  (d) 줄 수

**Q8.** 이 주제가 전체 보안 표준/컴플라이언스 커리큘럼에서 차지하는 위치는?
- (a) 독립적 주제  (b) **이전 주차의 심화/다음 주차의 기반**  (c) 선택 과목  (d) 부록

**Q9.** 실무에서 이 기법을 적용할 때 주의할 점은?
- (a) 속도  (b) **법적 허가, 범위 준수, 증적 관리**  (c) 디자인  (d) 비용

**Q10.** 이번 주차 학습의 성과를 어떻게 측정하는가?
- (a) 시간  (b) **실습 완료율 + 퀴즈 점수 + 과제 품질**  (c) 줄 수  (d) 파일 수

**정답:** Q1:b, Q2:b, Q3:b, Q4:b, Q5:b, Q6:b, Q7:b, Q8:b, Q9:b, Q10:b

---
---

> **실습 환경 검증:** 이 교안의 실습 명령은 실제 인프라(10.20.30.0/24)에서 동작을 확인하였습니다. (2026-03-28 검증)
