# Week 09: OpsClaw (1) - 기본

## 학습 목표
- OpsClaw의 프로젝트 생명주기를 이해한다
- dispatch와 execute-plan의 차이를 구분하고 적절히 사용한다
- 증거(evidence) 시스템과 PoW 체인을 이해한다
- OpsClaw를 활용한 보안 점검 자동화를 실습한다

---

## 1. OpsClaw 프로젝트 생명주기

```
created → planned → executing → done
   ↓         ↓          ↓
 생성      계획 수립    실행 중     완료
```

### Stage 전환 규칙

| 현재 → 다음 | API | 설명 |
|------------|-----|------|
| created → planned | POST /projects/{id}/plan | 계획 단계 진입 |
| planned → executing | POST /projects/{id}/execute | 실행 단계 진입 |
| executing → done | POST /projects/{id}/completion-report | 완료 보고 |

---

## 2. 프로젝트 생성

```bash
# external 모드: Claude Code(사람)가 오케스트레이션
curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "name": "security-audit-web",
    "request_text": "web 서버 보안 점검",
    "master_mode": "external"
  }' | python3 -m json.tool

# 응답에서 id 필드를 기록해둔다
```

### master_mode 옵션

| 모드 | 설명 | 사용 시점 |
|------|------|----------|
| **external** | 외부 도구(Claude Code)가 계획/실행 | 수동 오케스트레이션 |
| **native** | Master Service가 LLM으로 자동 | 자동 오케스트레이션 |

---

## 3. Dispatch (단일 명령 실행)

dispatch는 **단일 명령**을 특정 SubAgent에 전달하여 실행한다.

```bash
# 프로젝트 ID를 변수에 저장
PID="프로젝트_ID"

# Stage 전환
curl -s -X POST "http://localhost:8000/projects/$PID/plan" \
  -H "X-API-Key: opsclaw-api-key-2026"
curl -s -X POST "http://localhost:8000/projects/$PID/execute" \
  -H "X-API-Key: opsclaw-api-key-2026"

# 로컬 SubAgent에서 명령 실행
curl -s -X POST "http://localhost:8000/projects/$PID/dispatch" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "command": "hostname && uptime",
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool

# 원격 SubAgent에서 명령 실행 (secu 서버)
curl -s -X POST "http://localhost:8000/projects/$PID/dispatch" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "command": "sudo nft list ruleset | head -20",
    "subagent_url": "http://192.168.208.150:8002"
  }' | python3 -m json.tool
```

---

## 4. Execute-plan (다중 태스크 실행)

execute-plan은 **여러 태스크를 순차적으로** 실행한다.
각 태스크에 risk_level과 SubAgent를 지정할 수 있다.

```bash
curl -s -X POST "http://localhost:8000/projects/$PID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "hostname",
        "risk_level": "low",
        "subagent_url": "http://localhost:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "cat /etc/os-release",
        "risk_level": "low",
        "subagent_url": "http://192.168.208.150:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "docker ps --format table",
        "risk_level": "medium",
        "subagent_url": "http://192.168.208.151:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

### Risk Level

| 수준 | 설명 | 동작 |
|------|------|------|
| low | 읽기 전용, 안전 | 즉시 실행 |
| medium | 설정 변경 가능 | 즉시 실행 |
| high | 서비스 영향 가능 | 확인 후 실행 |
| critical | 파괴적 가능성 | dry_run 자동 강제 |

---

## 5. 증거(Evidence) 시스템

모든 실행 결과는 증거로 기록된다.

```bash
# 증거 요약 조회
curl -s -H "X-API-Key: opsclaw-api-key-2026" \
  "http://localhost:8000/projects/$PID/evidence/summary" | python3 -m json.tool
```

### PoW (Proof of Work) 체인

모든 태스크 실행은 PoW 블록으로 기록되어 변조를 방지한다.

```bash
# PoW 블록 조회
curl -s -H "X-API-Key: opsclaw-api-key-2026" \
  "http://localhost:8000/pow/blocks?agent_id=http://localhost:8002" | python3 -m json.tool

# 체인 무결성 검증
curl -s -H "X-API-Key: opsclaw-api-key-2026" \
  "http://localhost:8000/pow/verify?agent_id=http://localhost:8002" | python3 -m json.tool
# 정상: {"valid": true, "blocks": N, "orphans": 0}
```

---

## 6. 완료 보고서

프로젝트 완료 시 결과 보고서를 작성한다.

```bash
curl -s -X POST "http://localhost:8000/projects/$PID/completion-report" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "summary": "web 서버 보안 점검 완료",
    "outcome": "success",
    "work_details": [
      "호스트 정보 수집 완료",
      "OS 버전 확인 완료",
      "Docker 컨테이너 목록 확인 완료"
    ]
  }' | python3 -m json.tool
```

---

## 7. 실습: 보안 점검 자동화

### 실습 1: 전체 플로우 체험

```bash
# 1. 프로젝트 생성
PID=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"name":"lab-audit","request_text":"실습 보안 점검","master_mode":"external"}' \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")
echo "Project: $PID"

# 2. Stage 전환
curl -s -X POST "http://localhost:8000/projects/$PID/plan" \
  -H "X-API-Key: opsclaw-api-key-2026" > /dev/null
curl -s -X POST "http://localhost:8000/projects/$PID/execute" \
  -H "X-API-Key: opsclaw-api-key-2026" > /dev/null

# 3. 보안 점검 태스크 실행
curl -s -X POST "http://localhost:8000/projects/$PID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "tasks": [
      {"order":1, "instruction_prompt":"uname -a", "risk_level":"low"},
      {"order":2, "instruction_prompt":"ss -tlnp", "risk_level":"low"},
      {"order":3, "instruction_prompt":"last -10", "risk_level":"low"}
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool

# 4. 증거 확인
curl -s -H "X-API-Key: opsclaw-api-key-2026" \
  "http://localhost:8000/projects/$PID/evidence/summary" | python3 -m json.tool

# 5. 완료 보고
curl -s -X POST "http://localhost:8000/projects/$PID/completion-report" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"summary":"보안 점검 완료","outcome":"success","work_details":["시스템 정보 수집","열린 포트 확인","최근 로그인 이력 확인"]}'
```

### 실습 2: 다중 서버 점검

```bash
# 여러 서버에 동시에 명령 실행
curl -s -X POST "http://localhost:8000/projects/$PID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "tasks": [
      {"order":1, "instruction_prompt":"hostname && uptime", "risk_level":"low", "subagent_url":"http://localhost:8002"},
      {"order":2, "instruction_prompt":"hostname && uptime", "risk_level":"low", "subagent_url":"http://192.168.208.150:8002"},
      {"order":3, "instruction_prompt":"hostname && uptime", "risk_level":"low", "subagent_url":"http://192.168.208.151:8002"}
    ],
    "subagent_url":"http://localhost:8002"
  }' | python3 -m json.tool
```

### 실습 3: PoW 체인 확인

```bash
# 보상 랭킹 확인
curl -s -H "X-API-Key: opsclaw-api-key-2026" \
  http://localhost:8000/pow/leaderboard | python3 -m json.tool

# 프로젝트 작업 리플레이
curl -s -H "X-API-Key: opsclaw-api-key-2026" \
  "http://localhost:8000/projects/$PID/replay" | python3 -m json.tool
```

---

## 핵심 정리

1. OpsClaw 프로젝트는 created → planned → executing → done 순으로 진행한다
2. dispatch는 단일 명령, execute-plan은 여러 태스크를 순차 실행한다
3. risk_level로 태스크의 위험도를 관리하고, critical은 자동으로 dry_run된다
4. 모든 작업은 증거로 기록되고 PoW 체인으로 무결성을 보장한다
5. API 호출 시 반드시 X-API-Key 헤더를 포함해야 한다

---

## 다음 주 예고
- Week 10: OpsClaw (2) - Playbook과 강화학습(RL) 연동
