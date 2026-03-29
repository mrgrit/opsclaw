# OpsClaw 보안 교육 플랫폼 가이드

## 1. 개요

OpsClaw는 IT 운영 자동화 플랫폼이면서 동시에 **보안 교육 플랫폼**으로 활용된다.
실제 인프라 운영 도구 위에 교육 파이프라인을 구축하여,
학생들이 가상이 아닌 **실제 시스템에서** 보안 실습을 수행하고
그 증적이 블록체인(PoW)으로 기록되는 구조이다.

---

## 2. 4계층 교육 파이프라인

OpsClaw 교육은 4개 계층이 유기적으로 연결된다.

```
┌──────────────────────────────────────────────────────────┐
│  Layer 1: System (OpsClaw 플랫폼)                         │
│  실제 서버 인프라, Evidence 기록, PoW 체인                  │
└────────────────────────┬─────────────────────────────────┘
                         │ 기술 내용 추출
                         ▼
┌──────────────────────────────────────────────────────────┐
│  Layer 2: Education (교육과정)                             │
│  8개 과정 x 15주 = 120개 강의                              │
│  각 교안에 OpsClaw 실습 명령 포함                           │
└────────────────────────┬─────────────────────────────────┘
                         │ 기술 시나리오 스토리 변환
                         ▼
┌──────────────────────────────────────────────────────────┐
│  Layer 3: Novel (기술 소설)                                │
│  10권 x 12화 = 120화                                      │
│  각 화에 1개 강의의 기술 내용이 서사에 녹아있음               │
└────────────────────────┬─────────────────────────────────┘
                         │ 핵심 기술 포인트 추출
                         ▼
┌──────────────────────────────────────────────────────────┐
│  Layer 4: CTF (Capture The Flag)                          │
│  교안/소설의 기술 내용을 실습 문제로 변환                    │
│  CTFd 플랫폼에서 플래그 제출 + OpsClaw Evidence 자동 검증   │
└──────────────────────────────────────────────────────────┘
```

**계층간 연결 원리:**

- 교안 Week03 "nftables 기본 체인 설정" 에서 nftables 개념을 배운다
- 소설 Vol.1 Ch.3에서 주인공이 nftables로 침입을 막는 장면이 나온다
- CTF 문제 "nft-chain-basic"에서 학생이 직접 nftables 규칙을 작성한다
- OpsClaw가 학생의 실행 결과를 Evidence로 기록하고 FLAG를 검증한다

---

## 3. 8개 교육과정 개요

### 3.1 과정 목록

| 과정 | 코드 | 주제 | 대상 |
|------|------|------|------|
| Course 1 | attack-techniques | 공격 기법과 침투 테스트 | Red Team 입문자 |
| Course 2 | defense-strategies | 방어 전략과 대응 체계 | Blue Team 입문자 |
| Course 3 | compliance-audit | 컴플라이언스와 감사 | 보안 관리자 |
| Course 4 | soc-operations | SOC 운영과 위협 분석 | SOC 분석가 |
| Course 5 | cloud-security | 클라우드 보안 | 클라우드 엔지니어 |
| Course 6 | ai-security | AI/ML 보안 | AI 개발자 |
| Course 7 | ai-safety | AI 안전성과 윤리 | AI 연구자 |
| Course 8 | advanced-topics | 고급 주제와 실전 | 시니어 엔지니어 |

### 3.2 과정별 15주 구성 패턴

각 과정은 동일한 15주 구성을 따른다.

```
Week 01-03: 기초 개념 및 환경 구축
Week 04-06: 핵심 기술 심화
Week 07-09: 실전 시나리오 및 도구 활용
Week 10-12: 고급 기법 및 자동화
Week 13-14: 프로젝트 실습 및 팀 연습
Week 15:    종합 평가 및 리뷰
```

### 3.3 교안 구조 (각 강의)

```
# Week XX: 강의 제목

## 학습 목표
- 목표 1
- 목표 2

## 이론
### 개념 설명
### 기술 배경

## 실습
### OpsClaw 실습 명령
```bash
opsclaw run "nftables 규칙 확인" --target v-secu
```

### 수동 실습 (참고용)
```bash
sudo nft list ruleset
```

## 핵심 정리
## 참고 자료
```

---

## 4. 120개 강의 디렉토리 구조

```
contents/
├── education/
│   ├── course1-attack-techniques/
│   │   ├── week01-introduction.md
│   │   ├── week02-reconnaissance.md
│   │   ├── ...
│   │   └── week15-final-assessment.md
│   ├── course2-defense-strategies/
│   │   ├── week01-introduction.md
│   │   └── ...
│   ├── course3-compliance-audit/
│   ├── course4-soc-operations/
│   ├── course5-cloud-security/
│   ├── course6-ai-security/
│   ├── course7-ai-safety/
│   └── course8-advanced-topics/
├── novel/
│   ├── vol01/
│   │   ├── ch01.md
│   │   ├── ch02.md
│   │   └── ... (12화)
│   ├── vol02/
│   └── ... (10권)
└── ctf/
    ├── course1/
    │   ├── week01/
    │   │   ├── challenges.yaml
    │   │   └── flag_verify.sh
    │   └── ...
    └── ...
```

---

## 5. 기술 소설 통합

### 5.1 10권 구성

| 권 | 제목 | 교육과정 대응 | 핵심 주제 |
|----|------|--------------|----------|
| Vol.1 | 침입의 시작 | Course 1 (Week 1-12) | 공격 기법, 초기 침투 |
| Vol.2 | 방어선 | Course 2 (Week 1-12) | 방어 체계, 대응 |
| Vol.3 | 규정의 벽 | Course 3 (Week 1-12) | 컴플라이언스, 감사 |
| Vol.4 | 경계의 눈 | Course 4 (Week 1-12) | SOC 운영, 위협 분석 |
| Vol.5 | 구름 위의 전쟁 | Course 5 (Week 1-12) | 클라우드 보안 |
| Vol.6 | 기계의 적 | Course 6 (Week 1-12) | AI/ML 보안 |
| Vol.7 | 통제의 경계 | Course 7 (Week 1-12) | AI 안전성 |
| Vol.8 | 최전선 | Course 8 (Week 1-12) | 고급 실전 |
| Vol.9 | 수렴 | 과정 통합 | 전체 과정 통합 시나리오 |
| Vol.10 | 새벽 | 과정 통합 | 미래 전망, 에필로그 |

### 5.2 기술 내용 삽입 원칙

소설에서 기술 내용은 다음 방식으로 자연스럽게 삽입된다.

1. **캐릭터 대화**: 멘토가 주인공에게 개념을 설명하는 장면
2. **행동 묘사**: 주인공이 터미널에서 명령을 실행하는 장면
3. **사건 전개**: 보안 사고가 발생하고 대응하는 과정
4. **회고/분석**: 사건 후 팀이 분석하며 교훈을 정리하는 장면

```markdown
# Vol.1 Ch.2 — SSH 브루트포스

"여기 봐." 재현이 화면을 가리켰다. Wazuh 대시보드에 빨간 점이 점멸하고 있었다.
rule.id 5763 — 같은 IP에서 30초 안에 SSH 로그인 시도가 8번.

"공격자 IP가 뭐야?" 수진이 물었다.
"203.0.113.50. 지금 nftables에서 막아야 해."

재현은 OpsClaw 터미널을 열었다.

```bash
opsclaw run "203.0.113.50 SSH 차단" --target v-secu
```

OpsClaw가 nftables 규칙을 자동 생성하고, Evidence가 기록되었다.
[Evidence: ev_xxx, exit_code=0, 차단 규칙 적용 완료]
```

---

## 6. CTFd 플랫폼

### 6.1 CTFd 설정

CTFd는 Docker로 실행되며 OpsClaw와 연동된다.

```bash
# CTFd 기동
cd docker/
docker compose -f ctfd-compose.yaml up -d

# 접속
# http://localhost:8080 (또는 서버 IP:8080)
```

### 6.2 CTF 문제 YAML 형식

각 문제는 YAML 파일로 정의한다.

```yaml
# contents/ctf/course1/week01/challenges.yaml
challenges:
  - name: "port-scan-basic"
    category: "Course1-Week01"
    description: |
      v-web 서버(192.168.0.110)에서 열려 있는 포트를 확인하세요.
      80번 포트에서 실행 중인 서비스의 버전 문자열을 FLAG로 제출하세요.
    value: 100
    type: "standard"
    flag: "FLAG{Apache/2.4.62}"
    hints:
      - content: "ss 또는 nmap을 사용하세요"
        cost: 10
    tags: ["reconnaissance", "nmap"]

  - name: "nft-list-rules"
    category: "Course1-Week01"
    description: |
      v-secu 서버의 nftables 규칙 중 input 체인에 등록된
      drop 규칙의 수를 세어 FLAG 형식으로 제출하세요.
      예: FLAG{3}
    value: 150
    type: "standard"
    flag: "FLAG{5}"
    hints:
      - content: "nft list chain inet filter input"
        cost: 20
    tags: ["firewall", "nftables"]

  - name: "wazuh-alert-count"
    category: "Course1-Week01"
    description: |
      v-siem의 Wazuh에서 최근 1시간 동안 발생한
      level 10 이상 알림의 수를 확인하세요.
    value: 200
    type: "standard"
    flag: "FLAG{12}"
    tags: ["siem", "wazuh"]
```

### 6.3 문제 등록 스크립트

```bash
# register_challenges.py 사용법
python3 scripts/register_challenges.py \
  --ctfd-url http://localhost:8080 \
  --token <CTFd_API_Token> \
  --yaml contents/ctf/course1/week01/challenges.yaml

# 전체 과정 일괄 등록
for course in course1 course2 course3 course4; do
  for week in $(ls contents/ctf/$course/); do
    python3 scripts/register_challenges.py \
      --ctfd-url http://localhost:8080 \
      --token $CTFD_TOKEN \
      --yaml contents/ctf/$course/$week/challenges.yaml
  done
done
```

### 6.4 register_challenges.py 동작

```python
# 스크립트 내부 동작 요약
1. YAML 파일을 읽는다
2. CTFd REST API를 호출하여 각 challenge를 생성한다
   POST /api/v1/challenges  (name, description, value, type, category)
3. FLAG를 등록한다
   POST /api/v1/flags       (challenge_id, content, type=static)
4. 힌트를 등록한다
   POST /api/v1/hints       (challenge_id, content, cost)
5. 태그를 등록한다
   POST /api/v1/tags        (challenge_id, value)
```

---

## 7. Evidence 기반 자동 채점

### 7.1 개념

학생이 OpsClaw를 통해 실습을 수행하면, 모든 명령과 결과가 Evidence로 기록된다.
이 Evidence를 기반으로 자동 채점이 가능하다.

```
학생 실습 흐름:

1. 학생이 OpsClaw CLI로 실습 명령 실행
   opsclaw run "v-secu의 nftables 규칙 확인" --target v-secu

2. OpsClaw가 SubAgent를 통해 명령 실행
   → nft list ruleset

3. Evidence 기록
   → evidence_id: ev_xxx
   → stdout: nftables 규칙 목록
   → exit_code: 0

4. PoW 블록 생성
   → 변조 불가능한 실행 증적

5. Evidence에서 FLAG 추출
   → FLAG{5} (drop 규칙 수)

6. CTFd에 제출
```

### 7.2 자동 검증 스크립트

```bash
#!/bin/bash
# flag_verify.sh — Evidence에서 FLAG를 자동 추출하고 검증

PROJECT_ID=$1
EXPECTED_FLAG=$2
API_KEY="opsclaw-api-key-2026"

# Evidence 조회
EVIDENCE=$(curl -s -H "X-API-Key: $API_KEY" \
  http://localhost:8000/projects/$PROJECT_ID/evidence)

# stdout에서 FLAG 패턴 추출
FLAG=$(echo "$EVIDENCE" | python3 -c "
import json, sys, re
data = json.load(sys.stdin)
for ev in data.get('evidence', []):
    match = re.search(r'FLAG\{[^}]+\}', ev.get('stdout', ''))
    if match:
        print(match.group())
        break
")

if [ "$FLAG" = "$EXPECTED_FLAG" ]; then
    echo "CORRECT: $FLAG"
    exit 0
else
    echo "WRONG: got '$FLAG', expected '$EXPECTED_FLAG'"
    exit 1
fi
```

### 7.3 OpsClaw 검증 실행

```bash
# 프로젝트의 Evidence를 검증하는 validate/check 활용
curl -X POST http://localhost:8000/projects/{id}/validate/check \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "validator_name": "ctf_flag_check",
    "command": "nft list chain inet filter input | grep -c drop",
    "expected_contains": "5",
    "expected_exit_code": 0,
    "subagent_url": "http://192.168.0.108:8002"
  }'
```

---

## 8. PoW 체인과 학업 무결성

### 8.1 왜 블록체인인가

교육 환경에서 PoW 체인은 다음을 보장한다.

1. **실행 증명**: 학생이 실제로 명령을 실행했다는 증거
2. **시간 순서**: 블록의 시간 순서로 학습 과정을 추적
3. **변조 불가**: 이전 블록의 해시가 다음 블록에 연결되므로 중간 변조 불가
4. **성과 추적**: `task_reward`로 학생별 학습 성과를 정량 측정

### 8.2 학생별 PoW 체인 확인

```bash
# 학생 에이전트 체인 검증 (각 학생이 별도 SubAgent 사용)
curl "http://localhost:8000/pow/verify?agent_id=http://student01:8002" \
  -H "X-API-Key: $OPSCLAW_API_KEY"

# 학생 보상 랭킹
curl http://localhost:8000/pow/leaderboard -H "X-API-Key: $OPSCLAW_API_KEY"

# 특정 학생의 보상 이력
curl "http://localhost:8000/rewards/agents?agent_id=http://student01:8002" \
  -H "X-API-Key: $OPSCLAW_API_KEY"
```

### 8.3 실습 Replay

학생의 전체 작업 과정을 타임라인으로 재생할 수 있다.

```bash
# 프로젝트 Replay (시간순 타임라인)
curl http://localhost:8000/projects/{id}/replay \
  -H "X-API-Key: $OPSCLAW_API_KEY"

# 응답 예시
{
  "project_id": "proj_xxx",
  "timeline": [
    {
      "ts": "2026-03-30T10:00:00Z",
      "type": "evidence",
      "command": "nft list ruleset",
      "exit_code": 0,
      "agent_id": "http://student01:8002"
    },
    {
      "ts": "2026-03-30T10:01:15Z",
      "type": "pow_block",
      "block_hash": "0000abc...",
      "task_title": "nftables 규칙 확인"
    }
  ]
}
```

---

## 9. 교육과정 운영 시나리오

### 9.1 1주차 수업 흐름 예시

```
[사전 준비]
1. 교수자가 해당 주차 CTF 문제를 CTFd에 등록
2. 학생별 OpsClaw 프로젝트 생성

[수업]
3. 이론 강의 (교안 기반)
4. 소설 해당 화 독서 토론
5. OpsClaw 실습
   - 학생이 CLI로 명령 실행
   - Evidence 자동 기록
6. CTF 문제 풀이
   - 실습 결과에서 FLAG 추출
   - CTFd에 제출

[평가]
7. Evidence 기반 자동 채점
8. PoW 체인 무결성 확인
9. 보상 랭킹으로 성과 비교
```

### 9.2 학생 프로젝트 생성 자동화

```bash
# 30명 학생의 Week01 프로젝트 일괄 생성
for i in $(seq -w 1 30); do
  curl -X POST http://localhost:8000/projects \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $OPSCLAW_API_KEY" \
    -d "{
      \"name\": \"student${i}-week01\",
      \"request_text\": \"Course1 Week01 실습\",
      \"master_mode\": \"external\"
    }"
done
```

### 9.3 전체 학생 성과 대시보드

```bash
# 보상 리더보드 조회 (학생 순위)
curl http://localhost:8000/pow/leaderboard?limit=30 \
  -H "X-API-Key: $OPSCLAW_API_KEY"

# 특정 학생의 전체 프로젝트 목록
curl "http://localhost:8000/projects?limit=50" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | \
  python3 -c "
import json, sys
data = json.load(sys.stdin)
for p in data['projects']:
    if 'student05' in p['name']:
        print(f\"{p['id']} | {p['name']} | {p['status']}\")
"
```

---

## 10. CTF 문제 유형

### 10.1 기본 유형

| 유형 | 설명 | 예시 |
|------|------|------|
| standard | 정적 FLAG 제출 | FLAG{Apache/2.4.62} |
| dynamic | 점수 감소형 (풀수록 점수 하락) | 경쟁 문제 |
| manual | 교수자 수동 채점 | 보고서 작성 |

### 10.2 OpsClaw 연동 유형

| 유형 | 설명 |
|------|------|
| evidence-check | OpsClaw Evidence의 exit_code와 stdout으로 자동 검증 |
| validate-check | `/validate/check` API로 실시간 검증 |
| pow-verify | PoW 블록 존재 여부로 실행 확인 |

### 10.3 문제 난이도 매핑

```
교안 Week 01-03 → Easy (100-150점)
교안 Week 04-06 → Medium (200-300점)
교안 Week 07-09 → Hard (300-400점)
교안 Week 10-12 → Expert (400-500점)
교안 Week 13-15 → Challenge (500점+)
```

---

## 11. 교육 인프라 서버 구성

| 서버 | IP | 역할 | 교육 용도 |
|------|----|------|----------|
| v-secu | 192.168.0.108 | nftables + Suricata IPS | 방화벽/IPS 실습 |
| v-web | 192.168.0.110 | Apache + OWASP JuiceShop | 웹 보안 실습 |
| v-siem | 192.168.0.109 | Wazuh 4.11.2 | SIEM/로그 분석 실습 |
| opsclaw | 192.168.208.142 | Manager API + CTFd | 제어/채점 서버 |

```bash
# 서버 별명으로 접근 (CLI)
opsclaw run "방화벽 규칙 확인" --target v-secu
opsclaw run "웹서버 상태 확인" --target v-web
opsclaw run "Wazuh 알림 조회" --target v-siem
```
