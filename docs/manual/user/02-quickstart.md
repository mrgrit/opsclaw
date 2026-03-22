# OpsClaw 빠른 시작

서비스가 기동된 상태에서 첫 번째 작업을 5분 안에 실행한다.

---

## 방법 A — Claude Code (권장)

Claude Code를 External Master로 사용하는 가장 간단한 방법.

```bash
# OpsClaw 프로젝트 디렉토리에서 Claude Code 실행
cd /path/to/opsclaw
claude
```

Claude Code는 `CLAUDE.md`를 자동으로 읽고 OpsClaw 오케스트레이션을 시작한다.

예시 요청:
```
"로컬 서버의 CPU/메모리/디스크 현황을 수집하고 보고서를 남겨줘"
```

Claude Code가 자동으로:
1. 프로젝트 생성 (`master_mode=external`)
2. 작업 계획 수립
3. Manager API 호출 → SubAgent 실행
4. evidence 확인 → 완료보고서 생성

---

## 방법 B — curl (API 직접 호출)

### 1단계: 프로젝트 생성

```bash
curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "첫번째-테스트",
    "request_text": "서버 현황 수집",
    "master_mode": "external"
  }' | python3 -m json.tool
```

응답에서 `project.id` 저장:
```json
{"project": {"id": "prj_abc123...", "current_stage": "intake"}}
```

### 2단계: Stage 전환

```bash
PROJECT_ID="prj_abc123..."

curl -X POST http://localhost:8000/projects/$PROJECT_ID/plan
curl -X POST http://localhost:8000/projects/$PROJECT_ID/execute
```

### 3단계: 작업 실행

```bash
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute-plan \
  -H "Content-Type: application/json" \
  -d '{
    "tasks": [
      {"order": 1, "title": "현황 수집", "instruction_prompt": "hostname && uptime && df -h && free -m", "risk_level": "low"}
    ],
    "subagent_url": "http://localhost:8002",
    "dry_run": false
  }' | python3 -m json.tool
```

### 4단계: 결과 확인

```bash
curl http://localhost:8000/projects/$PROJECT_ID/evidence/summary
```

### 5단계: 완료보고서

```bash
curl -X POST http://localhost:8000/projects/$PROJECT_ID/completion-report \
  -H "Content-Type: application/json" \
  -d '{
    "summary": "서버 현황 수집 완료",
    "outcome": "success",
    "work_details": ["hostname/uptime/디스크/메모리 수집 완료"],
    "issues": [],
    "next_steps": []
  }'
```

---

## 결과 확인 방법

```bash
# 프로젝트 목록
curl http://localhost:8000/projects

# 특정 프로젝트 상세
curl http://localhost:8000/projects/$PROJECT_ID

# evidence 목록 (실행 결과 로그)
curl http://localhost:8000/projects/$PROJECT_ID/evidence

# 완료보고서 조회
curl http://localhost:8000/projects/$PROJECT_ID/report
```
