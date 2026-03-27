# Week 07: NIST CSF - 사이버보안 프레임워크

## 학습 목표

- NIST CSF(Cybersecurity Framework)의 5가지 기능을 이해한다
- 각 기능의 카테고리와 서브카테고리를 설명할 수 있다
- NIST CSF를 실습 환경에 적용하여 평가할 수 있다
- ISO 27001, ISMS-P와의 관계를 파악한다

---

## 1. NIST CSF란?

### 1.1 배경

- **NIST**: 미국 국립표준기술연구소 (National Institute of Standards and Technology)
- **CSF**: Cybersecurity Framework
- 2014년 초판 발행, **2024년 CSF 2.0** 개정
- 미국 정부 기관뿐 아니라 전 세계 민간 기업도 널리 활용

### 1.2 특징

| 특징 | 설명 |
|------|------|
| 리스크 기반 | 위험도에 따라 우선순위 결정 |
| 성과 기반 | "무엇을 달성할 것인가"에 초점 |
| 기술 중립적 | 특정 기술/제품에 종속되지 않음 |
| 자발적 | 법적 의무 아님 (권장 사항) |
| 유연함 | 조직 규모/산업에 맞게 조정 가능 |

---

## 2. 5가지 핵심 기능 (CSF 1.1 기준)

### 2.1 전체 구조

```
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│ Identify │→│ Protect  │→│  Detect  │→│ Respond  │→│ Recover  │
│  (식별)  │  │  (보호)  │  │  (탐지)  │  │  (대응)  │  │  (복구)  │
└──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘
```

> CSF 2.0에서는 **Govern(거버넌스)**이 추가되어 6개 기능이지만,
> 핵심 5개 기능의 이해가 먼저이다.

### 2.2 각 기능의 목표

| 기능 | 목표 | 핵심 질문 |
|------|------|----------|
| Identify | 자산과 리스크 파악 | "우리가 보호해야 할 것은 무엇인가?" |
| Protect | 보안 대책 구현 | "어떻게 보호할 것인가?" |
| Detect | 보안 이벤트 탐지 | "침해가 발생했는지 어떻게 알 수 있는가?" |
| Respond | 사고 대응 | "침해 발생 시 무엇을 할 것인가?" |
| Recover | 복구 및 개선 | "어떻게 정상으로 돌아갈 것인가?" |

---

## 3. Identify (식별)

### 3.1 카테고리

| ID | 카테고리 | 내용 |
|----|---------|------|
| ID.AM | 자산 관리 | 하드웨어, 소프트웨어, 데이터 인벤토리 |
| ID.BE | 비즈니스 환경 | 조직의 역할, 공급망, 핵심 서비스 |
| ID.GV | 거버넌스 | 정책, 법적 요구사항, 리스크 관리 전략 |
| ID.RA | 리스크 평가 | 위협, 취약점, 영향도, 가능성 |
| ID.RM | 리스크 관리 전략 | 리스크 수용 기준, 우선순위 |
| ID.SC | 공급망 리스크 | 외부 파트너/공급업체 리스크 |

### 3.2 실습: 자산 식별 (ID.AM)

```bash
# ID.AM-1: 물리적 장치 및 시스템 인벤토리
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "=== $ip ==="
  sshpass -p1 ssh user@$ip "hostname; lscpu | grep 'Model name'; free -h | grep Mem; df -h / | tail -1"
done

# ID.AM-2: 소프트웨어 인벤토리
sshpass -p1 ssh user@192.168.208.142 "dpkg -l | wc -l"
sshpass -p1 ssh user@192.168.208.142 "systemctl list-units --type=service --state=running --no-pager | wc -l"

# ID.AM-3: 데이터 흐름 매핑
sshpass -p1 ssh user@192.168.208.150 "ip route show"
sshpass -p1 ssh user@192.168.208.150 "ss -tlnp | grep LISTEN"
```

---

## 4. Protect (보호)

### 4.1 카테고리

| ID | 카테고리 | 내용 |
|----|---------|------|
| PR.AC | 접근 통제 | 신원 관리, 인증, 원격 접근 |
| PR.AT | 인식 교육 | 보안 교육, 역할 기반 훈련 |
| PR.DS | 데이터 보안 | 암호화, 무결성, 유출 방지 |
| PR.IP | 보호 프로세스 | 설정 관리, 백업, 변경 관리 |
| PR.MA | 유지보수 | 원격/현장 유지보수 통제 |
| PR.PT | 보호 기술 | 로깅, 이동매체, 네트워크 보호 |

### 4.2 실습: 보호 대책 점검

```bash
# PR.AC-1: 접근 통제 (계정 관리)
sshpass -p1 ssh user@192.168.208.142 "awk -F: '\$3>=1000 && \$3<65534{print \$1}' /etc/passwd"

# PR.AC-3: 원격 접근 관리 (SSH 설정)
sshpass -p1 ssh user@192.168.208.142 "grep -E 'PermitRootLogin|MaxAuthTries|Protocol' /etc/ssh/sshd_config | grep -v '^#'"

# PR.DS-1: 전송 데이터 보호 (TLS)
sshpass -p1 ssh user@192.168.208.152 "echo | openssl s_client -connect localhost:443 2>/dev/null | grep Protocol"

# PR.DS-2: 저장 데이터 보호 (파일 권한)
sshpass -p1 ssh user@192.168.208.142 "ls -la /etc/shadow"

# PR.IP-1: 설정 관리 (기본 설정 변경 여부)
sshpass -p1 ssh user@192.168.208.142 "grep '^Port' /etc/ssh/sshd_config || echo '기본 포트(22) 사용'"

# PR.IP-4: 백업
sshpass -p1 ssh user@192.168.208.142 "crontab -l 2>/dev/null | grep backup || echo '자동 백업 미설정'"

# PR.PT-1: 감사 로그
sshpass -p1 ssh user@192.168.208.142 "systemctl is-active rsyslog 2>/dev/null"
```

---

## 5. Detect (탐지)

### 5.1 카테고리

| ID | 카테고리 | 내용 |
|----|---------|------|
| DE.AE | 이상 징후 및 이벤트 | 기준선 설정, 이벤트 분석 |
| DE.CM | 지속적 모니터링 | 네트워크, 시스템, 악성코드 모니터링 |
| DE.DP | 탐지 프로세스 | 역할 정의, 테스트, 개선 |

### 5.2 실습: 탐지 체계 점검

```bash
# DE.CM-1: 네트워크 모니터링 (Suricata IPS)
sshpass -p1 ssh user@192.168.208.150 "systemctl is-active suricata 2>/dev/null"
sshpass -p1 ssh user@192.168.208.150 "tail -3 /var/log/suricata/fast.log 2>/dev/null || echo '로그 없음'"

# DE.CM-4: 악성코드 탐지
sshpass -p1 ssh user@192.168.208.142 "which clamscan 2>/dev/null || echo 'AV 미설치'"

# DE.CM-7: 비인가 활동 모니터링 (Wazuh)
sshpass -p1 ssh user@192.168.208.152 "systemctl is-active wazuh-manager 2>/dev/null"

# DE.AE-3: 이벤트 데이터 수집 확인
sshpass -p1 ssh user@192.168.208.152 "ls -lh /var/ossec/logs/alerts/alerts.json 2>/dev/null"
```

---

## 6. Respond (대응)

### 6.1 카테고리

| ID | 카테고리 | 내용 |
|----|---------|------|
| RS.RP | 대응 계획 | 사고 대응 절차 실행 |
| RS.CO | 커뮤니케이션 | 내외부 이해관계자 소통 |
| RS.AN | 분석 | 사고 조사, 영향 분석 |
| RS.MI | 완화 | 사고 격리, 확산 방지 |
| RS.IM | 개선 | 대응 절차 개선 |

### 6.2 실습: 대응 체계 점검

```bash
# RS.AN-1: 사고 분석 (로그 분석 능력)
# 최근 SSH 실패 로그 분석
sshpass -p1 ssh user@192.168.208.142 "grep 'Failed password' /var/log/auth.log 2>/dev/null | tail -5"

# RS.MI-1: 사고 격리 (방화벽으로 IP 차단 가능 여부)
sshpass -p1 ssh user@192.168.208.150 "sudo nft list ruleset 2>/dev/null | grep 'drop' | head -5"

# RS.CO-1: 알림 체계 확인 (Wazuh 알림 설정)
sshpass -p1 ssh user@192.168.208.152 "cat /var/ossec/etc/ossec.conf 2>/dev/null | grep -A5 '<email_notification>' | head -6"
```

---

## 7. Recover (복구)

### 7.1 카테고리

| ID | 카테고리 | 내용 |
|----|---------|------|
| RC.RP | 복구 계획 | 복구 절차 실행 |
| RC.IM | 개선 | 복구 전략 개선 |
| RC.CO | 커뮤니케이션 | 복구 상태 공유 |

### 7.2 실습: 복구 체계 점검

```bash
# RC.RP-1: 백업 존재 여부
sshpass -p1 ssh user@192.168.208.142 "ls -la /backup/ 2>/dev/null || echo '백업 디렉토리 없음'"

# 데이터베이스 백업 확인
sshpass -p1 ssh user@192.168.208.142 "ls -la /tmp/*dump* /tmp/*backup* 2>/dev/null || echo 'DB 백업 없음'"

# 서비스 재시작 능력 확인
sshpass -p1 ssh user@192.168.208.142 "systemctl is-enabled postgresql 2>/dev/null || echo 'postgresql 서비스 상태 확인 필요'"
```

---

## 8. NIST CSF vs ISO 27001 vs ISMS-P 비교

| 구분 | NIST CSF | ISO 27001 | ISMS-P |
|------|---------|-----------|--------|
| 국가 | 미국 | 국제 | 한국 |
| 성격 | 프레임워크 (가이드) | 표준 (인증) | 표준 (인증) |
| 접근법 | 기능 기반 (5+1) | 프로세스 기반 | 영역 기반 (3) |
| 인증 | 없음 | 있음 | 있음 |
| 강점 | 유연, 직관적 | 국제적 인정 | 한국법 완전 대응 |

### 8.1 매핑 예시

| NIST CSF | ISO 27001 | ISMS-P |
|----------|-----------|--------|
| ID.AM (자산관리) | A.5.9~A.5.14 | 2.1.3 |
| PR.AC (접근통제) | A.8.1~A.8.5 | 2.5, 2.6 |
| DE.CM (모니터링) | A.8.15~A.8.16 | 2.10.4 |
| RS.AN (사고분석) | A.5.25~A.5.27 | 2.11 |
| RC.RP (복구) | A.5.29~A.5.30 | 2.12 |

---

## 9. 실습: CSF 프로파일 작성

우리 실습 환경에 대한 간이 CSF 프로파일을 작성한다:

| 기능 | 카테고리 | 현재 수준 (1~4) | 목표 수준 | 갭 |
|------|---------|----------------|----------|-----|
| Identify | ID.AM 자산관리 | ? | 3 | ? |
| Protect | PR.AC 접근통제 | ? | 3 | ? |
| Detect | DE.CM 모니터링 | ? | 3 | ? |
| Respond | RS.AN 분석 | ? | 2 | ? |
| Recover | RC.RP 복구계획 | ? | 2 | ? |

**수준 정의**:
- 1: 부분적 (Partial) - 비공식, 임시 대응
- 2: 리스크 인지 (Risk Informed) - 일부 프로세스 존재
- 3: 반복 가능 (Repeatable) - 문서화된 절차
- 4: 적응형 (Adaptive) - 지속적 개선

---

## 10. 핵심 정리

1. **NIST CSF** = 5가지 기능(식별/보호/탐지/대응/복구) 기반 프레임워크
2. **인증이 아닌 가이드** = 조직에 맞게 유연하게 적용
3. **성숙도 모델** = Tier 1~4로 현재 수준과 목표를 비교
4. **다른 표준과 호환** = ISO 27001, ISMS-P 등과 매핑 가능
5. **CSF 2.0** = Govern(거버넌스) 기능 추가

---

## 과제

1. 실습 환경 4개 서버에 대해 CSF 5가지 기능별로 현재 수준을 평가하시오
2. 가장 개선이 시급한 기능과 그 이유를 설명하시오
3. NIST CSF와 ISMS-P의 매핑 표를 10개 항목 이상 작성하시오

---

## 참고 자료

- NIST Cybersecurity Framework v2.0 (https://www.nist.gov/cyberframework)
- NIST SP 800-53 Security and Privacy Controls
- NIST CSF to ISO 27001 Mapping Guide
