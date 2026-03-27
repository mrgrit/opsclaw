# Week 11: Wazuh SIEM (3) — FIM, SCA, Active Response (상세 버전)

## 학습 목표
- FIM(File Integrity Monitoring)을 설정하고 파일 변경을 탐지할 수 있다
- SCA(Security Configuration Assessment)로 보안 설정을 평가할 수 있다
- Active Response를 구성하여 위협에 자동 대응할 수 있다
- 각 개념의 보안 관점에서의 위험과 대응 방안을 분석할 수 있다
- OpsClaw를 활용하여 실습 작업을 자동화하고 증적을 관리할 수 있다
- 실제 보안 사고 사례와 연결하여 학습 내용을 적용할 수 있다


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

## 용어 해설 (보안 솔루션 운영 과목)

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **방화벽** | Firewall | 네트워크 트래픽을 규칙에 따라 허용/차단하는 시스템 | 건물 출입 통제 시스템 |
| **체인** | Chain (nftables) | 패킷 처리 규칙의 묶음 (input, forward, output) | 심사 단계 |
| **룰/규칙** | Rule | 특정 조건의 트래픽을 어떻게 처리할지 정의 | "택배 기사만 출입 허용" |
| **시그니처** | Signature | 알려진 공격 패턴을 식별하는 규칙 (IPS/AV) | 수배범 얼굴 사진 |
| **NFQUEUE** | Netfilter Queue | 커널에서 사용자 영역으로 패킷을 넘기는 큐 | 의심 택배를 별도 검사대로 보내는 것 |
| **FIM** | File Integrity Monitoring | 파일 변조 감시 (해시 비교) | CCTV로 금고 감시 |
| **SCA** | Security Configuration Assessment | 보안 설정 점검 (CIS 벤치마크 기반) | 건물 안전 점검표 |
| **Active Response** | Active Response | 탐지 시 자동 대응 (IP 차단 등) | 침입 감지 시 자동 잠금 |
| **디코더** | Decoder (Wazuh) | 로그를 파싱하여 구조화하는 규칙 | 외국어 통역사 |
| **CRS** | Core Rule Set (ModSecurity) | 범용 웹 공격 탐지 규칙 모음 | 표준 보안 검사 매뉴얼 |
| **CTI** | Cyber Threat Intelligence | 사이버 위협 정보 (IOC, TTPs) | 범죄 정보 공유 시스템 |
| **IOC** | Indicator of Compromise | 침해 지표 (악성 IP, 해시, 도메인 등) | 수배범의 지문, 차량번호 |
| **STIX** | Structured Threat Information eXpression | 위협 정보 표준 포맷 | 범죄 보고서 표준 양식 |
| **TAXII** | Trusted Automated eXchange of Intelligence Information | CTI 자동 교환 프로토콜 | 경찰서 간 수배 정보 공유 시스템 |
| **NAT** | Network Address Translation | 내부 IP를 외부 IP로 변환 | 회사 대표번호 (내선→외선) |
| **masquerade** | masquerade (nftables) | 나가는 패킷의 소스 IP를 게이트웨이 IP로 변환 | 회사 이름으로 편지 보내기 |


# 본 강의 내용

# Week 11: Wazuh SIEM (3) — FIM, SCA, Active Response

## 학습 목표

- FIM(File Integrity Monitoring)을 설정하고 파일 변경을 탐지할 수 있다
- SCA(Security Configuration Assessment)로 보안 설정을 평가할 수 있다
- Active Response를 구성하여 위협에 자동 대응할 수 있다

---

## 1. FIM (File Integrity Monitoring)

### 1.1 FIM이란?

FIM은 중요 파일의 변경(생성, 수정, 삭제)을 실시간으로 감지하는 기능이다.

**왜 필요한가?**
- 공격자가 설정 파일을 변조하면 시스템이 장악된다
- `/etc/passwd`, `/etc/shadow` 변경 = 계정 추가/변조
- 웹쉘 업로드 = 웹 디렉터리에 새 파일 생성

### 1.2 FIM 동작 방식

```
초기 스캔 → 파일 해시(checksum) 저장
  ↓
주기적/실시간 스캔 → 해시 비교
  ↓
변경 감지 시 → 알림 생성 (who changed, when, what)
```

---

## 2. 실습 환경 접속

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.100
```

---

## 3. FIM 설정

### 3.1 현재 FIM 설정 확인

```bash
echo 1 | sudo -S grep -A 30 "<syscheck>" /var/ossec/etc/ossec.conf | head -40
```

### 3.2 FIM 설정 항목

ossec.conf 내 `<syscheck>` 섹션:

```xml
<syscheck>
  <!-- 스캔 주기 (초) -->
  <frequency>600</frequency>

  <!-- 실시간 모니터링 디렉터리 -->
  <directories realtime="yes" check_all="yes">/etc,/usr/bin,/usr/sbin</directories>

  <!-- 웹 디렉터리 (웹쉘 탐지) -->
  <directories realtime="yes" check_all="yes" report_changes="yes">/var/www</directories>

  <!-- 감시 제외 -->
  <ignore>/etc/mtab</ignore>
  <ignore>/etc/resolv.conf</ignore>
  <ignore type="sregex">.log$</ignore>

  <!-- who-data (감사 로그 기반 - 누가 변경했는지 추적) -->
  <directories whodata="yes">/etc/passwd,/etc/shadow,/etc/sudoers</directories>
</syscheck>
```

| 옵션 | 설명 |
|------|------|
| `frequency` | 전체 스캔 주기 (초) |
| `realtime="yes"` | inotify 기반 실시간 감시 |
| `whodata="yes"` | audit 기반 변경자 추적 |
| `check_all="yes"` | 모든 속성 검사 (해시, 권한, 소유자 등) |
| `report_changes="yes"` | 파일 내용 변경 diff 기록 |
| `ignore` | 감시 제외 경로/패턴 |

### 3.3 FIM 설정 추가 (실습)

```bash
# secu 서버 Agent 설정에 추가
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.1

echo 1 | sudo -S cat >> /var/ossec/etc/ossec.conf << 'FIMEOF'
<ossec_config>
  <syscheck>
    <frequency>300</frequency>

    <!-- 핵심 시스템 파일 실시간 감시 -->
    <directories realtime="yes" check_all="yes">/etc/passwd,/etc/shadow,/etc/sudoers</directories>

    <!-- nftables 설정 감시 -->
    <directories realtime="yes" check_all="yes" report_changes="yes">/etc/nftables.conf</directories>

    <!-- Suricata 설정/룰 감시 -->
    <directories realtime="yes" check_all="yes">/etc/suricata/suricata.yaml</directories>
    <directories realtime="yes" check_all="yes" report_changes="yes">/etc/suricata/rules</directories>

    <!-- 테스트용 디렉터리 -->
    <directories realtime="yes" check_all="yes" report_changes="yes">/tmp/fim_test</directories>
  </syscheck>
</ossec_config>
FIMEOF

# Agent 재시작
echo 1 | sudo -S systemctl restart wazuh-agent
```

### 3.4 FIM 테스트

```bash
# secu 서버에서 테스트
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.1

# 테스트 디렉터리 생성
echo 1 | sudo -S mkdir -p /tmp/fim_test

# 파일 생성
echo 1 | sudo -S bash -c 'echo "original content" > /tmp/fim_test/test.txt'

# 잠시 대기 (초기 스캔)
sleep 10

# 파일 수정
echo 1 | sudo -S bash -c 'echo "modified content" >> /tmp/fim_test/test.txt'

# 새 파일 생성
echo 1 | sudo -S bash -c 'echo "suspicious" > /tmp/fim_test/webshell.php'
```

### 3.5 FIM 알림 확인

```bash
# siem 서버에서 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.100

echo 1 | sudo -S cat /var/ossec/logs/alerts/alerts.json | \
  python3 -c "
import sys, json
for line in sys.stdin:
    try:
        e = json.loads(line)
        r = e.get('rule',{})
        if 'syscheck' in str(r.get('groups',[])) or r.get('id','') in ['550','553','554']:
            sd = e.get('syscheck',{})
            print(f\"[FIM] {r.get('description','')} | File: {sd.get('path','?')}\")
            if sd.get('changed_attributes'):
                print(f\"  Changed: {sd['changed_attributes']}\")
    except: pass
" | tail -10
```

**예상 출력:**
```
[FIM] File added to the system. | File: /tmp/fim_test/test.txt
[FIM] Integrity checksum changed. | File: /tmp/fim_test/test.txt
  Changed: ['mtime', 'size', 'md5', 'sha1', 'sha256']
[FIM] File added to the system. | File: /tmp/fim_test/webshell.php
```

---

## 4. SCA (Security Configuration Assessment)

### 4.1 SCA란?

SCA는 시스템 설정이 보안 기준에 부합하는지 자동으로 검사하는 기능이다.

| 기준 | 설명 |
|------|------|
| CIS Benchmark | Center for Internet Security 벤치마크 |
| PCI-DSS | 카드결제 보안 표준 |
| HIPAA | 의료정보 보안 |

### 4.2 SCA 정책 파일 확인

```bash
echo 1 | sudo -S ls /var/ossec/ruleset/sca/
```

**예상 출력:**
```
cis_debian10.yml
cis_debian11.yml
cis_ubuntu22-04.yml
sca_unix_audit.yml
...
```

### 4.3 SCA 설정

ossec.conf:

```xml
<sca>
  <enabled>yes</enabled>
  <scan_on_start>yes</scan_on_start>
  <interval>12h</interval>
  <skip_nfs>yes</skip_nfs>
</sca>
```

### 4.4 SCA 결과 확인 (API)

```bash
# 토큰 획득
TOKEN=$(curl -s -u wazuh-wui:wazuh-wui -k -X POST \
  "https://10.20.30.100:55000/security/user/authenticate?raw=true")

# Agent 001(secu)의 SCA 결과
curl -s -k -X GET "https://10.20.30.100:55000/sca/001?pretty=true" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool | head -40
```

**예상 출력:**
```json
{
    "data": {
        "affected_items": [
            {
                "name": "CIS Benchmark for Debian/Ubuntu",
                "description": "CIS provides benchmarks...",
                "pass": 45,
                "fail": 12,
                "invalid": 3,
                "total_checks": 60,
                "score": 75
            }
        ]
    }
}
```

### 4.5 SCA 상세 결과

```bash
# 실패한 검사 항목 확인
curl -s -k -X GET \
  "https://10.20.30.100:55000/sca/001/checks/cis_debian11?result=failed&pretty=true" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool | head -60
```

**예상 출력 (일부):**
```json
{
    "id": 6012,
    "title": "Ensure SSH root login is disabled",
    "description": "PermitRootLogin should be set to no",
    "rationale": "Disabling root login forces...",
    "remediation": "Edit /etc/ssh/sshd_config and set: PermitRootLogin no",
    "result": "failed"
}
```

### 4.6 SCA 점검 항목 예시

```bash
# 직접 확인할 수 있는 보안 설정들
echo "=== SSH 설정 ==="
echo 1 | sudo -S grep "PermitRootLogin" /etc/ssh/sshd_config

echo "=== 패스워드 정책 ==="
echo 1 | sudo -S grep "PASS_MAX_DAYS" /etc/login.defs

echo "=== 불필요한 서비스 ==="
echo 1 | sudo -S systemctl list-unit-files --state=enabled | grep -E "telnet|rsh|rlogin"
```

---

## 5. Active Response (자동 대응)

### 5.1 Active Response란?

특정 알림이 발생하면 자동으로 대응 조치를 실행하는 기능이다.

```
알림 발생 (Level 7+) → Active Response 트리거
  → 대응 스크립트 실행 (IP 차단, 서비스 재시작 등)
  → 일정 시간 후 자동 해제 (timeout)
```

### 5.2 기본 제공 대응 스크립트

```bash
echo 1 | sudo -S ls /var/ossec/active-response/bin/
```

| 스크립트 | 설명 |
|----------|------|
| `firewall-drop` | iptables/nftables로 IP 차단 |
| `host-deny` | /etc/hosts.deny에 추가 |
| `disable-account` | 계정 비활성화 |
| `restart-wazuh` | Wazuh 재시작 |

### 5.3 Active Response 설정

ossec.conf (Manager측):

```xml
<!-- 대응 명령 정의 -->
<command>
  <name>firewall-drop</name>
  <executable>firewall-drop</executable>
  <timeout_allowed>yes</timeout_allowed>
</command>

<!-- 대응 규칙 -->
<active-response>
  <command>firewall-drop</command>
  <location>local</location>
  <rules_id>5712</rules_id>     <!-- SSH 브루트포스 -->
  <timeout>600</timeout>         <!-- 10분 후 자동 해제 -->
</active-response>

<active-response>
  <command>firewall-drop</command>
  <location>local</location>
  <level>12</level>              <!-- Level 12 이상 모든 알림 -->
  <timeout>3600</timeout>        <!-- 1시간 후 해제 -->
</active-response>
```

| 옵션 | 설명 |
|------|------|
| `command` | 실행할 대응 명령 |
| `location` | 실행 위치 (local/all/defined-agent) |
| `rules_id` | 트리거할 룰 ID |
| `level` | 트리거할 최소 레벨 |
| `timeout` | 대응 조치 지속 시간 (초) |

### 5.4 커스텀 Active Response 스크립트

```bash
# 커스텀 대응 스크립트 생성
echo 1 | sudo -S tee /var/ossec/active-response/bin/custom-block.sh << 'AREOF'
#!/bin/bash

LOCAL=$(dirname $0)
cd $LOCAL
cd ../

PWD=$(pwd)
ACTION=$1
USER=$2
IP=$3
ALERTID=$4
RULEID=$5

# 로그 기록
echo "$(date) $ACTION $IP Rule:$RULEID" >> /var/ossec/logs/active-responses.log

if [ "$ACTION" = "add" ]; then
    # IP 차단 (nftables)
    nft add element inet filter blocklist "{ $IP }" 2>/dev/null
    echo "$(date) BLOCKED $IP" >> /var/ossec/logs/active-responses.log
elif [ "$ACTION" = "delete" ]; then
    # IP 차단 해제
    nft delete element inet filter blocklist "{ $IP }" 2>/dev/null
    echo "$(date) UNBLOCKED $IP" >> /var/ossec/logs/active-responses.log
fi

exit 0
AREOF

echo 1 | sudo -S chmod 750 /var/ossec/active-response/bin/custom-block.sh
echo 1 | sudo -S chown root:wazuh /var/ossec/active-response/bin/custom-block.sh
```

### 5.5 Active Response 테스트

```bash
# 수동으로 Active Response 실행 (테스트)
echo 1 | sudo -S /var/ossec/active-response/bin/firewall-drop add - 192.168.99.99 1234 5712

# 차단 확인
echo 1 | sudo -S iptables -L -n | grep 192.168.99.99

# 수동 해제
echo 1 | sudo -S /var/ossec/active-response/bin/firewall-drop delete - 192.168.99.99 1234 5712
```

### 5.6 Active Response 로그 확인

```bash
echo 1 | sudo -S cat /var/ossec/logs/active-responses.log | tail -10
```

---

## 6. FIM + Active Response 연동

파일 변조 감지 시 자동 대응:

```xml
<!-- ossec.conf에 추가 -->
<command>
  <name>notify-admin</name>
  <executable>custom-notify.sh</executable>
  <timeout_allowed>no</timeout_allowed>
</command>

<active-response>
  <command>notify-admin</command>
  <location>server</location>
  <rules_id>550,553,554</rules_id>  <!-- FIM 알림 -->
</active-response>
```

---

## 7. 종합 실습: 침입 시나리오

### 시나리오: SSH 브루트포스 → 로그인 성공 → 파일 변조

```bash
# 1단계: 브루트포스 시뮬레이션 (secu에서 siem으로)
for i in $(seq 1 10); do
  sshpass -p wrong ssh -o StrictHostKeyChecking=no -o ConnectTimeout=2 \
    wronguser@10.20.30.100 2>/dev/null
done

# 2단계: 정상 로그인
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.100

# 3단계: 파일 변조
echo 1 | sudo -S bash -c 'echo "hacked" >> /tmp/fim_test/test.txt'
```

### 기대되는 Wazuh 알림 흐름:

```
1. Rule 5710 (Level 5): SSH 로그인 실패 x 10
2. Rule 5712 (Level 10): SSH 브루트포스 탐지
3. Active Response: 공격자 IP 차단
4. Rule 5715 (Level 3): SSH 로그인 성공
5. Rule 100005 (Level 12): 실패 후 성공 - 침입 의심
6. Rule 550 (Level 7): FIM - 파일 변경 감지
```

---

## 8. 실습 과제

### 과제 1: FIM 설정

1. secu 서버에서 `/etc/ssh/sshd_config` 파일을 FIM 감시 대상으로 추가
2. 파일을 수정하고 FIM 알림이 발생하는지 확인
3. 변경 내용(diff)이 기록되는지 확인

### 과제 2: SCA 분석

1. secu 서버의 SCA 결과를 조회
2. 실패한 항목 3개를 선택하여 원인과 조치 방안을 작성
3. 1개 항목을 실제로 수정하고 SCA를 재실행

### 과제 3: Active Response

1. SSH 브루트포스 탐지 시 IP를 차단하는 Active Response를 설정
2. 브루트포스를 시뮬레이션하여 자동 차단이 동작하는지 확인
3. timeout 후 자동 해제되는지 확인

---

## 9. 핵심 정리

| 개념 | 설명 |
|------|------|
| FIM | 파일 무결성 모니터링 (변경 탐지) |
| realtime | inotify 기반 실시간 감시 |
| whodata | audit 기반 변경자 추적 |
| report_changes | 파일 내용 diff 기록 |
| SCA | 보안 설정 자동 평가 (CIS 기반) |
| Active Response | 알림 기반 자동 대응 |
| firewall-drop | IP 차단 대응 스크립트 |
| timeout | 자동 대응 지속 시간 |

---

## 다음 주 예고

Week 12에서는 OpenCTI를 다룬다:
- 위협 인텔리전스 플랫폼 설치와 구성
- STIX/TAXII 기초
- 데이터 소스 연동


---

## 심화 학습: 개념 확장

### 핵심 개념 상세 해설

이 주차에서 다루는 핵심 개념들을 더 깊이 살펴본다.

#### 개념 1: 동작 원리 (Course 2)

이 주차에서 다루는 기술의 동작 방식을 단계별로 분해하여 이해한다.

```
[1단계] 입력/요청 → 시스템이 데이터를 수신
[2단계] 처리 → 내부 로직에 의한 데이터 처리
[3단계] 출력/응답 → 결과 반환 또는 상태 변경
[4단계] 기록 → 로그/증적 생성
```

> **왜 이 순서가 중요한가?**
> 각 단계에서 보안 검증이 누락되면 취약점이 발생한다.
> 1단계: 입력값 검증 미흡 → Injection
> 2단계: 인가 확인 누락 → Broken Access Control
> 3단계: 에러 정보 노출 → Information Disclosure
> 4단계: 로깅 실패 → Monitoring Failures

#### 개념 2: 보안 관점에서의 위험 분석

| 위험 요소 | 발생 조건 | 영향도 | 대응 방안 |
|----------|---------|--------|---------|
| 설정 미흡 | 기본 설정 사용 | 높음 | 보안 하드닝 가이드 적용 |
| 패치 누락 | 업데이트 미적용 | 높음 | 정기 패치 관리 프로세스 |
| 접근 제어 부재 | 인증/인가 미구현 | 매우 높음 | RBAC, MFA 적용 |
| 로깅 미흡 | 감사 로그 미수집 | 중간 | SIEM 연동, 로그 정책 |

#### 개념 3: 실제 사례 분석

**사례 1: 유사 취약점이 실제 피해로 이어진 경우**

실제 보안 사고에서 이 주차의 주제가 어떻게 악용되었는지 살펴본다.
공격자는 동일한 기법을 사용하여 대규모 데이터 유출, 서비스 장애, 금전적 피해를 초래하였다.

**교훈:**
- 기본적인 보안 조치의 중요성
- 탐지 체계의 필수성
- 사고 대응 절차의 사전 수립 필요성

### 도구 비교표

| 도구 | 용도 | 장점 | 단점 | 라이선스 |
|------|------|------|------|---------|
| 도구 A | 기본 점검 | 간편, 빠름 | 기능 제한 | 오픈소스 |
| 도구 B | 심층 분석 | 상세 결과 | 학습 곡선 | 상용/무료 |
| 도구 C | 자동화 | CI/CD 연동 | 오탐 가능 | 오픈소스 |


---

## 보충 실습

### 보충 실습 1: 기본 동작 확인

이론에서 배운 내용을 직접 확인하는 기초 실습이다.

```bash
# Step 1: 현재 상태 확인
echo "=== 현재 상태 ==="
# (해당 주차에 맞는 확인 명령)

# Step 2: 설정/변경 적용
echo "=== 변경 적용 ==="
# (해당 주차에 맞는 실습 명령)

# Step 3: 결과 검증
echo "=== 결과 확인 ==="
# (변경 결과 확인 명령)
```

> **트러블슈팅:**
> - 명령이 실패하면: 권한(sudo), 경로, 서비스 상태를 먼저 확인
> - 예상과 다른 결과: 이전 실습의 설정이 남아있을 수 있으므로 초기화 후 재시도
> - 타임아웃: 네트워크 연결 또는 서비스 가동 상태 확인

### 보충 실습 2: 탐지/모니터링 관점

공격자가 아닌 **방어자 관점**에서 동일한 활동을 모니터링하는 실습이다.

```bash
# siem 서버에서 관련 로그 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100 \
  "sudo cat /var/ossec/logs/alerts/alerts.json | tail -5" 2>/dev/null

# Suricata 알림 확인 (해당 시)
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \
  "sudo tail -20 /var/log/suricata/fast.log" 2>/dev/null
```

> **왜 방어자 관점도 배우는가?**
> 공격 기법만 알면 "스크립트 키디"에 불과하다.
> 공격이 어떻게 탐지되는지 이해해야 진정한 보안 전문가이다.
> 이 과목의 모든 공격 실습에는 대응하는 탐지/방어 관점이 포함된다.

### 보충 실습 3: OpsClaw 자동화

이번 주차의 핵심 실습을 OpsClaw execute-plan으로 자동화한다.

```bash
# 프로젝트 생성 (이번 주차용)
RESULT=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"name":"weekXX-lab","request_text":"이번 주차 실습 자동화","master_mode":"external"}')
PID=$(echo $RESULT | python3 -c "import sys,json; print(json.load(sys.stdin)['project']['id'])")

# Stage 전환
curl -s -X POST "http://localhost:8000/projects/$PID/plan" -H "X-API-Key: opsclaw-api-key-2026" > /dev/null
curl -s -X POST "http://localhost:8000/projects/$PID/execute" -H "X-API-Key: opsclaw-api-key-2026" > /dev/null

# 실습 태스크 실행 (해당 주차에 맞게 수정)
curl -s -X POST "http://localhost:8000/projects/$PID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "tasks": [
      {"order":1,"title":"실습 태스크 1","instruction_prompt":"echo 실습1","risk_level":"low","subagent_url":"http://localhost:8002"},
      {"order":2,"title":"실습 태스크 2","instruction_prompt":"echo 실습2","risk_level":"low","subagent_url":"http://10.20.30.80:8002"}
    ],
    "subagent_url":"http://localhost:8002",
    "parallel":true
  }'

# Evidence 확인
curl -s "http://localhost:8000/projects/$PID/evidence/summary" \
  -H "X-API-Key: opsclaw-api-key-2026" | python3 -m json.tool
```


---

## 자가 점검 퀴즈 (10문항)

이번 주차의 핵심 내용을 점검한다. 8/10 이상 정답을 목표로 한다.

**Q1.** 이번 주차 "Week 11: Wazuh SIEM (3) — FIM, SCA, Active Response"의 핵심 목적은 무엇인가?
- (a) 네트워크 속도 향상  (b) **보안 솔루션 기법/개념의 이해와 실습**  (c) 데이터베이스 관리  (d) UI 디자인

**Q2.** 이 주제에서 방화벽/IPS의 역할은?
- (a) 성능 최적화  (b) 비용 절감  (c) **체계적 분류와 대응 기준 제공**  (d) 사용자 편의

**Q3.** 실습에서 사용한 주요 도구/명령어의 1차 목적은?
- (a) 파일 복사  (b) **SIEM 수행 및 결과 확인**  (c) 메모리 관리  (d) 화면 출력

**Q4.** OpsClaw를 통해 실습을 실행하는 가장 큰 이점은?
- (a) 속도  (b) **모든 실행의 자동 증적(evidence) 기록**  (c) 무료  (d) 간편함

**Q5.** 이 주제의 보안 위험이 높은 이유는?
- (a) 비용이 많이 들어서  (b) 복잡해서  (c) **악용 시 시스템/데이터에 직접적 피해**  (d) 법적 문제

**Q6.** 방어/대응의 핵심 원칙은?
- (a) 모든 트래픽 차단  (b) **최소 권한 + 탐지 + 대응의 조합**  (c) 서버 재시작  (d) 비밀번호 변경

**Q7.** 실습 결과를 분석할 때 가장 먼저 확인해야 하는 것은?
- (a) 서버 이름  (b) **exit_code (성공/실패 여부)**  (c) 파일 크기  (d) 날짜

**Q8.** 이 주제와 관련된 MITRE ATT&CK 전술은?
- (a) Impact만  (b) Reconnaissance만  (c) **주제에 해당하는 전술(들)**  (d) 해당 없음

**Q9.** 실무에서 이 기법/도구를 사용할 때 가장 주의할 점은?
- (a) 속도  (b) **법적 허가와 범위 준수**  (c) 비용  (d) 보고서 양식

**Q10.** 다음 주차와의 연결 포인트는?
- (a) 관련 없음  (b) **이번 주 결과를 다음 주에서 활용/심화**  (c) 완전히 다른 주제  (d) 복습만

**정답:** Q1:b, Q2:c, Q3:b, Q4:b, Q5:c, Q6:b, Q7:b, Q8:c, Q9:b, Q10:b

---

## 과제 (다음 주까지)

### 과제 1: 이론 정리 보고서 (30점)

이번 주차의 핵심 개념을 자신의 말로 정리하라.

| 항목 | 배점 |
|------|------|
| 핵심 개념 정의 및 설명 | 10점 |
| 실습 결과 캡처 및 해석 | 10점 |
| 보안 관점 분석 (공격↔방어) | 10점 |

### 과제 2: 실습 수행 보고서 (40점)

이번 주차의 모든 실습을 수행하고 결과를 보고서로 작성하라.

| 항목 | 배점 |
|------|------|
| 실습 명령어 및 실행 결과 캡처 | 15점 |
| 결과 해석 및 보안 의미 분석 | 15점 |
| 트러블슈팅 경험 (있는 경우) | 10점 |

### 과제 3: OpsClaw 자동화 (30점)

이번 주차의 핵심 실습을 OpsClaw execute-plan으로 자동화하라.

| 항목 | 배점 |
|------|------|
| 프로젝트 생성 + stage 전환 | 5점 |
| execute-plan 태스크 설계 (3개 이상) | 10점 |
| evidence/summary 결과 | 5점 |
| replay 타임라인 결과 | 5점 |
| 자동화의 이점 분석 (직접 실행 대비) | 5점 |

**제출:** 보고서(PDF 또는 MD) + OpsClaw project_id


---

## 검증 체크리스트

이번 주차의 학습을 완료하려면 다음 항목을 모두 확인하라:

- [ ] 이론 강의 내용 이해 (핵심 용어 설명 가능)
- [ ] 기본 실습 모두 수행 완료
- [ ] 보충 실습 1 (기본 동작 확인) 완료
- [ ] 보충 실습 2 (탐지/모니터링 관점) 수행
- [ ] 보충 실습 3 (OpsClaw 자동화) 수행
- [ ] 자가 점검 퀴즈 8/10 이상 정답
- [ ] 과제 1 (이론 정리) 작성
- [ ] 과제 2 (실습 보고서) 작성
- [ ] 과제 3 (OpsClaw 자동화) 완료

