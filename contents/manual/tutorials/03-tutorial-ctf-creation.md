# 튜토리얼: 교안 기반 CTF 문제 만들기

## 학습 목표

이 튜토리얼을 완료하면 다음을 할 수 있다.

- 교육과정 교안에서 CTF 문제 주제를 선정한다
- YAML 형식으로 CTF 문제를 정의한다
- register_challenges.py 스크립트로 CTFd에 등록한다
- OpsClaw Evidence로 FLAG를 자동 검증한다
- 문제의 난이도와 배점을 적절히 설정한다

**소요 시간:** 약 40분
**난이도:** 초급~중급

---

## 사전 준비

### 필요 환경

```bash
# CTFd 실행 확인
curl -s http://localhost:8080/api/v1/challenges -H "Authorization: Token <CTFD_TOKEN>" | head -5

# OpsClaw Manager 실행 확인
curl -s http://localhost:8000/health

# API Key 설정
export OPSCLAW_API_KEY=opsclaw-api-key-2026
export CTFD_TOKEN="<CTFd API Token>"
export CTFD_URL="http://localhost:8080"
```

### CTFd API Token 발급

1. CTFd 웹 UI (http://localhost:8080)에 관리자로 로그인
2. Settings → Access Tokens → Generate
3. Token을 복사하여 환경변수에 설정

---

## 단계 1: 교안에서 주제 선정

### 1.1 교안 확인

Course 1 Week 01 교안을 읽고 CTF 문제로 변환할 기술 포인트를 선정한다.

```bash
# 교안 목록 확인
ls contents/education/course1-attack-techniques/

# Week 01 교안 내용 확인
cat contents/education/course1-attack-techniques/week01-introduction.md
```

### 1.2 주제 선정 기준

CTF 문제로 적합한 기술 포인트:

| 기준 | 적합 | 부적합 |
|------|------|--------|
| 실행 가능성 | 명령어로 확인 가능한 것 | 이론만 있는 것 |
| 답이 명확함 | 숫자, 문자열 등 정확한 답 | 주관식 서술 |
| 실습 환경 | v-secu/v-web/v-siem에서 가능 | 외부 서비스 필요 |
| 교육 효과 | 실습 후 개념 이해 향상 | 단순 암기 |

### 1.3 선정 예시

Week 01 "정보 수집과 정찰" 교안에서 다음 5개 주제를 선정한다.

```
1. 서버 열린 포트 확인 (ss/nmap)
2. 서비스 버전 확인 (banner grabbing)
3. nftables 방화벽 규칙 분석
4. Wazuh 알림 레벨 분석
5. 네트워크 인터페이스 정보 수집
```

---

## 단계 2: YAML 문제 정의

### 2.1 YAML 파일 구조

```yaml
# contents/ctf/course1/week01/challenges.yaml

# 메타데이터
course: "Course 1 - Attack Techniques"
week: 1
topic: "정보 수집과 정찰"
author: "OpsClaw Education Team"
created: "2026-03-30"

# 문제 목록
challenges:
  - name: "port-scan-basic"
    # ... (아래에서 상세 설명)
```

### 2.2 문제 1: 포트 스캔 기초

```yaml
  - name: "port-scan-basic"
    category: "Course1-Week01-Recon"
    description: |
      ## 포트 스캔 기초

      v-secu 서버(192.168.0.108)에서 현재 열려 있는 TCP 포트의 **수**를 확인하세요.

      ### 조건
      - LISTEN 상태인 TCP 포트만 세세요
      - IPv4와 IPv6 모두 포함합니다

      ### 힌트
      `ss` 또는 `netstat` 명령을 사용할 수 있습니다.

      ### FLAG 형식
      열린 포트 수를 FLAG{숫자} 형식으로 제출하세요.
      예: 3개라면 FLAG{3}
    value: 100
    type: "standard"
    flag: "FLAG{6}"
    state: "visible"
    hints:
      - content: "ss -tlnp 명령을 사용해보세요"
        cost: 10
      - content: "grep LISTEN으로 필터링하세요"
        cost: 20
    tags: ["reconnaissance", "network", "beginner"]
    files: []
    opsclaw_verify:
      command: "ss -tlnp | grep LISTEN | wc -l"
      target: "http://192.168.0.108:8002"
      expected_exit_code: 0
      expected_contains: "6"
```

### 2.3 문제 2: 서비스 버전 확인

```yaml
  - name: "service-version-banner"
    category: "Course1-Week01-Recon"
    description: |
      ## 서비스 버전 확인

      v-web 서버(192.168.0.110)에서 HTTP 서비스의 **Server 헤더** 값을 확인하세요.

      ### 조건
      - curl을 사용하여 HTTP 응답 헤더에서 Server 필드를 추출하세요
      - 전체 Server 헤더 값이 FLAG입니다

      ### FLAG 형식
      FLAG{Server헤더값}
      예: FLAG{nginx/1.24.0}
    value: 150
    type: "standard"
    flag: "FLAG{Apache/2.4.62 (Debian)}"
    hints:
      - content: "curl -I 명령으로 헤더를 확인할 수 있습니다"
        cost: 15
      - content: "curl -sI http://localhost/ | grep -i '^Server:'"
        cost: 30
    tags: ["reconnaissance", "web", "beginner"]
    opsclaw_verify:
      command: "curl -sI http://localhost/ | grep -i '^Server:' | cut -d' ' -f2-"
      target: "http://192.168.0.110:8002"
      expected_contains: "Apache"
```

### 2.4 문제 3: 방화벽 규칙 분석

```yaml
  - name: "nft-rule-analysis"
    category: "Course1-Week01-Recon"
    description: |
      ## 방화벽 규칙 분석

      v-secu 서버의 nftables 규칙을 분석하세요.
      input 체인에서 **drop** 동작이 설정된 규칙의 수를 찾으세요.

      ### FLAG 형식
      FLAG{숫자}
    value: 200
    type: "standard"
    flag: "FLAG{5}"
    hints:
      - content: "nft list chain inet filter input 명령을 사용하세요"
        cost: 20
      - content: "grep -c drop으로 세세요"
        cost: 30
    tags: ["firewall", "nftables", "intermediate"]
    opsclaw_verify:
      command: "nft list chain inet filter input | grep -c drop"
      target: "http://192.168.0.108:8002"
      expected_contains: "5"
```

### 2.5 문제 4: Wazuh 알림 분석

```yaml
  - name: "wazuh-alert-analysis"
    category: "Course1-Week01-Recon"
    description: |
      ## Wazuh 알림 분석

      v-siem 서버의 Wazuh에서 최근 알림 중
      **Level 10 이상**인 알림의 수를 확인하세요.

      ### 조건
      - /var/ossec/logs/alerts/alerts.json의 최근 500줄을 분석하세요
      - rule.level >= 10인 알림만 세세요

      ### FLAG 형식
      FLAG{숫자}
    value: 250
    type: "standard"
    flag: "FLAG{12}"
    hints:
      - content: "Python의 json 모듈로 파싱할 수 있습니다"
        cost: 25
      - content: "tail -500 alerts.json | python3 -c ..."
        cost: 40
    tags: ["siem", "wazuh", "intermediate"]
    opsclaw_verify:
      command: "tail -500 /var/ossec/logs/alerts/alerts.json | python3 -c \"import json,sys; alerts=[json.loads(l) for l in sys.stdin if l.strip()]; print(sum(1 for a in alerts if a.get('rule',{}).get('level',0)>=10))\""
      target: "http://192.168.0.109:8002"
      expected_exit_code: 0
```

### 2.6 문제 5: 네트워크 정보 수집

```yaml
  - name: "network-info-gather"
    category: "Course1-Week01-Recon"
    description: |
      ## 네트워크 인터페이스 정보

      v-secu 서버의 주 네트워크 인터페이스(eth0 또는 ens*)의
      **서브넷 마스크 비트 수**(CIDR 표기의 / 뒤 숫자)를 확인하세요.

      ### FLAG 형식
      FLAG{숫자}
      예: 서브넷이 /24이면 FLAG{24}
    value: 100
    type: "standard"
    flag: "FLAG{24}"
    hints:
      - content: "ip addr show 명령을 사용하세요"
        cost: 10
    tags: ["network", "beginner"]
    opsclaw_verify:
      command: "ip -4 addr show | grep 'inet ' | grep -v '127.0.0' | head -1 | awk '{print $2}' | cut -d/ -f2"
      target: "http://192.168.0.108:8002"
      expected_contains: "24"
```

---

## 단계 3: 문제 검증 (OpsClaw로 사전 테스트)

문제를 등록하기 전에 FLAG가 정확한지 OpsClaw로 검증한다.

### 3.1 검증 프로젝트 생성

```bash
oc -X POST http://localhost:8000/projects \
  -d '{
    "name": "ctf-verify-c1w01",
    "request_text": "Course1 Week01 CTF 문제 FLAG 검증",
    "master_mode": "external"
  }'
PID="<project_id>"
oc -X POST http://localhost:8000/projects/$PID/plan
oc -X POST http://localhost:8000/projects/$PID/execute
```

### 3.2 각 문제 FLAG 검증

```bash
oc -X POST http://localhost:8000/projects/$PID/execute-plan \
  -d '{
    "parallel": true,
    "tasks": [
      {
        "order": 1,
        "title": "문제1 FLAG 검증: port-scan-basic",
        "instruction_prompt": "ss -tlnp | grep LISTEN | wc -l",
        "risk_level": "low",
        "subagent_url": "http://192.168.0.108:8002"
      },
      {
        "order": 2,
        "title": "문제2 FLAG 검증: service-version-banner",
        "instruction_prompt": "curl -sI http://localhost/ | grep -i '\"'\"'Server:'\"'\"' | cut -d'\"'\"' '\"'\"' -f2-",
        "risk_level": "low",
        "subagent_url": "http://192.168.0.110:8002"
      },
      {
        "order": 3,
        "title": "문제3 FLAG 검증: nft-rule-analysis",
        "instruction_prompt": "nft list chain inet filter input | grep -c drop",
        "risk_level": "low",
        "subagent_url": "http://192.168.0.108:8002"
      },
      {
        "order": 4,
        "title": "문제4 FLAG 검증: wazuh-alert-analysis",
        "instruction_prompt": "tail -500 /var/ossec/logs/alerts/alerts.json | python3 -c \"import json,sys; alerts=[json.loads(l) for l in sys.stdin if l.strip()]; print(sum(1 for a in alerts if a.get('\"'\"'rule'\"'\"',{}).get('\"'\"'level'\"'\"',0)>=10))\"",
        "risk_level": "low",
        "subagent_url": "http://192.168.0.109:8002"
      },
      {
        "order": 5,
        "title": "문제5 FLAG 검증: network-info-gather",
        "instruction_prompt": "ip -4 addr show | grep '\"'\"'inet '\"'\"' | grep -v '\"'\"'127.0.0'\"'\"' | head -1 | awk '\"'\"'{print $2}'\"'\"' | cut -d/ -f2",
        "risk_level": "low",
        "subagent_url": "http://192.168.0.108:8002"
      }
    ]
  }'
```

### 3.3 검증 결과 확인

```bash
oc http://localhost:8000/projects/$PID/evidence/summary
```

각 task의 stdout이 YAML에 정의한 FLAG 값과 일치하는지 확인한다.
일치하지 않으면 YAML의 flag 값을 수정한다.

---

## 단계 4: CTFd에 등록

### 4.1 register_challenges.py 실행

```bash
python3 scripts/register_challenges.py \
  --ctfd-url $CTFD_URL \
  --token $CTFD_TOKEN \
  --yaml contents/ctf/course1/week01/challenges.yaml
```

**스크립트 동작 과정:**

```
1. YAML 파일 파싱
2. 각 challenge에 대해:
   a. POST /api/v1/challenges → challenge 생성
   b. POST /api/v1/flags     → FLAG 등록
   c. POST /api/v1/hints     → 힌트 등록 (있으면)
   d. POST /api/v1/tags      → 태그 등록 (있으면)
3. 결과 요약 출력
```

### 4.2 수동 등록 (스크립트 없이)

CTFd REST API를 직접 호출하여 등록할 수도 있다.

```bash
# 문제 생성
CHALLENGE_ID=$(curl -s -X POST $CTFD_URL/api/v1/challenges \
  -H "Authorization: Token $CTFD_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "port-scan-basic",
    "category": "Course1-Week01-Recon",
    "description": "v-secu 서버에서 열려 있는 TCP 포트 수를 확인하세요.\nFLAG{숫자}",
    "value": 100,
    "type": "standard",
    "state": "visible"
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['data']['id'])")

echo "Challenge ID: $CHALLENGE_ID"

# FLAG 등록
curl -s -X POST $CTFD_URL/api/v1/flags \
  -H "Authorization: Token $CTFD_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"challenge_id\": $CHALLENGE_ID,
    \"content\": \"FLAG{6}\",
    \"type\": \"static\"
  }"

# 힌트 등록
curl -s -X POST $CTFD_URL/api/v1/hints \
  -H "Authorization: Token $CTFD_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"challenge_id\": $CHALLENGE_ID,
    \"content\": \"ss -tlnp 명령을 사용해보세요\",
    \"cost\": 10
  }"

# 태그 등록
curl -s -X POST $CTFD_URL/api/v1/tags \
  -H "Authorization: Token $CTFD_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"challenge_id\": $CHALLENGE_ID,
    \"value\": \"reconnaissance\"
  }"
```

---

## 단계 5: 학생 실습 시뮬레이션

학생이 문제를 풀 때의 과정을 시뮬레이션한다.

### 5.1 학생 프로젝트 생성

```bash
oc -X POST http://localhost:8000/projects \
  -d '{
    "name": "student01-c1w01",
    "request_text": "Course1 Week01 CTF 실습",
    "master_mode": "external"
  }'
STUDENT_PID="<project_id>"
oc -X POST http://localhost:8000/projects/$STUDENT_PID/plan
oc -X POST http://localhost:8000/projects/$STUDENT_PID/execute
```

### 5.2 학생이 문제를 풀다

```bash
# 문제 1: 포트 스캔
oc -X POST http://localhost:8000/projects/$STUDENT_PID/dispatch \
  -d '{
    "command": "ss -tlnp | grep LISTEN | wc -l",
    "subagent_url": "http://192.168.0.108:8002"
  }'
# → stdout: "6"
# → FLAG{6}을 CTFd에 제출
```

### 5.3 Evidence 기반 자동 검증

```bash
# validate/check로 FLAG 자동 검증
oc -X POST http://localhost:8000/projects/$STUDENT_PID/validate/check \
  -d '{
    "validator_name": "ctf_port_scan",
    "command": "ss -tlnp | grep LISTEN | wc -l",
    "expected_contains": "6",
    "expected_exit_code": 0,
    "subagent_url": "http://192.168.0.108:8002"
  }'

# 응답
# {"status": "ok", "result": {"validation_status": "passed", ...}}
```

### 5.4 학생 PoW 블록 확인

```bash
# 학생의 작업 증명 (변조 불가)
oc http://localhost:8000/projects/$STUDENT_PID/pow
```

---

## 단계 6: 전체 과정 일괄 등록

여러 주차의 문제를 한 번에 등록하는 방법이다.

### 6.1 디렉토리 구조

```
contents/ctf/
├── course1/
│   ├── week01/
│   │   └── challenges.yaml    # 5문제
│   ├── week02/
│   │   └── challenges.yaml    # 5문제
│   └── ...
├── course2/
│   └── ...
└── ...
```

### 6.2 일괄 등록 스크립트

```bash
#!/bin/bash
# bulk_register.sh — 전체 CTF 문제 일괄 등록

CTFD_URL="http://localhost:8080"
CTFD_TOKEN="<token>"

for course_dir in contents/ctf/course*/; do
  course=$(basename $course_dir)
  echo "=== Registering $course ==="

  for week_dir in $course_dir/week*/; do
    yaml="$week_dir/challenges.yaml"
    if [ -f "$yaml" ]; then
      echo "  Processing: $yaml"
      python3 scripts/register_challenges.py \
        --ctfd-url $CTFD_URL \
        --token $CTFD_TOKEN \
        --yaml "$yaml"
    fi
  done
done

echo "Registration complete!"
```

---

## 문제 설계 가이드라인

### 난이도별 배점

| 난이도 | 배점 | 교안 범위 | 예시 |
|--------|------|----------|------|
| Beginner | 100-150 | Week 01-03 | 단순 명령 실행, 결과 확인 |
| Intermediate | 200-300 | Week 04-06 | 조합 명령, 분석 |
| Advanced | 300-400 | Week 07-09 | 스크립트 작성, 취약점 분석 |
| Expert | 400-500 | Week 10-12 | 복합 시나리오 |
| Challenge | 500+ | Week 13-15 | 종합 과제 |

### FLAG 형식 규칙

```
FLAG{답}

형식 예시:
  FLAG{6}                        ← 숫자
  FLAG{Apache/2.4.62 (Debian)}   ← 문자열
  FLAG{192.168.0.108}            ← IP 주소
  FLAG{root:x:0:0}               ← 파일 내용
  FLAG{sha256:abc123...}         ← 해시값
```

### 좋은 CTF 문제의 특징

1. **명확한 지시**: 학생이 무엇을 해야 하는지 정확히 이해할 수 있다
2. **유일한 답**: 정답이 하나뿐이다 (모호하지 않음)
3. **교육 효과**: 문제를 풀면서 기술을 배울 수 있다
4. **단계적 힌트**: 힌트가 점진적으로 도움을 준다
5. **검증 가능**: OpsClaw Evidence로 자동 검증이 가능하다

### 피해야 할 문제 유형

- 동적으로 변하는 값을 FLAG로 사용 (로그 타임스탬프 등)
- 외부 서비스에 의존하는 문제
- 서버 상태를 변경해야 하는 문제 (다른 학생에게 영향)
- 모호한 FLAG 형식 (대소문자 혼동 등)

---

## 최종 확인 체크리스트

```
[ ] YAML 문법 오류 없는가
[ ] 모든 FLAG가 OpsClaw로 검증되었는가
[ ] 카테고리와 태그가 일관성 있는가
[ ] 힌트가 적절한가 (너무 쉽지도, 어렵지도 않은가)
[ ] 배점이 난이도에 맞는가
[ ] 문제 설명이 한국어로 명확한가
[ ] CTFd에 등록 후 웹 UI에서 정상 표시되는가
[ ] 학생 시뮬레이션으로 풀이가 가능한가
```
