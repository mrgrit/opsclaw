# Week 12: 보안 감사 실습 (상세 버전)

## 학습 목표
- 보안 감사의 유형과 절차를 이해한다
- 로그 감사(Log Audit)를 수행할 수 있다
- 설정 검토(Configuration Review)를 수행할 수 있다
- 갭 분석(Gap Analysis)을 통해 미준수 항목을 도출할 수 있다


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

# Week 12: 보안 감사 실습

## 학습 목표

- 보안 감사의 유형과 절차를 이해한다
- 로그 감사(Log Audit)를 수행할 수 있다
- 설정 검토(Configuration Review)를 수행할 수 있다
- 갭 분석(Gap Analysis)을 통해 미준수 항목을 도출할 수 있다

---

## 1. 보안 감사 개요

### 1.1 감사 유형

| 유형 | 설명 | 주체 |
|------|------|------|
| 내부 감사 | 조직 내부에서 자체 수행 | 내부 감사팀 |
| 외부 감사 | 제3자 기관이 수행 | 인증기관, 회계법인 |
| 기술 감사 | 시스템 설정/취약점 점검 | 보안 컨설턴트 |
| 프로세스 감사 | 절차/정책 준수 확인 | 감사팀 |

### 1.2 감사 절차

```
1. 감사 계획 수립 (범위, 기준, 일정)
2. 자료 수집 (문서, 로그, 설정, 인터뷰)
3. 분석 및 평가 (기준 대비 현황 비교)
4. 발견사항 도출 (부적합, 관찰사항, 개선권고)
5. 보고서 작성
6. 시정조치 확인
```

---

## 2. 로그 감사 (Log Audit)

### 2.1 감사해야 할 로그

| 로그 | 위치 | 감사 목적 |
|------|------|----------|
| auth.log | /var/log/auth.log | 인증 시도, sudo 사용 |
| syslog | /var/log/syslog | 시스템 이벤트 |
| Suricata | /var/log/suricata/ | 네트워크 공격 탐지 |
| Wazuh | /var/ossec/logs/ | 보안 알림 통합 |
| 웹 로그 | /var/log/nginx/ | 웹 접근, 공격 시도 |

### 2.2 실습: 인증 로그 감사

```bash
# 1. SSH 로그인 성공/실패 통계
echo "=== SSH 로그인 감사 ==="
for ip in 10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100; do
  echo "--- $ip ---"
  echo -n "성공: "
  sshpass -p1 ssh user@$ip "grep 'Accepted' /var/log/auth.log 2>/dev/null | wc -l"
  echo -n "실패: "
  sshpass -p1 ssh user@$ip "grep 'Failed password' /var/log/auth.log 2>/dev/null | wc -l"
done
```

```bash
# 2. 실패한 로그인의 출발지 IP 분석
sshpass -p1 ssh opsclaw@10.20.30.201 "grep 'Failed password' /var/log/auth.log 2>/dev/null | \
  awk '{print \$(NF-3)}' | sort | uniq -c | sort -rn | head -10"
```

```bash
# 3. sudo 사용 감사
for ip in 10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100; do
  echo "=== $ip: sudo 사용 이력 ==="
  sshpass -p1 ssh user@$ip "grep 'sudo:' /var/log/auth.log 2>/dev/null | tail -5"
done
```

```bash
# 4. 비정상 시간대 로그인 확인 (새벽 2~5시)
sshpass -p1 ssh opsclaw@10.20.30.201 "grep 'session opened' /var/log/auth.log 2>/dev/null | \
  awk '{print \$3}' | awk -F: '\$1>=2 && \$1<=5 {print}'"
```

### 2.3 실습: 네트워크 로그 감사

```bash
# Suricata 알림 분석
echo "=== Suricata 알림 통계 ==="
sshpass -p1 ssh secu@10.20.30.1 "cat /var/log/suricata/fast.log 2>/dev/null | \
  awk -F'\\]' '{print \$2}' | sort | uniq -c | sort -rn | head -10"

# Suricata 알림 심각도별 분류
sshpass -p1 ssh secu@10.20.30.1 "cat /var/log/suricata/fast.log 2>/dev/null | \
  grep -oE 'Priority: [0-9]+' | sort | uniq -c | sort -rn"
```

### 2.4 실습: Wazuh 알림 감사

```bash
# Wazuh 알림 레벨별 통계
sshpass -p1 ssh siem@10.20.30.100 "cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c \"
import sys, json
from collections import Counter
levels = Counter()
rules = Counter()
for line in sys.stdin:
    try:
        a = json.loads(line)
        r = a.get('rule', {})
        levels[r.get('level', 0)] += 1
        if r.get('level', 0) >= 8:
            rules[r.get('description', 'unknown')] += 1
    except: pass
print('=== 레벨별 통계 ===')
for l in sorted(levels.keys(), reverse=True):
    print(f'  Level {l}: {levels[l]}건')
print()
print('=== 고위험 알림 Top 5 ===')
for desc, cnt in rules.most_common(5):
    print(f'  {cnt}건: {desc}')
\" 2>/dev/null"
```

---

## 3. 설정 검토 (Configuration Review)

### 3.1 점검 스크립트

```bash
#!/bin/bash
# 보안 설정 감사 스크립트
echo "================================================"
echo " 보안 설정 감사 보고서 - $(date '+%Y-%m-%d %H:%M')"
echo "================================================"

SERVERS="10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100"

for ip in $SERVERS; do
  echo ""
  echo "############## $ip ##############"

  # 1. SSH 설정
  echo "[SSH 설정]"
  sshpass -p1 ssh user@$ip "
    echo -n '  PermitRootLogin: '; grep '^PermitRootLogin' /etc/ssh/sshd_config 2>/dev/null || echo '기본값'
    echo -n '  PasswordAuth: '; grep '^PasswordAuthentication' /etc/ssh/sshd_config 2>/dev/null || echo '기본값'
    echo -n '  MaxAuthTries: '; grep '^MaxAuthTries' /etc/ssh/sshd_config 2>/dev/null || echo '기본값(6)'
    echo -n '  Protocol: '; ssh -V 2>&1
  " 2>/dev/null

  # 2. 비밀번호 정책
  echo "[비밀번호 정책]"
  sshpass -p1 ssh user@$ip "
    grep -E '^PASS_MAX_DAYS|^PASS_MIN_DAYS|^PASS_MIN_LEN' /etc/login.defs 2>/dev/null | sed 's/^/  /'
  " 2>/dev/null

  # 3. 파일 권한
  echo "[중요 파일 권한]"
  sshpass -p1 ssh user@$ip "
    stat -c '  %a %n' /etc/passwd /etc/shadow /etc/ssh/sshd_config 2>/dev/null
  " 2>/dev/null

  # 4. 네트워크 서비스
  echo "[열린 포트]"
  sshpass -p1 ssh user@$ip "ss -tlnp 2>/dev/null | grep LISTEN | awk '{print \"  \" \$4}'" 2>/dev/null

  # 5. 커널 보안
  echo "[커널 보안 파라미터]"
  sshpass -p1 ssh user@$ip "
    echo -n '  ip_forward: '; sysctl -n net.ipv4.ip_forward 2>/dev/null
    echo -n '  accept_redirects: '; sysctl -n net.ipv4.conf.all.accept_redirects 2>/dev/null
    echo -n '  accept_source_route: '; sysctl -n net.ipv4.conf.all.accept_source_route 2>/dev/null
  " 2>/dev/null
done
```

### 3.2 CIS Benchmark 기준 점검

CIS(Center for Internet Security)는 각 OS별 보안 설정 가이드를 제공한다.

```bash
# CIS 권장 사항 일부 점검
ip=10.20.30.201

echo "=== CIS Benchmark 일부 점검 ==="

echo "[1.1] 별도 /tmp 파티션:"
sshpass -p1 ssh user@$ip "mount | grep ' /tmp ' || echo '  별도 파티션 아님'"

echo "[1.4] ASLR 활성화:"
sshpass -p1 ssh user@$ip "sysctl kernel.randomize_va_space 2>/dev/null"

echo "[2.1] inetd/xinetd 서비스:"
sshpass -p1 ssh user@$ip "systemctl is-active inetd xinetd 2>/dev/null || echo '  미설치 (양호)'"

echo "[3.1] IP 포워딩 비활성화:"
sshpass -p1 ssh user@$ip "sysctl net.ipv4.ip_forward 2>/dev/null"

echo "[4.1] auditd 활성화:"
sshpass -p1 ssh user@$ip "systemctl is-active auditd 2>/dev/null || echo '  미활성'"

echo "[5.1] cron 접근 제한:"
sshpass -p1 ssh user@$ip "ls -la /etc/cron.allow /etc/cron.deny 2>/dev/null || echo '  설정 없음'"

echo "[5.2] SSH 설정:"
sshpass -p1 ssh user@$ip "stat -c '%a' /etc/ssh/sshd_config 2>/dev/null | xargs -I{} echo '  sshd_config 권한: {}'"

echo "[6.1] 파일 무결성 도구:"
sshpass -p1 ssh user@$ip "which aide tripwire 2>/dev/null || echo '  무결성 도구 미설치'"
```

---

## 4. 갭 분석 (Gap Analysis)

### 4.1 갭 분석이란?

현재 상태(As-Is)와 목표 상태(To-Be)의 차이를 분석하는 것이다.

```
[현재 상태] ←--- GAP ---→ [목표 상태 (ISO 27001/ISMS-P 기준)]
```

### 4.2 실습: 갭 분석 수행

```bash
# 갭 분석 자동화 스크립트
echo "========================================="
echo " 갭 분석 결과 - ISO 27001 기반"
echo "========================================="

ip=10.20.30.201

# A.8.2 특수접근권한
echo ""
echo "[A.8.2] 특수접근권한 관리"
echo "  기준: PermitRootLogin no"
result=$(sshpass -p1 ssh user@$ip "grep '^PermitRootLogin' /etc/ssh/sshd_config 2>/dev/null" || echo "미설정")
echo "  현황: $result"
if echo "$result" | grep -q "no"; then
  echo "  판정: 적합"
else
  echo "  판정: 부적합 (GAP)"
  echo "  조치: /etc/ssh/sshd_config에 PermitRootLogin no 설정"
fi

# A.8.5 보안인증
echo ""
echo "[A.8.5] 보안인증 - 비밀번호 최대 사용일"
echo "  기준: PASS_MAX_DAYS <= 90"
result=$(sshpass -p1 ssh user@$ip "grep '^PASS_MAX_DAYS' /etc/login.defs 2>/dev/null | awk '{print \$2}'")
echo "  현황: PASS_MAX_DAYS = $result"
if [ -n "$result" ] && [ "$result" -le 90 ] 2>/dev/null; then
  echo "  판정: 적합"
else
  echo "  판정: 부적합 (GAP)"
  echo "  조치: /etc/login.defs에서 PASS_MAX_DAYS 90으로 변경"
fi

# A.8.15 로깅
echo ""
echo "[A.8.15] 로깅 - auditd"
echo "  기준: auditd 활성화"
result=$(sshpass -p1 ssh user@$ip "systemctl is-active auditd 2>/dev/null" || echo "inactive")
echo "  현황: $result"
if [ "$result" = "active" ]; then
  echo "  판정: 적합"
else
  echo "  판정: 부적합 (GAP)"
  echo "  조치: apt install auditd && systemctl enable auditd"
fi

# A.8.20 네트워크보안
echo ""
echo "[A.8.20] 네트워크보안 - 방화벽 기본정책"
echo "  기준: 기본 정책 DROP"
result=$(sshpass -p1 ssh secu@10.20.30.1 "sudo nft list ruleset 2>/dev/null | grep 'policy drop'" || echo "")
if [ -n "$result" ]; then
  echo "  현황: 기본 정책 DROP"
  echo "  판정: 적합"
else
  echo "  현황: 기본 정책 DROP 아님 또는 확인 불가"
  echo "  판정: 확인 필요"
fi
```

### 4.3 갭 분석 결과 요약 템플릿

```
| No | 통제항목 | 기준 | 현황 | 갭 여부 | 우선순위 | 조치 방안 | 담당 | 완료예정 |
|----|---------|------|------|---------|---------|----------|------|---------|
| 1 | A.8.2 | root 로그인 차단 | 허용 상태 | GAP | 높음 | sshd_config 수정 | 시스템팀 | 1주 |
| 2 | A.8.5 | 비밀번호 90일 | 99999일 | GAP | 높음 | login.defs 수정 | 시스템팀 | 1주 |
| 3 | A.8.15 | auditd 활성화 | 미설치 | GAP | 중간 | 패키지 설치 | 보안팀 | 2주 |
| ... | ... | ... | ... | ... | ... | ... | ... | ... |
```

---

## 5. 감사 보고서 작성

### 5.1 보고서 구조

```
========================================
보안 감사 보고서
========================================

1. 감사 개요
   - 감사 기간: 2026-XX-XX ~ 2026-XX-XX
   - 감사 범위: 서버 4대 (opsclaw, secu, web, siem)
   - 감사 기준: ISO 27001:2022, ISMS-P
   - 감사팀: (이름)

2. 감사 결과 요약
   - 점검 항목: 20개
   - 적합: X개
   - 부적합: X개
   - 관찰사항: X개

3. 상세 발견사항
   3.1 부적합 사항
       (각 항목별 상세)
   3.2 관찰 사항
       (개선 권고)

4. 갭 분석 결과

5. 권고사항
   - 즉시 조치 항목
   - 단기 개선 항목
   - 중장기 개선 항목

6. 결론
```

---

## 6. 핵심 정리

1. **보안 감사** = 로그 감사 + 설정 검토 + 갭 분석
2. **로그 감사** = 인증, 네트워크, SIEM 로그 분석
3. **설정 검토** = CIS Benchmark 등 기준 대비 점검
4. **갭 분석** = 현재 상태와 목표 상태의 차이 도출
5. **보고서** = 발견사항, 갭 분석, 권고사항을 체계적으로 문서화

---

## 과제

1. 4개 서버에 대해 로그 감사를 수행하고 이상 징후를 3가지 이상 보고하시오
2. CIS Benchmark 기준 10개 항목 이상 설정 검토를 수행하시오
3. 갭 분석 결과를 표로 작성하고 우선순위별 개선 계획을 수립하시오

---

## 참고 자료

- CIS Benchmarks (https://www.cisecurity.org/cis-benchmarks)
- ISO 27001:2022 내부 감사 가이드
- KISA 보안 감사 체크리스트


---


---

## 자가 점검 퀴즈 (10문항)

이번 주차의 핵심 내용을 점검한다. 8/10 이상 정답을 목표로 한다.

**Q1.** "Week 12: 보안 감사 실습"에서 가장 핵심적인 학습 목표는?
- (a) 데이터베이스 최적화  (b) **보안 표준/컴플라이언스의 원리와 실습**  (c) UI 개발  (d) 네트워크 속도

**Q2.** "1. 보안 감사 개요"의 보안 관점에서의 의의는?
- (a) 성능 향상  (b) **보안 위협 이해 또는 방어 역량 강화**  (c) 비용 절감  (d) 사용성 개선

**Q3.** "2. 로그 감사 (Log Audit)"에서 사용하는 주요 도구/기법은?
- (a) 워드프로세서  (b) **보안 표준/컴플라이언스 전용 도구/명령**  (c) 게임 엔진  (d) 그래픽 도구

**Q4.** 이번 실습에서 OpsClaw evidence가 제공하는 가치는?
- (a) 속도  (b) **작업 증적의 자동 기록과 감사 추적**  (c) 화면 출력  (d) 파일 압축

**Q5.** "3. 설정 검토 (Configuration Review)"의 실무 활용 방안은?
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
