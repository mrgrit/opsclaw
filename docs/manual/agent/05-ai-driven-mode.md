# AI-Driven Mode (Mode B) 운용 매뉴얼

**대상:** OpsClaw를 외부 AI 에이전트(Claude Code, GPT-4, Gemini 등)로 제어하는 운영자 및 에이전트 개발자

---

## 개요

OpsClaw는 두 가지 오케스트레이션 모드를 지원한다.

| 모드 | master_mode | 주 사용자 |
|------|-------------|----------|
| Mode A: Native | `native` | 웹 UI / master-service 내장 LLM |
| **Mode B: AI-Driven** | `external` | **외부 AI 에이전트 (Claude Code 등)** |

Mode B에서 외부 AI는 **External Master** 역할을 맡는다.
OpsClaw는 실행 control-plane(상태 관리, evidence 기록, 명령 dispatch)만 담당한다.

---

## AI 에이전트에게 OpsClaw를 연동하는 방법

### 방법 1: System Prompt 직접 삽입 (추천)

에이전트 실행 전 `docs/agent-system-prompt.md` 파일 내용을 system prompt에 삽입한다.

```python
# 예시: Python에서 Claude API 사용 시
with open("docs/agent-system-prompt.md") as f:
    opsclaw_prompt = f.read()

system_prompt = f"""
{opsclaw_prompt}

---

추가 지시사항:
- SubAgent URL: http://192.168.0.10:8002
- 작업 대상 서버: web-server-01
"""
```

### 방법 2: 첫 번째 도구 호출로 읽기 강제

에이전트 도구 정의에 `read_opsclaw_guide` 도구를 최우선 도구로 등록:

```json
{
  "name": "read_opsclaw_guide",
  "description": "OpsClaw 작업 시작 전 반드시 호출. 역할, API 흐름, 안전 규칙을 반환한다.",
  "input_schema": {"type": "object", "properties": {}}
}
```

도구 실행 시 `docs/agent-system-prompt.md` 내용 반환.

### 방법 3: CLAUDE.md (Claude Code 전용)

Claude Code는 프로젝트 루트의 `CLAUDE.md`를 자동으로 읽는다.
이미 적용되어 있음. Claude Code 사용자는 별도 설정 불필요.

---

## 역할 경계 상세

### External Master (AI 에이전트)의 책임 범위

```
✅ 할 일
- 사용자 자연어 → 작업 계획 변환
- risk_level 판단 (low/medium/high/critical)
- execute-plan tasks 배열 구성
- evidence stdout/stderr 해석 → 성공/실패 판단
- 완료보고서 작성

❌ 하면 안 되는 일
- 서버에 직접 SSH 접속
- SubAgent (localhost:8002)에 직접 POST
- 한 번의 execute-plan에 관련 없는 작업 혼용
- risk_level=critical 작업을 dry_run 없이 실행
- Manager API evidence 직접 INSERT/UPDATE
```

### Manager API (:8000)의 책임 범위

```
✅ Manager가 자동 처리
- Project stage machine 상태 전이 검증
- 모든 실행 결과 → evidence 자동 기록
- risk_level=critical → dry_run 강제 적용
- Playbook step 순서 보장

❌ Manager가 하지 않는 것
- 사용자 의도 해석
- 작업 순서 결정
- 실패 원인 분석
```

### SubAgent Runtime (:8002)의 책임 범위

```
✅ SubAgent가 처리
- shell 명령 실제 실행
- stdout/stderr/exit_code 반환
- Skill 스크립트 실행 (probe_linux_host 등)

❌ SubAgent 직접 호출 금지
- 반드시 Manager /dispatch 또는 /execute-plan 통해서만
- 직접 호출 시 evidence 기록 누락, audit 불가
```

---

## 에이전트 개발 가이드

### 에이전트 루프 구조 (의사코드)

```python
def opsclaw_agent(user_request: str, subagent_url: str):
    # 1. 프로젝트 생성
    project = api.post("/projects", {
        "name": derive_name(user_request),
        "request_text": user_request,
        "master_mode": "external"
    })
    pid = project["project"]["id"]

    # 2. Stage 전환 (필수)
    api.post(f"/projects/{pid}/plan")
    api.post(f"/projects/{pid}/execute")

    # 3. 작업 계획 수립 (AI 담당)
    tasks = plan_tasks(user_request)  # AI가 결정

    # 4. dry_run으로 검증 (critical 태스크 포함 시)
    if any(t["risk_level"] == "critical" for t in tasks):
        dry = api.post(f"/projects/{pid}/execute-plan",
                       {"tasks": tasks, "dry_run": True, "subagent_url": subagent_url})
        confirm = ask_user(f"이 작업을 실행할까요?\n{dry}")
        if not confirm:
            return "취소됨"

    # 5. 실제 실행
    result = api.post(f"/projects/{pid}/execute-plan",
                      {"tasks": tasks, "dry_run": False, "subagent_url": subagent_url})

    # 6. 결과 해석
    evidence = api.get(f"/projects/{pid}/evidence/summary")
    interpretation = interpret_evidence(evidence)  # AI 담당

    # 7. 완료보고서
    api.post(f"/projects/{pid}/completion-report", {
        "summary": summarize(result),
        "outcome": "success" if result["overall"] == "success" else "partial",
        "work_details": [t["title"] for t in tasks],
        "issues": extract_issues(result),
        "next_steps": recommend_next(interpretation)
    })

    return interpretation
```

---

## 다중 에이전트 시나리오

OpsClaw는 여러 AI 에이전트가 동시에 사용하는 상황을 지원한다.

### 역할 분리 패턴

```
Orchestrator Agent (계획)
    ↓  POST /projects + /execute-plan
Manager API (상태 관리)
    ↓  dispatch to
SubAgent-01 (웹서버 담당)     SubAgent-02 (DB 서버 담당)
http://web-server:8002        http://db-server:8002
```

각 에이전트는 **project_id를 공유**하면 같은 evidence에 기록된다.
순서 의존성이 있는 작업은 하나의 execute-plan에 `order` 필드로 직렬화한다.

### 병렬 실행 시 주의사항

```
❌ 같은 project_id로 동시에 두 번의 execute-plan 호출 → race condition
✅ 병렬 작업은 별도 project_id 생성 → evidence 병합은 에이전트 레이어에서
```

---

## 트러블슈팅

### "stage must be plan" 에러

```bash
# 원인: /plan → /execute 없이 execute-plan 호출
# 해결:
curl -X POST http://localhost:8000/projects/{id}/plan
curl -X POST http://localhost:8000/projects/{id}/execute
```

### evidence에 결과가 없음

```bash
# 원인: dry_run=true로 실행했거나 SubAgent URL이 틀림
curl http://localhost:8002/health   # SubAgent 확인
# dry_run: false 로 재실행
```

### step status: failed

```bash
# evidence에서 stderr 확인
curl http://localhost:8000/projects/{id}/evidence
# task_results[n].stderr 내용 분석 후 instruction_prompt 수정
```

### Skill 실행 시 "no command specified"

```bash
# 원인: Playbook step에 params가 누락됨
# 해결: step 등록 시 params 포함
curl -X POST http://localhost:8000/playbooks/{pb_id}/steps \
  -d '{"step_order":1,"step_type":"tool","name":"run_command","ref_id":"run_command",
       "params":{"command":"echo test"}}'
```

---

## PoW & 보상 자동 연동

`execute-plan`으로 Task를 실행하면 **별도 호출 없이** PoW 블록과 보상이 자동 생성된다.

### 동작 원리

1. SubAgent가 Task 실행 완료
2. Manager가 `generate_proof()` 자동 호출
3. SHA-256 nonce 채굴 → PoW 블록 생성 (difficulty=4, `0000...`으로 시작하는 해시 탐색)
4. 보상 계산: 성공 +1.0 / 실패 -1.0 + 속도 보너스 + 위험도 페널티
5. `reward_ledger`에 누적 잔액 갱신

### 확인 방법

```bash
# 에이전트의 PoW 블록 조회
curl "http://localhost:8000/pow/blocks?agent_id=http://localhost:8002"

# 블록체인 무결성 검증
curl "http://localhost:8000/pow/verify?agent_id=http://localhost:8002"

# 보상 랭킹
curl http://localhost:8000/pow/leaderboard

# 프로젝트 작업 Replay
curl http://localhost:8000/projects/{id}/replay
```

> `dry_run=true`인 Task는 PoW 블록이 생성되지 않는다.

---

## 체크리스트 — 에이전트 연동 전 확인

- [ ] `docs/agent-system-prompt.md`를 system prompt에 삽입했는가?
- [ ] Manager API(`localhost:8000`)가 응답하는가? `GET /health`
- [ ] SubAgent Runtime(`localhost:8002`)이 응답하는가? `GET /health`
- [ ] DB migration이 모두 적용되었는가? (0001~0010)
- [ ] `master_mode: "external"` 로 프로젝트를 생성하는가?
- [ ] `/plan` → `/execute` 순서를 지키는가?
- [ ] `risk_level=critical` 태스크에 dry_run 검토가 있는가?
- [ ] 완료 후 `completion-report`를 제출하는가?
