# Master Service API 레퍼런스

> **문서 버전**: 1.0 | **최종 수정**: 2026-03-30
> **서비스 포트**: 8001
> **소스 파일**: `apps/master-service/src/main.py`

---

## 개요

Master Service는 OpsClaw의 Native 모드(Mode A)에서 LLM 기반 작업 계획 수립을 담당하는 서비스이다.
포트 8001에서 실행되며, Ollama LLM을 통해 사용자 요청을 분석하고 실행 가능한 tasks 배열을 생성한다.

> **Mode B(Claude Code)에서는 이 서비스를 사용하지 않는다.**
> Claude Code가 직접 Manager API(:8000)를 호출하여 작업을 계획하고 실행한다.

---

## 서비스 기동

```bash
# dev.sh 사용
./dev.sh master

# 수동 기동
set -a && source .env && set +a
export PYTHONPATH=/home/opsclaw/opsclaw
.venv/bin/uvicorn "apps.master-service.src.main:app" \
  --host 0.0.0.0 --port 8001 --reload
```

### 헬스체크

```bash
curl -s http://localhost:8001/health
# {"status": "ok", "service": "master-service"}
```

---

## 엔드포인트 목록

| Method | Path | 설명 |
|--------|------|------|
| `GET` | `/health` | 서비스 상태 확인 |
| `POST` | `/projects/{id}/master-plan` | LLM 기반 작업 계획 수립 |
| `POST` | `/projects/{id}/review` | 작업 계획 검토 |
| `GET` | `/projects/{id}/review` | 최신 검토 결과 조회 |
| `GET` | `/projects/{id}/reviews` | 전체 검토 이력 조회 |
| `POST` | `/projects/{id}/replan` | 작업 계획 재수립 |
| `POST` | `/projects/{id}/escalate` | 에스컬레이션 |
| `GET` | `/projects/{id}/status` | 프로젝트 상태 + 검증 + 검토 통합 조회 |
| `POST` | `/runtime/invoke` | LLM 직접 호출 (범용) |

---

## POST /projects/{id}/master-plan

### 설명

프로젝트의 `request_text`를 분석하여 실행 가능한 tasks 배열을 생성한다.
내부적으로 Ollama LLM을 호출하며, RAG로 유사 Playbook과 과거 보고서를 참고한다.

### 요청

```bash
curl -s -X POST http://localhost:8001/projects/$PID/master-plan \
  -H "Content-Type: application/json" \
  -d '{"subagent_url": "http://localhost:8002"}'
```

파라미터가 없어도 호출 가능하다. 프로젝트에 저장된 `request_text`를 자동으로 사용한다.

### 응답

```json
{
  "status": "ok",
  "project_id": "prj_abc123",
  "request_text": "서버 현황을 점검해줘",
  "summary": "서버 상태를 3단계로 점검합니다",
  "tasks": [
    {
      "order": 1,
      "title": "시스템 기본 정보 수집",
      "playbook_hint": null,
      "instruction_prompt": "hostname && uptime && uname -a",
      "risk_level": "low"
    },
    {
      "order": 2,
      "title": "디스크 사용량 확인",
      "playbook_hint": null,
      "instruction_prompt": "df -h && du -sh /var/log/* | sort -rh | head -5",
      "risk_level": "low"
    },
    {
      "order": 3,
      "title": "네트워크 상태 점검",
      "playbook_hint": null,
      "instruction_prompt": "ss -tlnp && ip addr show",
      "risk_level": "low"
    }
  ],
  "similar_playbooks": [
    {"name": "server-health-check", "id": "pb_xyz", "relevance": "keyword"}
  ],
  "past_reports_referenced": 2
}
```

### 응답 필드 설명

| 필드 | 타입 | 설명 |
|------|------|------|
| `summary` | string | 전체 계획 요약 (1~2문장) |
| `tasks` | array | 실행할 태스크 목록 |
| `tasks[].order` | int | 실행 순서 |
| `tasks[].title` | string | 태스크 제목 |
| `tasks[].playbook_hint` | string/null | 참고한 기존 Playbook 이름 |
| `tasks[].instruction_prompt` | string | SubAgent에서 실행할 명령/지시 |
| `tasks[].risk_level` | string | 위험도: `low`, `medium`, `high`, `critical` |
| `similar_playbooks` | array | RAG로 검색된 유사 Playbook 목록 |
| `past_reports_referenced` | int | 참고한 과거 보고서 수 |

### LLM 실패 시 폴백

Ollama 연결 실패, JSON 파싱 오류 등으로 LLM이 정상 응답하지 못하면,
단일 태스크 플랜으로 자동 폴백된다:

```json
{
  "tasks": [
    {
      "order": 1,
      "title": "서버 현황을 점검해줘",
      "playbook_hint": null,
      "instruction_prompt": "다음 작업을 수행하라: 서버 현황을 점검해줘",
      "risk_level": "medium"
    }
  ],
  "summary": "요구사항 '서버 현황을 점검해줘'을 단일 태스크로 처리."
}
```

### RAG 검색 동작

1. **Playbook 검색**: `retrieval_service.search_documents()`로 유사 Playbook을 검색
2. **키워드 매칭**: Playbook 이름의 키워드와 요청 텍스트를 비교하여 추가 매칭
3. **과거 보고서 검색**: `completion_report` 타입의 문서를 검색하여 과거 유사 작업 참고
4. **프롬프트 조합**: 위 정보를 모두 LLM 프롬프트에 포함

---

## POST /projects/{id}/review

### 설명

작업 계획(또는 실행 결과)에 대한 검토를 기록한다.
검토자(reviewer)가 승인, 거부, 재수립 필요 중 하나를 선택한다.

### 요청

```bash
curl -s -X POST http://localhost:8001/projects/$PID/review \
  -H "Content-Type: application/json" \
  -d '{
    "reviewer_id": "senior-admin",
    "review_status": "approved",
    "summary": "계획 검토 완료. 위험 요소 없음.",
    "findings": {
      "risk_assessment": "low",
      "notes": "표준 점검 절차와 일치"
    },
    "auto_replan": false
  }'
```

### 요청 필드

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `reviewer_id` | string | 필수 | 검토자 식별자 |
| `review_status` | string | 필수 | `approved`, `rejected`, `needs_replan` |
| `summary` | string | 필수 | 검토 요약 |
| `findings` | object | 선택 | 검토 상세 내용 |
| `auto_replan` | bool | 선택 | `needs_replan` 시 자동 재수립 여부 (기본: false) |

### 응답

```json
{
  "status": "ok",
  "review": {
    "id": "rev_abc123",
    "project_id": "prj_abc123",
    "reviewer_agent_id": "senior-admin",
    "status": "approved",
    "review_summary": "계획 검토 완료. 위험 요소 없음.",
    "findings": {"risk_assessment": "low", "notes": "표준 점검 절차와 일치"},
    "created_at": "2026-03-30T10:35:00Z"
  },
  "replan": null
}
```

### review_status 선택지

| 상태 | 설명 | 후속 동작 |
|------|------|-----------|
| `approved` | 계획 승인 — 실행 진행 가능 | 없음 |
| `rejected` | 계획 거부 — 실행 불가 | 수동으로 수정 후 재검토 필요 |
| `needs_replan` | 계획 재수립 필요 | `auto_replan: true`이면 자동 재수립 |

---

## GET /projects/{id}/review

### 설명

프로젝트의 최신 검토 결과를 조회한다.

```bash
curl -s http://localhost:8001/projects/$PID/review
```

### 응답

```json
{
  "status": "ok",
  "review": {
    "id": "rev_abc123",
    "project_id": "prj_abc123",
    "reviewer_agent_id": "senior-admin",
    "status": "approved",
    "review_summary": "계획 검토 완료",
    "findings": {},
    "created_at": "2026-03-30T10:35:00Z"
  }
}
```

검토 기록이 없으면 404를 반환한다.

---

## GET /projects/{id}/reviews

### 설명

프로젝트의 전체 검토 이력을 조회한다.

```bash
curl -s http://localhost:8001/projects/$PID/reviews
```

### 응답

```json
{
  "status": "ok",
  "reviews": [
    {
      "id": "rev_001",
      "status": "needs_replan",
      "review_summary": "디스크 정리 단계가 누락됨",
      "created_at": "2026-03-30T10:30:00Z"
    },
    {
      "id": "rev_002",
      "status": "approved",
      "review_summary": "수정된 계획 승인",
      "created_at": "2026-03-30T10:35:00Z"
    }
  ]
}
```

---

## POST /projects/{id}/replan

### 설명

프로젝트의 작업 계획을 재수립한다. 계획 단계(plan stage)에서만 호출 가능하다.

```bash
curl -s -X POST http://localhost:8001/projects/$PID/replan \
  -H "Content-Type: application/json" \
  -d '{"reason": "디스크 정리 단계가 누락됨. 추가 필요."}'
```

### 요청 필드

| 필드 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| `reason` | string | `"master-initiated replan"` | 재수립 사유 |

### 응답

```json
{
  "status": "ok",
  "project": {
    "id": "prj_abc123",
    "current_stage": "plan",
    "replan_count": 1
  }
}
```

### 에러

| 상태 코드 | 원인 | 해결 |
|-----------|------|------|
| 400 | execute 단계에서 호출 | plan 단계에서만 호출 가능 |
| 404 | 프로젝트 없음 | project_id 확인 |

---

## POST /projects/{id}/escalate

### 설명

위험도가 높은 작업이나 판단이 어려운 상황에서 상위 담당자에게 에스컬레이션한다.
내부적으로 `rejected` 상태의 review를 생성한다.

```bash
curl -s -X POST http://localhost:8001/projects/$PID/escalate \
  -H "Content-Type: application/json" \
  -d '{
    "level": 2,
    "reason": "critical risk 태스크 포함 - 수동 승인 필요",
    "reviewer_id": "master-service"
  }'
```

### 요청 필드

| 필드 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| `level` | int | `1` | 에스컬레이션 레벨 (1=팀장, 2=부서장, 3=CISO) |
| `reason` | string | `"no reason given"` | 에스컬레이션 사유 |
| `reviewer_id` | string | `"master-service"` | 에스컬레이션 요청자 |

### 응답

```json
{
  "status": "ok",
  "review": {
    "id": "rev_esc001",
    "status": "rejected",
    "review_summary": "Escalated to level 2: critical risk 태스크 포함 - 수동 승인 필요",
    "findings": {
      "escalation_level": 2,
      "reason": "critical risk 태스크 포함 - 수동 승인 필요"
    }
  },
  "escalation_level": 2
}
```

---

## GET /projects/{id}/status

### 설명

프로젝트의 상태, 검증 결과, 최신 검토를 통합하여 한 번에 조회한다.

```bash
curl -s http://localhost:8001/projects/$PID/status
```

### 응답

```json
{
  "status": "ok",
  "project": {
    "id": "prj_abc123",
    "name": "서버점검",
    "current_stage": "execute",
    "master_mode": "native"
  },
  "validation_status": {
    "is_valid": true,
    "checks": ["stage_sequence", "required_fields"]
  },
  "latest_review": {
    "id": "rev_002",
    "status": "approved",
    "review_summary": "승인"
  }
}
```

---

## POST /runtime/invoke

### 설명

Ollama LLM을 범용으로 직접 호출한다. 계획 수립 외의 용도로 LLM을 활용할 때 사용한다.

```bash
curl -s -X POST http://localhost:8001/runtime/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "다음 로그에서 보안 이슈를 분석하라:\n[로그 내용]",
    "role": "master"
  }'
```

### 요청 필드

| 필드 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| `prompt` | string | (필수) | LLM에 전달할 프롬프트 |
| `role` | string | `"master"` | LLM 역할 (프롬프트 컨텍스트) |

### 응답

```json
{
  "status": "ok",
  "session_id": "sess_abc123",
  "result": {
    "stdout": "분석 결과: ...",
    "model": "gpt-oss:120b"
  }
}
```

### 에러

LLM 호출 실패 시 502 Bad Gateway:

```json
{
  "detail": {
    "message": "pi adapter invocation failed",
    "error": "connection refused",
    "stdout": "",
    "stderr": "Ollama 서버 연결 실패",
    "exit_code": 1
  }
}
```

---

## 프롬프트 엔지니어링 팁

Master Service의 LLM 계획 품질을 높이기 위한 권장사항:

### 요청 텍스트 작성 원칙

1. **구체적으로 작성**: "서버 점검" 보다 "v-secu 서버의 nftables 방화벽 규칙과 Suricata IDS 상태를 점검"
2. **목적을 명시**: "확인해줘" 보다 "보안 감사를 위해 ... 을 확인하고 문제점을 보고"
3. **대상을 명확히**: "웹 서버" 보다 "192.168.0.110의 Apache 웹 서버"
4. **제약 조건 포함**: "read-only로만 확인, 설정 변경 금지" 등

### 좋은 요청 예시

```
서버 점검:       "v-secu 서버의 시스템 정보, 디스크 사용량, 메모리 현황, 오픈 포트를 종합 점검해줘"
보안 감사:       "v-web 서버의 TLS 인증서 유효기간, Apache 설정 보안, 불필요한 오픈 포트를 감사해줘"
사고 대응:       "v-siem에서 최근 1시간 내 critical 등급 Wazuh 알림을 수집하고 원인을 분석해줘"
패키지 관리:     "v-secu 서버의 보안 패치를 확인하고, 적용 가능한 업데이트 목록을 보여줘"
```

### 나쁜 요청 예시

```
"점검해줘"                → 무엇을 점검할지 불명확
"서버 좀 봐줘"            → 대상 서버와 점검 항목이 모호
"다 확인해"               → 범위가 너무 넓음
```

---

## 다음 단계

- **CLI에서 Native 모드 사용**: [02-cli-guide.md](02-cli-guide.md)
- **Claude Code 모드 전환**: [../claude-code-mode/01-overview.md](../claude-code-mode/01-overview.md)
- **Manager API 전체 가이드**: [../claude-code-mode/02-api-guide.md](../claude-code-mode/02-api-guide.md)
