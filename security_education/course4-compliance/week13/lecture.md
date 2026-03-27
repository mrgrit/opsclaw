# Week 13: 미국 표준 - SOC 2, HIPAA

## 학습 목표

- SOC 2 인증의 Trust Service Criteria를 이해한다
- HIPAA의 의료 데이터 보호 요구사항을 이해한다
- 글로벌 컴플라이언스의 공통점과 차이점을 파악한다
- 실습 환경에서 SOC 2/HIPAA 기준의 점검을 수행한다

---

## 1. SOC 2 (Service Organization Control 2)

### 1.1 SOC 보고서 유형

| 유형 | 대상 | 내용 |
|------|------|------|
| SOC 1 | 재무 보고 관련 | 내부 통제 (ICFR) |
| SOC 2 | IT 서비스 | 보안, 가용성, 처리 무결성, 기밀성, 프라이버시 |
| SOC 3 | 일반 공개 | SOC 2의 요약본 |

- **SOC 2 Type I**: 특정 시점의 통제 설계 적합성
- **SOC 2 Type II**: 일정 기간(보통 6~12개월) 동안의 통제 운영 효과성

### 1.2 SOC 2를 받는 이유

- SaaS, 클라우드 서비스 기업에서 **사실상 필수**
- B2B 계약에서 고객이 SOC 2 보고서를 요구
- AWS, Google Cloud, Salesforce 등 모두 SOC 2 보유

---

## 2. Trust Service Criteria (TSC) 5가지

### 2.1 개요

| TSC | 기준 | 핵심 |
|-----|------|------|
| Security (보안) | 공통 기준, 필수 | 비인가 접근으로부터 보호 |
| Availability (가용성) | 선택 | 약정된 수준의 서비스 가용성 |
| Processing Integrity (처리 무결성) | 선택 | 정확하고 완전한 데이터 처리 |
| Confidentiality (기밀성) | 선택 | 기밀 정보 보호 |
| Privacy (프라이버시) | 선택 | 개인정보 수집/이용/보관/파기 |

> Security는 **필수**이고, 나머지 4개는 서비스 성격에 따라 선택한다.

### 2.2 Security TSC 주요 항목

| 항목 | 내용 | 실습 환경 점검 |
|------|------|---------------|
| CC1 | 통제 환경 (조직, 역할) | 관리자 역할 분리 |
| CC2 | 커뮤니케이션 (정책 공유) | 보안 정책 문서 존재 |
| CC3 | 리스크 평가 | 리스크 매트릭스 |
| CC4 | 모니터링 | Wazuh, Suricata |
| CC5 | 통제 활동 | 접근통제, 암호화 |
| CC6 | 논리적/물리적 접근 통제 | SSH, 방화벽, 계정관리 |
| CC7 | 시스템 운영 | 변경관리, 패치 |
| CC8 | 변경 관리 | 설정 변경 이력 |
| CC9 | 리스크 완화 | 사고 대응 절차 |

### 2.3 실습: CC6 (접근 통제) 점검

```bash
# CC6.1: 논리적 접근 보안 소프트웨어
echo "=== 방화벽 ==="
sshpass -p1 ssh user@192.168.208.150 "sudo nft list ruleset 2>/dev/null | head -10"

echo "=== IPS ==="
sshpass -p1 ssh user@192.168.208.150 "systemctl is-active suricata 2>/dev/null"

# CC6.2: 사용자 인증
echo "=== 인증 방식 ==="
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "--- $ip ---"
  sshpass -p1 ssh user@$ip "grep -E 'PasswordAuthentication|PubkeyAuthentication' /etc/ssh/sshd_config | grep -v '^#'"
done

# CC6.3: 접근 권한 부여/변경/제거
echo "=== 권한 관리 ==="
sshpass -p1 ssh user@192.168.208.142 "getent group sudo"
sshpass -p1 ssh user@192.168.208.142 "lastlog 2>/dev/null | head -10"

# CC6.6: 외부 위협으로부터 보호
echo "=== 보안 시스템 ==="
sshpass -p1 ssh user@192.168.208.150 "systemctl is-active suricata nftables 2>/dev/null"
sshpass -p1 ssh user@192.168.208.151 "docker ps 2>/dev/null | grep bunkerweb || systemctl is-active bunkerweb 2>/dev/null"
```

### 2.4 실습: CC7 (시스템 운영) 점검

```bash
# CC7.1: 이상 징후 탐지
echo "=== Wazuh 알림 현황 ==="
sshpass -p1 ssh user@192.168.208.152 "systemctl is-active wazuh-manager 2>/dev/null"
sshpass -p1 ssh user@192.168.208.152 "wc -l /var/ossec/logs/alerts/alerts.json 2>/dev/null"

# CC7.2: 보안 사고 모니터링
echo "=== 최근 고위험 알림 ==="
sshpass -p1 ssh user@192.168.208.152 "cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c \"
import sys, json
for line in sys.stdin:
    try:
        a = json.loads(line)
        r = a.get('rule',{})
        if r.get('level',0) >= 10:
            print(f'  [{r[\"level\"]}] {r.get(\"description\",\"\")}')
    except: pass
\" 2>/dev/null | tail -5"

# CC7.3: 변경 관리
echo "=== 최근 패키지 변경 ==="
sshpass -p1 ssh user@192.168.208.142 "tail -5 /var/log/dpkg.log 2>/dev/null"
```

---

## 3. HIPAA (Health Insurance Portability and Accountability Act)

### 3.1 개요

- **미국 의료정보 보호법** (1996년 제정)
- PHI (Protected Health Information, 보호대상 건강정보) 보호
- 의료기관, 보험사, 의료 IT 서비스 기업에 적용

### 3.2 HIPAA 구성

| 규칙 | 내용 |
|------|------|
| Privacy Rule | PHI의 사용/공개 규제 |
| Security Rule | 전자 PHI(ePHI)의 기술적/관리적/물리적 보호 |
| Breach Notification Rule | 유출 시 통지 의무 |
| Enforcement Rule | 위반 시 제재 |

### 3.3 Security Rule 세부

| 보호 유형 | 항목 | 예시 |
|-----------|------|------|
| 관리적 | 리스크 분석 | 정기적 위험 평가 수행 |
| 관리적 | 인력 보안 | 직원 접근 권한 관리 |
| 관리적 | 보안 교육 | 연 1회 이상 |
| 물리적 | 시설 접근 통제 | 서버실 출입 관리 |
| 물리적 | 워크스테이션 보안 | 화면 잠금 |
| 기술적 | 접근 통제 | 고유 사용자 ID |
| 기술적 | 감사 통제 | 접근 로그 기록 |
| 기술적 | 무결성 통제 | 데이터 변조 방지 |
| 기술적 | 전송 보안 | 암호화 |

### 3.4 실습: HIPAA 기술적 보호조치 점검

```bash
# 기술적 보호조치: 접근통제 (164.312(a))
echo "=== 고유 사용자 ID ==="
sshpass -p1 ssh user@192.168.208.142 "awk -F: '\$3>=1000 && \$3<65534 {print \$1, \$3}' /etc/passwd"

echo "=== 자동 로그오프 ==="
sshpass -p1 ssh user@192.168.208.142 "grep TMOUT /etc/profile /etc/bash.bashrc 2>/dev/null || echo '미설정 (HIPAA 부적합)'"

echo "=== 접근 실패 잠금 ==="
sshpass -p1 ssh user@192.168.208.142 "grep pam_faillock /etc/pam.d/common-auth 2>/dev/null || echo '미설정'"

# 기술적 보호조치: 감사통제 (164.312(b))
echo "=== 감사 로그 ==="
sshpass -p1 ssh user@192.168.208.142 "systemctl is-active auditd rsyslog 2>/dev/null"
sshpass -p1 ssh user@192.168.208.142 "ls -lh /var/log/auth.log 2>/dev/null"

# 기술적 보호조치: 전송보안 (164.312(e))
echo "=== 전송 암호화 ==="
sshpass -p1 ssh user@192.168.208.152 "echo | openssl s_client -connect localhost:443 2>/dev/null | grep Protocol"
```

### 3.5 HIPAA 위반 제재

| 위반 유형 | 과징금 (건당) |
|-----------|-------------|
| 모르고 위반 | $100~$50,000 |
| 합리적 사유 | $1,000~$50,000 |
| 고의적 무시 (시정) | $10,000~$50,000 |
| 고의적 무시 (미시정) | $50,000 |
| **연간 최대** | **$1,500,000** |

---

## 4. SOC 2 vs HIPAA vs ISO 27001 vs ISMS-P

| 항목 | SOC 2 | HIPAA | ISO 27001 | ISMS-P |
|------|-------|-------|-----------|--------|
| 국가 | 미국 | 미국 | 국제 | 한국 |
| 대상 | 서비스 기업 | 의료 관련 | 전 산업 | 전 산업 |
| 인증 | 보고서 | 자체 준수 | 인증서 | 인증서 |
| 감사 주체 | CPA 법인 | 자체/OCR | 인증기관 | KISA |
| 개인정보 | Privacy TSC | PHI 보호 | ISO 27701 | 통합(22항목) |
| 유효기간 | 12개월 | 지속 | 3년 | 3년 |

---

## 5. 글로벌 컴플라이언스 전략

### 5.1 공통 요구사항

거의 모든 표준/규정이 요구하는 공통 보안 통제:

```
1. 접근통제 (사용자 인증, 권한 관리)
2. 로깅 및 모니터링 (감사 로그)
3. 암호화 (전송/저장)
4. 패치 관리
5. 사고 대응 절차
6. 리스크 관리
7. 보안 교육
```

### 5.2 실습: 공통 기준 점검

```bash
# 모든 표준이 공통으로 요구하는 7가지 기본 점검
echo "========================================="
echo " 글로벌 컴플라이언스 공통 점검"
echo "========================================="

ip=192.168.208.142

echo "[1] 접근통제"
sshpass -p1 ssh user@$ip "grep -c '^PermitRootLogin no' /etc/ssh/sshd_config 2>/dev/null && echo '  root 로그인 차단: OK' || echo '  root 로그인 차단: FAIL'"

echo "[2] 로깅"
sshpass -p1 ssh user@$ip "systemctl is-active rsyslog 2>/dev/null && echo '  rsyslog: OK' || echo '  rsyslog: FAIL'"

echo "[3] 암호화"
sshpass -p1 ssh user@192.168.208.152 "echo | openssl s_client -connect localhost:443 2>/dev/null | grep 'Protocol' | grep -q 'TLSv1.[23]' && echo '  TLS: OK' || echo '  TLS: 확인필요'"

echo "[4] 패치"
cnt=$(sshpass -p1 ssh user@$ip "apt list --upgradable 2>/dev/null | wc -l")
echo "  미적용 패치: $cnt"

echo "[5] 사고대응"
sshpass -p1 ssh user@192.168.208.152 "systemctl is-active wazuh-manager 2>/dev/null && echo '  SIEM: OK' || echo '  SIEM: FAIL'"

echo "[6] 리스크관리"
echo "  (문서 점검 항목 - 리스크 평가 문서 존재 여부)"

echo "[7] 보안교육"
echo "  (문서 점검 항목 - 교육 이수 기록 존재 여부)"
```

---

## 6. 실무 시나리오: 다중 컴플라이언스 대응

한 기업이 ISO 27001 + SOC 2 + ISMS-P를 동시에 충족해야 하는 경우:

### 6.1 통합 접근법

```
1. 공통 기반 구축
   → ISO 27001 기반 ISMS 구축 (가장 포괄적)
2. SOC 2 추가 대응
   → Trust Service Criteria 매핑, 증적 수집
3. ISMS-P 추가 대응
   → 개인정보보호 요구사항 추가
4. 통합 감사
   → 한 번의 감사로 여러 인증 대응
```

### 6.2 매핑 테이블 예시

| 통제 | ISO 27001 | SOC 2 | ISMS-P | HIPAA |
|------|-----------|-------|--------|-------|
| 접근통제 정책 | A.5.15 | CC6.1 | 2.6.1 | 164.312(a) |
| 사용자 인증 | A.8.5 | CC6.1 | 2.5.3 | 164.312(d) |
| 감사 로그 | A.8.15 | CC7.2 | 2.10.4 | 164.312(b) |
| 암호화 | A.8.24 | CC6.7 | 2.7.1 | 164.312(e) |
| 사고 대응 | A.5.26 | CC7.4 | 2.11.3 | 164.308(a)(6) |

---

## 7. 핵심 정리

1. **SOC 2** = SaaS/클라우드 기업의 사실상 필수 인증, 5가지 TSC
2. **HIPAA** = 미국 의료정보 보호법, ePHI에 대한 기술적/관리적/물리적 보호
3. **공통 요구사항** = 접근통제, 로깅, 암호화, 패치, 사고대응
4. **다중 컴플라이언스** = ISO 27001 기반으로 구축하고 매핑으로 대응
5. **증적(Evidence)** = 모든 인증에서 가장 중요한 것은 "증명"

---

## 과제

1. SOC 2 Trust Service Criteria 5가지를 실습 환경에 대해 각각 점검하시오
2. HIPAA Security Rule의 기술적 보호조치를 실습 환경에서 점검하시오
3. ISO 27001, SOC 2, ISMS-P, HIPAA의 접근통제 관련 항목 매핑 표를 완성하시오

---

## 참고 자료

- AICPA SOC 2 Trust Service Criteria (TSC)
- HHS HIPAA Security Rule (https://www.hhs.gov/hipaa)
- SOC 2 Compliance Guide for Startups
- HIPAA Technical Safeguards Checklist
