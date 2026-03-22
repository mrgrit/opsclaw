# A2A 프로토콜 연동 가이드

A2A(Agent-to-Agent) 프로토콜은 Manager와 SubAgent 간 통신 규격이다.

---

## 아키텍처

```
External Master (Claude Code)
       │  REST API
       ▼
Manager API (:8000)
       │  A2A HTTP
       ▼
SubAgent Runtime (:8002)
       │  subprocess
       ▼
대상 서버 shell
```

---

## SubAgent A2A 엔드포인트

SubAgent가 제공하는 A2A API:

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/health` | GET | 상태 확인 |
| `/a2a/run_script` | POST | 스크립트/명령 실행 |
| `/a2a/invoke_llm` | POST | LLM 직접 호출 (Ollama) |
| `/a2a/analyze` | POST | 출력 분석 (LLM) |

---

## `/a2a/run_script` — 명령 실행

Manager가 SubAgent에 명령을 전달할 때 사용하는 핵심 엔드포인트.

**Request:**
```json
{
  "project_id": "prj_...",
  "job_run_id": "job_...",
  "script": "echo hello && hostname && df -h",
  "timeout": 60
}
```

**Response:**
```json
{
  "status": "ok",
  "detail": {
    "exit_code": 0,
    "stdout": "hello\nweb-server-01\nFilesystem ...",
    "stderr": "",
    "duration_seconds": 0.3
  }
}
```

실패 시:
```json
{
  "status": "error",
  "detail": {
    "exit_code": 127,
    "stdout": "",
    "stderr": "command not found: nginx",
    "duration_seconds": 0.1
  }
}
```

---

## `/a2a/invoke_llm` — LLM 호출

SubAgent를 통해 Ollama에 직접 LLM 요청:

**Request:**
```json
{
  "project_id": "prj_...",
  "job_run_id": "job_...",
  "task": "다음 출력에서 비정상 프로세스를 찾아줘:\n[ps 출력 내용]"
}
```

**Response:**
```json
{
  "response": "비정상 프로세스: PID 1234 (crypto_miner) — CPU 사용률 98%",
  "model": "gpt-oss:120b",
  "tokens": 256
}
```

---

## `/a2a/analyze` — 출력 분석

명령 실행 결과를 LLM으로 분석:

**Request:**
```json
{
  "project_id": "prj_...",
  "job_run_id": "job_...",
  "content": "분석할 텍스트 (stdout 등)",
  "question": "이 내용에서 이상한 점은?"
}
```

---

## 커스텀 SubAgent 개발

표준 A2A 엔드포인트를 구현하면 OpsClaw와 연동 가능한 커스텀 SubAgent를 만들 수 있다.

### 최소 구현 (FastAPI 예시)

```python
from fastapi import FastAPI
import subprocess

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok", "service": "custom-subagent"}

@app.post("/a2a/run_script")
def run_script(body: dict):
    script = body.get("script", "")
    timeout = body.get("timeout", 60)

    try:
        result = subprocess.run(
            script, shell=True, capture_output=True,
            text=True, timeout=timeout
        )
        return {
            "status": "ok",
            "detail": {
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        }
    except subprocess.TimeoutExpired:
        return {"status": "error", "detail": {"exit_code": 124, "stderr": "timeout"}}
```

### 요구사항

- `/health` → `{"status":"ok"}` 반환
- `/a2a/run_script` → `{"status":"ok","detail":{"exit_code":N,"stdout":"...","stderr":"..."}}` 반환
- 포트: 기본 8002 (변경 가능)
- HTTPS 선택적 (내부망에서는 HTTP 사용 가능)

---

## A2A 직접 호출 (디버깅 목적)

Manager를 통하지 않고 SubAgent를 직접 호출할 수 있다 (디버깅용).
**운영 환경에서는 반드시 Manager를 통해 호출할 것 — evidence 누락 방지.**

```bash
# SubAgent 직접 호출 (디버깅 전용)
curl -X POST http://192.168.0.10:8002/a2a/run_script \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "debug",
    "job_run_id": "debug-001",
    "script": "echo test",
    "timeout": 10
  }'
```

---

## 보안 고려사항

### 내부망 전용 운영

SubAgent는 신뢰할 수 있는 네트워크에서만 접근 가능하도록 방화벽 설정:

```bash
# SubAgent 포트 (8002)를 Manager IP에서만 허용
ufw allow from <manager_ip> to any port 8002
ufw deny 8002
```

### 인증 (현재 미구현, 향후 추가 예정)

현재 A2A 프로토콜은 인증 없이 동작한다.
운영 환경에서는 네트워크 레이어에서 접근 제어 필수.

향후 계획:
- HMAC 서명 기반 요청 인증
- TLS mutual authentication
