# Week 09: GDPR / 개인정보보호 - EU와 한국 비교

## 학습 목표

- GDPR(EU 일반 개인정보보호 규정)의 핵심 원칙을 이해한다
- 한국의 개인정보보호법과 GDPR을 비교할 수 있다
- 개인정보 처리의 기술적 보호조치를 실습한다
- 개인정보 유출 대응 절차를 파악한다

---

## 1. GDPR이란?

### 1.1 개요

- **GDPR**: General Data Protection Regulation (EU 일반 개인정보보호 규정)
- 2018년 5월 25일 시행
- EU 시민의 개인정보를 처리하는 **모든 조직**에 적용 (EU 밖 기업 포함)

### 1.2 왜 알아야 하는가?

| 이유 | 설명 |
|------|------|
| 역외 적용 | 한국 기업도 EU 고객 데이터를 다루면 적용 |
| 높은 과징금 | 최대 2천만 유로 또는 전세계 연매출 4% |
| 글로벌 표준 | 한국법도 GDPR을 참고하여 개정 |
| 기술 요구사항 | 개발자/운영자에게 직접적인 기술 요구 |

---

## 2. GDPR 핵심 원칙 (7가지)

### 2.1 원칙 목록

| 원칙 | 내용 | 예시 |
|------|------|------|
| 적법성/공정성/투명성 | 합법적 근거로 공정하게 처리 | 동의서, 개인정보처리방침 |
| 목적 제한 | 명확한 목적으로만 수집 | 마케팅 동의 없이 광고 발송 불가 |
| 데이터 최소화 | 필요한 최소한만 수집 | 배송에 주민번호 불필요 |
| 정확성 | 정확하게 유지 | 오래된 정보 갱신 |
| 보관 제한 | 목적 달성 후 파기 | 탈퇴 회원 정보 즉시 삭제 |
| 무결성/기밀성 | 적절한 보안 조치 | 암호화, 접근통제 |
| 책임성 | 준수를 증명할 의무 | 처리 활동 기록 |

### 2.2 적법한 처리 근거 (6가지)

```
1. 정보주체의 동의
2. 계약 이행
3. 법적 의무
4. 정보주체의 중대한 이익
5. 공익 목적
6. 정당한 이익 (이해관계 균형)
```

---

## 3. 정보주체의 권리

| 권리 | 내용 | GDPR 조항 |
|------|------|----------|
| 열람권 | 자신의 데이터 확인 | 제15조 |
| 정정권 | 부정확한 데이터 수정 | 제16조 |
| 삭제권 (잊힐 권리) | 데이터 삭제 요구 | 제17조 |
| 처리 제한권 | 처리 일시 중지 요구 | 제18조 |
| 이동권 | 다른 서비스로 데이터 이전 | 제20조 |
| 반대권 | 특정 처리에 반대 | 제21조 |
| 자동화 결정 거부권 | AI/자동 판단 거부 | 제22조 |

---

## 4. 한국 개인정보보호법과 비교

### 4.1 주요 비교

| 항목 | GDPR | 한국 개인정보보호법 |
|------|------|-------------------|
| 시행 | 2018년 | 2011년 (2020년 대규모 개정) |
| 적용 범위 | EU 시민 데이터 처리 전체 | 한국 내 개인정보 처리 |
| 역외 적용 | 있음 | 제한적 |
| 과징금 | 매출 4% 또는 2천만 유로 | 매출 3% 이하 |
| DPO 의무 | 특정 조건 시 필수 | CPO(개인정보보호책임자) 필수 |
| 동의 방식 | 옵트인 (명시적) | 옵트인 (명시적) |
| 잊힐 권리 | 명시적 규정 | 삭제 요구권 |
| 이동권 | 명시적 규정 | 2023년 도입 (마이데이터) |
| 처벌 | 행정 과징금 중심 | 형사 처벌 + 과징금 |

### 4.2 한국법 특이사항

- **주민등록번호**: 원칙적 수집 금지 (법적 근거 필요)
- **개인정보 영향평가**: 공공기관 의무
- **개인정보보호위원회**: 독립 감독기관 (2020년 격상)
- **정보통신망법**: 온라인 서비스 추가 규제

---

## 5. 기술적 보호조치

### 5.1 GDPR Article 32 - 처리의 보안

GDPR은 다음 기술적 조치를 요구한다:

```
(a) 개인정보의 가명처리 및 암호화
(b) 처리 시스템의 기밀성, 무결성, 가용성, 복원력 보장
(c) 물리적/기술적 사고 시 적시에 가용성 복원
(d) 보호조치의 효과를 정기적으로 테스트/평가
```

### 5.2 실습: 데이터베이스의 개인정보 보호

```bash
# PostgreSQL 접속하여 암호화 확인
sshpass -p1 ssh user@192.168.208.142 "PGPASSWORD=opsclaw psql -h 127.0.0.1 -U opsclaw -d opsclaw -c \"SHOW ssl;\" 2>/dev/null"

# DB 접근 권한 확인
sshpass -p1 ssh user@192.168.208.142 "PGPASSWORD=opsclaw psql -h 127.0.0.1 -U opsclaw -d opsclaw -c \"\\du\" 2>/dev/null"

# DB 접근 로그 설정 확인
sshpass -p1 ssh user@192.168.208.142 "PGPASSWORD=opsclaw psql -h 127.0.0.1 -U opsclaw -d opsclaw -c \"SHOW log_connections;\" 2>/dev/null"
sshpass -p1 ssh user@192.168.208.142 "PGPASSWORD=opsclaw psql -h 127.0.0.1 -U opsclaw -d opsclaw -c \"SHOW log_disconnections;\" 2>/dev/null"
```

### 5.3 실습: 전송 구간 암호화

```bash
# 웹 서비스의 TLS 설정 확인
sshpass -p1 ssh user@192.168.208.151 "echo | openssl s_client -connect localhost:443 2>/dev/null | grep -E 'Protocol|Cipher'"

# Wazuh API TLS
sshpass -p1 ssh user@192.168.208.152 "echo | openssl s_client -connect localhost:55000 2>/dev/null | grep Protocol"

# Wazuh Dashboard TLS
sshpass -p1 ssh user@192.168.208.152 "echo | openssl s_client -connect localhost:443 2>/dev/null | grep Protocol"
```

### 5.4 실습: 접근 통제

```bash
# 개인정보가 포함될 수 있는 로그 파일의 접근 권한
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "=== $ip ==="
  sshpass -p1 ssh user@$ip "ls -la /var/log/auth.log /var/log/syslog 2>/dev/null"
done
```

### 5.5 실습: 로그에서 개인정보 확인

```bash
# 로그에 IP 주소(개인정보 해당 가능)가 기록되는지 확인
sshpass -p1 ssh user@192.168.208.150 "tail -20 /var/log/suricata/fast.log 2>/dev/null"

# 웹 로그에서 사용자 정보 확인
sshpass -p1 ssh user@192.168.208.151 "tail -10 /var/log/nginx/access.log 2>/dev/null || tail -10 /var/log/bunkerweb/access.log 2>/dev/null"
```

---

## 6. 개인정보 유출 대응

### 6.1 GDPR 유출 통지 의무

```
발견 → 72시간 이내 감독기관 통지
     → 고위험인 경우 정보주체에게도 통지
```

### 6.2 한국법 유출 통지 의무

```
발견 → 72시간 이내 정보주체 통지
     → 1천명 이상 유출 시 개인정보보호위원회 + KISA 신고
```

### 6.3 유출 대응 절차

```
1. 유출 인지 및 초기 대응
   - 유출 범위 파악
   - 추가 유출 차단
2. 영향 평가
   - 유출 데이터 종류
   - 영향 받는 정보주체 수
   - 위험도 평가
3. 통지
   - 감독기관 통지 (72시간)
   - 정보주체 통지
4. 사후 조치
   - 원인 분석
   - 재발 방지 대책
   - 기록 보존
```

### 6.4 실습: 유출 탐지 시뮬레이션

```bash
# 대량 데이터 외부 전송 시도 탐지 (Wazuh 알림)
sshpass -p1 ssh user@192.168.208.152 "cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c \"
import sys, json
for line in sys.stdin:
    try:
        alert = json.loads(line)
        rule = alert.get('rule', {})
        if rule.get('level', 0) >= 10:
            print(f'Level {rule[\"level\"]}: {rule.get(\"description\",\"\")}')
    except: pass
\" 2>/dev/null | head -10"

# auth.log에서 대량 접근 시도 확인
sshpass -p1 ssh user@192.168.208.142 "grep 'session opened' /var/log/auth.log 2>/dev/null | wc -l"
```

---

## 7. 가명처리와 익명처리

### 7.1 개념 비교

| 구분 | 가명처리 (Pseudonymization) | 익명처리 (Anonymization) |
|------|---------------------------|------------------------|
| 정의 | 추가 정보 없이는 식별 불가 | 어떤 수단으로도 식별 불가 |
| GDPR 적용 | 적용됨 (여전히 개인정보) | 적용 안됨 |
| 복원 가능 | 가능 (매핑 테이블 보유) | 불가능 |
| 예시 | 이름을 해시값으로 대체 | 통계 데이터만 추출 |

### 7.2 실습: 간단한 가명처리 예시

```bash
# 로그에서 IP 주소를 해시로 가명처리하는 예시
sshpass -p1 ssh user@192.168.208.142 "echo '192.168.208.150 tried SSH login' | \
  sed -E 's/([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)/[MASKED]/g'"

# Python으로 가명처리
sshpass -p1 ssh user@192.168.208.142 "python3 -c \"
import hashlib
ip = '192.168.208.150'
pseudo = hashlib.sha256(ip.encode()).hexdigest()[:8]
print(f'원본: {ip}')
print(f'가명: user_{pseudo}')
\""
```

---

## 8. 개인정보보호 체크리스트 (실습 환경)

```bash
# 종합 점검 스크립트
echo "=== 개인정보보호 기술적 점검 ==="

echo "[1] DB 암호화 설정:"
sshpass -p1 ssh user@192.168.208.142 "PGPASSWORD=opsclaw psql -h 127.0.0.1 -U opsclaw -d opsclaw -c 'SHOW ssl;' 2>/dev/null"

echo "[2] 전송 암호화 (TLS):"
sshpass -p1 ssh user@192.168.208.152 "echo | openssl s_client -connect localhost:443 2>/dev/null | grep Protocol"

echo "[3] 접근 로그 활성화:"
sshpass -p1 ssh user@192.168.208.142 "PGPASSWORD=opsclaw psql -h 127.0.0.1 -U opsclaw -d opsclaw -c 'SHOW log_statement;' 2>/dev/null"

echo "[4] 로그 파일 권한:"
sshpass -p1 ssh user@192.168.208.142 "stat -c '%a' /var/log/auth.log 2>/dev/null"

echo "[5] 백업 암호화:"
sshpass -p1 ssh user@192.168.208.142 "ls /backup/*.gpg 2>/dev/null || echo '암호화된 백업 없음'"
```

---

## 9. 핵심 정리

1. **GDPR** = EU 시민 데이터를 다루는 모든 조직에 적용되는 강력한 규정
2. **7가지 원칙** = 적법성, 목적제한, 최소화, 정확성, 보관제한, 보안, 책임
3. **정보주체 권리** = 열람, 정정, 삭제, 이동, 반대, 자동화결정 거부
4. **한국법과 유사** = 동의 기반, 목적 제한, 안전조치 의무
5. **72시간 통지** = GDPR과 한국법 모두 유출 시 신속 통지 의무

---

## 과제

1. GDPR과 한국 개인정보보호법의 차이점을 5가지 이상 정리하시오
2. 실습 환경에서 개인정보보호 기술적 점검을 수행하고 결과를 보고하시오
3. 로그 데이터에서 개인정보(IP, 사용자명)를 가명처리하는 스크립트를 작성하시오

---

## 참고 자료

- EU GDPR 공식 문서 (https://gdpr.eu)
- 개인정보보호위원회 (https://www.pipc.go.kr)
- 한국 개인정보보호법 전문
- GDPR vs 한국법 비교 분석 (KISA 발간)
