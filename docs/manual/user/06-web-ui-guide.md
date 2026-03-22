# Web UI 가이드

> **현재 상태:** Web UI는 M16에서 구현 예정이다. 현재 OpsClaw는 API 전용으로 운영된다.
> 이 문서는 M16 완료 후 업데이트된다.

---

## 현재 사용 가능한 인터페이스

### 1. Claude Code (권장)

OpsClaw 프로젝트 디렉토리에서 `claude` 명령으로 실행.
`CLAUDE.md`를 자동으로 읽고 External Master로서 작업을 수행한다.

### 2. REST API (curl / Postman / httpie)

모든 기능은 REST API로 접근 가능하다.

```bash
# API 엔드포인트 목록 확인
curl http://localhost:8000/openapi.json | python3 -m json.tool | grep '"path"'

# 또는 브라우저에서
http://localhost:8000/docs      # Swagger UI
http://localhost:8000/redoc     # ReDoc
```

### 3. Python SDK (직접 구성)

```python
import httpx

MANAGER = "http://localhost:8000"

def create_project(name, request_text):
    r = httpx.post(f"{MANAGER}/projects", json={
        "name": name,
        "request_text": request_text,
        "master_mode": "external"
    })
    return r.json()["project"]["id"]
```

---

## M16 Web UI 예정 기능

M16에서 구현될 화면 목록:

| 화면 | 주요 기능 |
|------|---------|
| 대시보드 | 에이전트 상태, 진행 중 프로젝트, 최근 알림 |
| 프로젝트 | 목록, 생성, 상태 추적, evidence 조회 |
| 에이전트 | SubAgent 등록/편집, 상태 모니터링, bootstrap 실행 |
| Playbook | 목록, 생성/편집, 실행 이력 |
| 설정 | 알림 채널(Slack/Email/Webhook), RBAC 사용자/역할 |
| 작업 Replay | 프로젝트 단위 단계별 Replay 뷰어 |

---

## Swagger UI 사용법

`http://localhost:8000/docs`에서 모든 API를 브라우저에서 직접 테스트할 수 있다.

1. 엔드포인트 클릭 → "Try it out"
2. Request body 입력
3. "Execute" 클릭
4. Response 확인
