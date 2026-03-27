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
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "--- $ip ---"
  echo -n "성공: "
  sshpass -p1 ssh user@$ip "grep 'Accepted' /var/log/auth.log 2>/dev/null | wc -l"
  echo -n "실패: "
  sshpass -p1 ssh user@$ip "grep 'Failed password' /var/log/auth.log 2>/dev/null | wc -l"
done
```

```bash
# 2. 실패한 로그인의 출발지 IP 분석
sshpass -p1 ssh user@192.168.208.142 "grep 'Failed password' /var/log/auth.log 2>/dev/null | \
  awk '{print \$(NF-3)}' | sort | uniq -c | sort -rn | head -10"
```

```bash
# 3. sudo 사용 감사
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "=== $ip: sudo 사용 이력 ==="
  sshpass -p1 ssh user@$ip "grep 'sudo:' /var/log/auth.log 2>/dev/null | tail -5"
done
```

```bash
# 4. 비정상 시간대 로그인 확인 (새벽 2~5시)
sshpass -p1 ssh user@192.168.208.142 "grep 'session opened' /var/log/auth.log 2>/dev/null | \
  awk '{print \$3}' | awk -F: '\$1>=2 && \$1<=5 {print}'"
```

### 2.3 실습: 네트워크 로그 감사

```bash
# Suricata 알림 분석
echo "=== Suricata 알림 통계 ==="
sshpass -p1 ssh user@192.168.208.150 "cat /var/log/suricata/fast.log 2>/dev/null | \
  awk -F'\\]' '{print \$2}' | sort | uniq -c | sort -rn | head -10"

# Suricata 알림 심각도별 분류
sshpass -p1 ssh user@192.168.208.150 "cat /var/log/suricata/fast.log 2>/dev/null | \
  grep -oE 'Priority: [0-9]+' | sort | uniq -c | sort -rn"
```

### 2.4 실습: Wazuh 알림 감사

```bash
# Wazuh 알림 레벨별 통계
sshpass -p1 ssh user@192.168.208.152 "cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c \"
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

SERVERS="192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152"

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
ip=192.168.208.142

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

ip=192.168.208.142

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
result=$(sshpass -p1 ssh user@192.168.208.150 "sudo nft list ruleset 2>/dev/null | grep 'policy drop'" || echo "")
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
