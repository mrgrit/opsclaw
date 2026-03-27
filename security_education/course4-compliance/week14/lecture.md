# Week 14: 인증 준비 실습 - SoA, 증적 수집, 심사 대응

## 학습 목표

- 적용성 보고서(SoA)를 작성할 수 있다
- 인증 심사를 위한 증적(Evidence)을 수집할 수 있다
- 심사원의 질문에 대한 답변을 준비할 수 있다
- 인증 심사의 전체 프로세스를 이해한다

---

## 1. 인증 준비 로드맵

### 1.1 전체 일정 (일반적인 ISO 27001 인증)

```
Phase 1: 준비 (2~3개월)
├── 범위 정의
├── 리스크 평가
├── 정책/절차 수립
└── SoA 작성

Phase 2: 구현 (3~6개월)
├── 통제 구현
├── 교육 실시
├── 운영 시작
└── 증적 축적

Phase 3: 검증 (1~2개월)
├── 내부 감사
├── 경영검토
├── 부적합 시정
└── 인증 신청

Phase 4: 심사 (2~4주)
├── Stage 1: 문서 심사
├── Stage 2: 현장 심사
├── 시정조치 (필요 시)
└── 인증서 발급
```

---

## 2. 적용성 보고서 (Statement of Applicability, SoA)

### 2.1 SoA란?

ISO 27001 인증에서 **가장 중요한 문서** 중 하나이다.
93개 Annex A 통제 항목 각각에 대해:
- 적용 여부
- 적용/미적용 사유
- 구현 상태
- 관련 문서/증적

### 2.2 실습: SoA 작성

다음 형식으로 우리 실습 환경의 SoA를 작성한다:

```
================================================================
적용성 보고서 (Statement of Applicability)
조직: OpsClaw 실습 환경
기준: ISO 27001:2022 Annex A
작성일: 2026-03-27
================================================================
```

#### A.5 조직적 통제

| 통제 | 항목명 | 적용 | 사유 | 구현상태 | 증적 |
|------|--------|------|------|---------|------|
| A.5.1 | 정보보안 정책 | 적용 | 보안 운영 필수 | 부분 | 보안정책서 |
| A.5.7 | 위협 인텔리전스 | 적용 | Wazuh/OpenCTI 운영 | 구현 | SIEM 설정 |
| A.5.9 | 자산 인벤토리 | 적용 | 자산 관리 필요 | 부분 | 자산목록 |
| A.5.15 | 접근통제 정책 | 적용 | 접근통제 필수 | 구현 | 정책서, SSH설정 |
| A.5.24 | 사고관리 계획 | 적용 | 사고 대응 필수 | 부분 | 대응절차서 |

#### A.6 인적 통제

| 통제 | 항목명 | 적용 | 사유 | 구현상태 | 증적 |
|------|--------|------|------|---------|------|
| A.6.3 | 보안 인식 교육 | 적용 | 필수 | 미구현 | - |
| A.6.5 | 퇴직 후 책임 | 미적용 | 실습 환경 | N/A | - |

#### A.7 물리적 통제

| 통제 | 항목명 | 적용 | 사유 | 구현상태 | 증적 |
|------|--------|------|------|---------|------|
| A.7.1 | 물리적 보안 경계 | 미적용 | 가상 환경 | N/A | - |
| A.7.8 | 장비 위치 및 보호 | 미적용 | 가상 환경 | N/A | - |

#### A.8 기술적 통제

| 통제 | 항목명 | 적용 | 사유 | 구현상태 | 증적 |
|------|--------|------|------|---------|------|
| A.8.1 | 사용자 단말 | 적용 | 서버 접근 관리 | 부분 | SSH 설정 |
| A.8.2 | 특수접근권한 | 적용 | sudo 관리 필수 | 구현 | sudoers 설정 |
| A.8.5 | 보안 인증 | 적용 | 인증 보안 | 부분 | sshd_config |
| A.8.7 | 악성코드 방지 | 적용 | 보호 필수 | 미구현 | - |
| A.8.9 | 설정 관리 | 적용 | 서버 관리 | 부분 | 설정파일 |
| A.8.15 | 로깅 | 적용 | 감사 필수 | 구현 | rsyslog, Wazuh |
| A.8.16 | 모니터링 활동 | 적용 | 상시 감시 | 구현 | Wazuh Dashboard |
| A.8.20 | 네트워크 보안 | 적용 | 경계 보호 | 구현 | nftables 설정 |
| A.8.24 | 암호화 사용 | 적용 | 데이터 보호 | 부분 | TLS 설정 |
| A.8.28 | 보안 코딩 | 적용 | 개발 보안 | 부분 | 코드 리뷰 |

---

## 3. 증적 수집 (Evidence Collection)

### 3.1 증적 유형

| 유형 | 예시 |
|------|------|
| 문서 | 정책서, 절차서, 가이드라인 |
| 기록 | 로그, 감사 이력, 회의록 |
| 설정 | 서버 설정 파일, 방화벽 규칙 |
| 스크린샷 | 대시보드 화면, 설정 화면 |
| 인터뷰 | 담당자 면담 기록 |

### 3.2 실습: 증적 수집 스크립트

```bash
#!/bin/bash
# 인증 심사용 증적 수집 스크립트
EVIDENCE_DIR="/tmp/audit_evidence_$(date +%Y%m%d)"
mkdir -p "$EVIDENCE_DIR"

echo "증적 수집 시작: $(date)"
echo "저장 위치: $EVIDENCE_DIR"

# 1. 서버 인벤토리 (A.5.9)
echo "=== [A.5.9] 자산 인벤토리 수집 ==="
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  sshpass -p1 ssh user@$ip "
    echo '=== 서버 정보 ==='
    hostname
    uname -a
    cat /etc/os-release | grep PRETTY_NAME
    echo '=== 하드웨어 ==='
    lscpu | grep 'Model name'
    free -h | grep Mem
    df -h /
    echo '=== 서비스 ==='
    systemctl list-units --type=service --state=running --no-pager
  " 2>/dev/null > "$EVIDENCE_DIR/inventory_${ip}.txt"
done

# 2. SSH 설정 (A.8.5)
echo "=== [A.8.5] SSH 설정 수집 ==="
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  sshpass -p1 ssh user@$ip "cat /etc/ssh/sshd_config" 2>/dev/null > "$EVIDENCE_DIR/sshd_config_${ip}.txt"
done

# 3. 사용자 계정 (A.8.2)
echo "=== [A.8.2] 계정 정보 수집 ==="
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  sshpass -p1 ssh user@$ip "
    echo '=== 사용자 목록 ==='
    cat /etc/passwd
    echo '=== 그룹 ==='
    cat /etc/group
    echo '=== sudo 그룹 ==='
    getent group sudo
    echo '=== 최근 로그인 ==='
    lastlog
  " 2>/dev/null > "$EVIDENCE_DIR/accounts_${ip}.txt"
done

# 4. 방화벽 규칙 (A.8.20)
echo "=== [A.8.20] 방화벽 규칙 수집 ==="
sshpass -p1 ssh user@192.168.208.150 "sudo nft list ruleset" 2>/dev/null > "$EVIDENCE_DIR/firewall_rules.txt"

# 5. 비밀번호 정책 (A.8.5)
echo "=== [A.8.5] 비밀번호 정책 수집 ==="
sshpass -p1 ssh user@192.168.208.142 "
  echo '=== login.defs ==='
  grep -E 'PASS_MAX_DAYS|PASS_MIN_DAYS|PASS_MIN_LEN|PASS_WARN_AGE' /etc/login.defs
  echo '=== pwquality ==='
  cat /etc/security/pwquality.conf 2>/dev/null
" 2>/dev/null > "$EVIDENCE_DIR/password_policy.txt"

# 6. 로그 샘플 (A.8.15)
echo "=== [A.8.15] 로그 샘플 수집 ==="
sshpass -p1 ssh user@192.168.208.142 "tail -100 /var/log/auth.log" 2>/dev/null > "$EVIDENCE_DIR/auth_log_sample.txt"
sshpass -p1 ssh user@192.168.208.152 "tail -50 /var/ossec/logs/alerts/alerts.json" 2>/dev/null > "$EVIDENCE_DIR/wazuh_alerts_sample.txt"

# 7. NTP 설정 (A.8.17)
echo "=== [A.8.17] NTP 설정 수집 ==="
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  sshpass -p1 ssh user@$ip "timedatectl" 2>/dev/null > "$EVIDENCE_DIR/ntp_${ip}.txt"
done

# 8. 패치 현황 (A.8.8)
echo "=== [A.8.8] 패치 현황 수집 ==="
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  sshpass -p1 ssh user@$ip "apt list --upgradable 2>/dev/null" > "$EVIDENCE_DIR/patches_${ip}.txt"
done

echo ""
echo "수집 완료! 파일 목록:"
ls -la "$EVIDENCE_DIR/"
echo ""
echo "총 파일 수: $(ls $EVIDENCE_DIR | wc -l)"
```

### 3.3 증적 무결성 보장

```bash
# 수집한 증적 파일의 해시값 생성 (무결성 증명)
EVIDENCE_DIR="/tmp/audit_evidence_$(date +%Y%m%d)"
cd "$EVIDENCE_DIR" 2>/dev/null && sha256sum *.txt > checksums.sha256
cat checksums.sha256
```

---

## 4. 심사 대응 준비

### 4.1 심사원이 자주 묻는 질문

| 질문 | 준비할 답변 |
|------|------------|
| "정보보안 정책은 어디에 있습니까?" | 정책 문서 위치, 최근 검토일 |
| "리스크 평가는 언제 수행했습니까?" | 리스크 평가 보고서, 날짜 |
| "비인가 접근 시 어떻게 탐지합니까?" | Wazuh SIEM 운영, 알림 체계 |
| "접근 권한은 어떻게 관리합니까?" | 계정 관리 절차, sudo 정책 |
| "사고 발생 시 대응 절차는?" | 사고대응 절차서, 대응팀 연락처 |
| "로그는 얼마나 보관합니까?" | logrotate 설정, 6개월 이상 |
| "패치 관리는 어떻게 합니까?" | 패치 주기, 최근 적용 이력 |
| "변경 관리 절차가 있습니까?" | 변경 요청/승인/테스트/적용 절차 |

### 4.2 실습: 심사 시뮬레이션

심사원 역할과 피심사자 역할을 나누어 연습한다.

**시나리오 1: 접근통제 심사**
```
심사원: "서버에 대한 접근 통제를 어떻게 하고 있습니까?"

피심사자: (다음을 보여준다)
```

```bash
# SSH 접근 제한 설정 시연
sshpass -p1 ssh user@192.168.208.142 "grep -E 'PermitRootLogin|PasswordAuthentication|MaxAuthTries' /etc/ssh/sshd_config | grep -v '^#'"

# 방화벽에서 SSH 접근 제한
sshpass -p1 ssh user@192.168.208.150 "sudo nft list ruleset 2>/dev/null | grep -A2 'ssh\|22'"

# 계정 권한 현황
sshpass -p1 ssh user@192.168.208.142 "getent group sudo"
```

**시나리오 2: 모니터링 심사**
```
심사원: "보안 이벤트를 어떻게 모니터링합니까?"
```

```bash
# Wazuh SIEM 운영 현황
sshpass -p1 ssh user@192.168.208.152 "systemctl status wazuh-manager 2>/dev/null | head -5"

# 에이전트 연결 현황
sshpass -p1 ssh user@192.168.208.152 "/var/ossec/bin/agent_control -l 2>/dev/null | head -10"

# 최근 알림 확인
sshpass -p1 ssh user@192.168.208.152 "cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | tail -3 | python3 -m json.tool 2>/dev/null | head -20"
```

**시나리오 3: 사고대응 심사**
```
심사원: "지난 6개월간 보안 사고가 있었습니까? 대응 기록을 보여주십시오."
```

```bash
# 고위험 알림 이력
sshpass -p1 ssh user@192.168.208.152 "cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c \"
import sys, json
for line in sys.stdin:
    try:
        a = json.loads(line)
        r = a.get('rule',{})
        if r.get('level',0) >= 12:
            ts = a.get('timestamp','')
            print(f'  {ts} [Level {r[\"level\"]}] {r.get(\"description\",\"\")}')
    except: pass
\" 2>/dev/null | tail -10"
```

---

## 5. 부적합 시정 조치

### 5.1 부적합 유형

| 유형 | 설명 | 대응 기한 |
|------|------|----------|
| 중대 부적합 (Major) | 통제 항목 전체가 미구현 | 90일 이내 시정 |
| 경미 부적합 (Minor) | 부분적으로 미흡 | 다음 사후심사까지 |
| 관찰 사항 (OFI) | 개선이 바람직한 사항 | 권고 (의무 아님) |

### 5.2 시정 조치 보고서 양식

```
시정조치 보고서
- 부적합 번호: NC-001
- 관련 통제: A.8.15 로깅
- 부적합 내용: auditd가 미설치되어 명령 수준 감사 로그가 없음
- 근본 원인: 초기 서버 구축 시 auditd 설치가 누락됨
- 시정 조치: auditd 패키지 설치 및 감사 규칙 설정
- 예방 조치: 서버 구축 체크리스트에 auditd 포함
- 증적: 설치 로그, 설정 파일, auditd 상태 캡처
- 완료일: 2026-04-XX
```

---

## 6. 핵심 정리

1. **SoA** = 93개 통제 항목별 적용 여부와 사유를 문서화
2. **증적 수집** = 문서, 설정, 로그, 스크린샷을 체계적으로 수집
3. **무결성** = 증적의 해시값을 기록하여 변조 방지
4. **심사 대응** = 질문에 즉시 증적을 보여줄 수 있도록 준비
5. **시정 조치** = 부적합 발견 시 근본원인 분석 + 예방조치까지

---

## 과제

1. 실습 환경에 대한 SoA를 A.8 기술적 통제 34개 항목 전체에 대해 작성하시오
2. 증적 수집 스크립트를 실행하고 결과를 정리하시오
3. 심사 시뮬레이션 시나리오 2개를 추가로 작성하고 답변을 준비하시오

---

## 참고 자료

- ISO 27001 Certification Process Guide
- ISO 27001 SoA Template
- KISA ISMS-P 인증심사 가이드
