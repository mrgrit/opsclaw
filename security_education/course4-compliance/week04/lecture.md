# Week 04: ISO 27001 (3) - 기술 통제 실습

## 학습 목표

- ISO 27001 A.8 기술적 통제를 실제 서버에서 점검할 수 있다
- 접근 통제, 암호화, 네트워크 보안 설정을 확인하고 평가한다
- 점검 결과를 통제 항목 기준으로 문서화한다

---

## 1. 실습 환경 구성 확인

### 1.1 서버 접속 테스트

```bash
# 모든 서버 접속 확인
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "=== $ip ==="
  sshpass -p1 ssh -o StrictHostKeyChecking=no user@$ip "hostname" 2>/dev/null || echo "접속 실패"
done
```

### 1.2 서버별 역할 확인

| 서버 | IP | 점검 대상 서비스 |
|------|----|-----------------|
| opsclaw | 192.168.208.142 | Manager API, PostgreSQL, SubAgent |
| secu | 192.168.208.150 | nftables 방화벽, Suricata IPS |
| web | 192.168.208.151 | BunkerWeb WAF, JuiceShop |
| siem | 192.168.208.152 | Wazuh Dashboard, OpenCTI |

---

## 2. A.8.1 사용자 단말 장치 (User Endpoint Devices)

서버에 접근하는 단말의 보안 설정을 확인한다.

```bash
# 자동 로그아웃 설정 확인 (TMOUT)
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "=== $ip ==="
  sshpass -p1 ssh user@$ip "grep TMOUT /etc/profile /etc/bash.bashrc /etc/environment 2>/dev/null || echo 'TMOUT 미설정'"
done
```

**점검 기준**: 서버의 TMOUT이 설정되어 있지 않으면 미준수. 권장값은 300~900초이다.

---

## 3. A.8.2 특수 접근 권한 (Privileged Access Rights)

### 3.1 sudo 권한 점검

```bash
# 각 서버의 sudo 사용자 확인
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "=== $ip ==="
  sshpass -p1 ssh user@$ip "getent group sudo 2>/dev/null; getent group wheel 2>/dev/null"
done
```

### 3.2 root 직접 로그인 차단 확인

```bash
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "=== $ip ==="
  sshpass -p1 ssh user@$ip "grep '^PermitRootLogin' /etc/ssh/sshd_config || echo '기본값 사용 중'"
done
```

**점검 기준**: PermitRootLogin이 `no`여야 준수. `yes`나 `prohibit-password`는 부분 준수.

### 3.3 SUID/SGID 파일 점검

```bash
# SUID 비트가 설정된 파일 확인 (권한 상승 위험)
sshpass -p1 ssh user@192.168.208.142 "find /usr -perm -4000 -type f 2>/dev/null"
```

---

## 4. A.8.5 보안 인증 (Secure Authentication)

### 4.1 비밀번호 정책 확인

```bash
# 비밀번호 복잡도 정책
sshpass -p1 ssh user@192.168.208.142 "cat /etc/security/pwquality.conf 2>/dev/null | grep -v '^#' | grep -v '^$' || echo 'pwquality 미설정'"

# 비밀번호 만료 기본 정책
sshpass -p1 ssh user@192.168.208.142 "grep -E 'PASS_MAX_DAYS|PASS_MIN_DAYS|PASS_MIN_LEN|PASS_WARN_AGE' /etc/login.defs"
```

### 4.2 SSH 인증 방식 점검

```bash
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "=== $ip ==="
  sshpass -p1 ssh user@$ip "grep -E 'PasswordAuthentication|PubkeyAuthentication|MaxAuthTries' /etc/ssh/sshd_config | grep -v '^#'"
done
```

**점검 기준**:
- PubkeyAuthentication yes (권장)
- PasswordAuthentication no (키 기반 인증만 허용이 이상적)
- MaxAuthTries 3~5 (무차별 대입 방지)

### 4.3 로그인 실패 잠금 설정

```bash
# PAM 기반 계정 잠금 설정 확인
sshpass -p1 ssh user@192.168.208.142 "grep pam_faillock /etc/pam.d/common-auth 2>/dev/null || echo 'faillock 미설정'"
sshpass -p1 ssh user@192.168.208.142 "grep pam_tally /etc/pam.d/common-auth 2>/dev/null || echo 'tally 미설정'"
```

---

## 5. A.8.9 설정 관리 (Configuration Management)

### 5.1 불필요한 서비스 확인

```bash
# 실행 중인 서비스 중 불필요한 것이 있는지 확인
sshpass -p1 ssh user@192.168.208.142 "systemctl list-units --type=service --state=running --no-pager | grep -E 'cups|avahi|bluetooth|rpcbind'"
```

### 5.2 커널 보안 파라미터 확인

```bash
sshpass -p1 ssh user@192.168.208.142 "sysctl net.ipv4.ip_forward net.ipv4.conf.all.accept_redirects net.ipv4.conf.all.accept_source_route net.ipv4.conf.all.log_martians 2>/dev/null"
```

**권장 설정**:
- `ip_forward = 0` (라우터가 아닌 경우)
- `accept_redirects = 0` (ICMP 리다이렉트 차단)
- `accept_source_route = 0` (소스 라우팅 차단)
- `log_martians = 1` (비정상 패킷 로깅)

---

## 6. A.8.15 로깅 (Logging)

### 6.1 로그 설정 확인

```bash
# rsyslog 설정 확인
sshpass -p1 ssh user@192.168.208.142 "cat /etc/rsyslog.conf | grep -v '^#' | grep -v '^$' | head -20"

# 주요 로그 파일 존재 및 크기 확인
sshpass -p1 ssh user@192.168.208.142 "ls -lh /var/log/syslog /var/log/auth.log /var/log/kern.log 2>/dev/null"
```

### 6.2 감사 로그 (auditd) 확인

```bash
# auditd 설치 및 실행 여부
sshpass -p1 ssh user@192.168.208.142 "systemctl status auditd 2>/dev/null | head -5 || echo 'auditd 미설치'"

# audit 규칙 확인
sshpass -p1 ssh user@192.168.208.142 "sudo auditctl -l 2>/dev/null || echo 'audit 규칙 없음'"
```

### 6.3 Wazuh 에이전트 로그 수집 확인

```bash
# Wazuh 에이전트 상태
for ip in 192.168.208.142 192.168.208.150 192.168.208.151; do
  echo "=== $ip ==="
  sshpass -p1 ssh user@$ip "systemctl status wazuh-agent 2>/dev/null | grep Active || echo 'Wazuh Agent 미설치'"
done
```

---

## 7. A.8.20 네트워크 보안 (Networks Security)

### 7.1 방화벽 규칙 점검

```bash
# secu 서버의 nftables 규칙 확인
sshpass -p1 ssh user@192.168.208.150 "sudo nft list ruleset"
```

### 7.2 열린 포트 점검

```bash
# 각 서버에서 열려 있는 포트 확인
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "=== $ip ==="
  sshpass -p1 ssh user@$ip "ss -tlnp 2>/dev/null | grep LISTEN"
done
```

**점검 기준**: 서비스에 필요하지 않은 포트가 열려 있으면 미준수.

### 7.3 네트워크 분리 확인

```bash
# secu 서버의 네트워크 인터페이스 확인 (DMZ 분리)
sshpass -p1 ssh user@192.168.208.150 "ip addr show | grep 'inet '"
```

---

## 8. A.8.24 암호화 사용 (Use of Cryptography)

### 8.1 TLS 설정 확인

```bash
# Wazuh 대시보드 TLS 확인
sshpass -p1 ssh user@192.168.208.152 "echo | openssl s_client -connect localhost:443 2>/dev/null | head -20"

# TLS 버전 확인 (TLS 1.2 이상이어야 함)
sshpass -p1 ssh user@192.168.208.152 "echo | openssl s_client -connect localhost:443 2>/dev/null | grep 'Protocol'"
```

### 8.2 SSH 암호화 알고리즘 확인

```bash
sshpass -p1 ssh user@192.168.208.142 "grep -E 'Ciphers|MACs|KexAlgorithms' /etc/ssh/sshd_config | grep -v '^#'"
```

### 8.3 디스크 암호화 확인

```bash
sshpass -p1 ssh user@192.168.208.142 "lsblk -o NAME,FSTYPE,MOUNTPOINT | head -10"
sshpass -p1 ssh user@192.168.208.142 "dmsetup status 2>/dev/null | head -5 || echo 'dm-crypt 미사용'"
```

---

## 9. 점검 결과 문서화

### 9.1 점검 결과 템플릿

다음 형식으로 결과를 정리한다:

```
| 통제 항목 | 점검 대상 | 기대 결과 | 실제 결과 | 적합 여부 | 조치 사항 |
|-----------|----------|----------|----------|----------|----------|
| A.8.2 특수접근권한 | opsclaw SSH | PermitRootLogin no | ? | ? | ? |
| A.8.5 보안인증 | opsclaw SSH | MaxAuthTries 5 | ? | ? | ? |
| A.8.15 로깅 | opsclaw auditd | active 상태 | ? | ? | ? |
| A.8.20 네트워크 | secu nftables | 정책 존재 | ? | ? | ? |
| A.8.24 암호화 | siem TLS | TLS 1.2+ | ? | ? | ? |
```

---

## 10. 핵심 정리

1. **기술적 통제 점검** = 실제 서버 설정을 ISO 27001 기준으로 확인하는 것
2. **접근 통제**: SSH 설정, sudo 권한, 비밀번호 정책
3. **로깅**: rsyslog, auditd, Wazuh 에이전트
4. **네트워크**: 방화벽 규칙, 열린 포트, 네트워크 분리
5. **암호화**: TLS 버전, SSH 알고리즘, 디스크 암호화

---

## 과제

1. 4개 서버 모두에 대해 위 점검 항목을 수행하고 결과를 표로 작성하시오
2. 미준수 항목에 대한 개선 방안을 제시하시오
3. 자동 점검 스크립트를 작성하시오 (선택)

---

## 참고 자료

- CIS Benchmarks for Ubuntu Linux
- KISA 서버 보안 가이드
- SSH Hardening Guide (ssh-audit 도구)
