# Manager API 인증 가이드 (M28)

> **마일스톤**: M28 (BUG-001 수정)
> **방식**: API Key (`X-API-Key` 헤더)

---

## 개요

M28부터 Manager API(`:8000`)에 API Key 인증이 적용됩니다.
`OPSCLAW_API_KEY` 환경변수가 설정된 경우 모든 API 요청에 키가 필요합니다.

---

## 빠른 시작

```bash
# .env 또는 환경에서 키 확인
echo $OPSCLAW_API_KEY
# → opsclaw-api-key-2026

# 모든 API 호출에 헤더 추가
curl -H "X-API-Key: $OPSCLAW_API_KEY" http://localhost:8000/projects
```

---

## 지원 헤더

```bash
# 방법 1 (권장): X-API-Key 헤더
curl -H "X-API-Key: $OPSCLAW_API_KEY" ...

# 방법 2: Authorization Bearer
curl -H "Authorization: Bearer $OPSCLAW_API_KEY" ...
```

---

## 인증 불필요 경로 (whitelist)

| 경로 | 이유 |
|------|------|
| `GET /health` | 모니터링 헬스체크 |
| `GET /` | 리다이렉트 |
| `GET /ui` | 대시보드 UI |
| `GET /app/*` | React SPA 정적 파일 |
| WebSocket `/ws/*` | HTTP Upgrade 요청 |
| `OPTIONS *` | CORS pre-flight |

---

## Claude Code (External Master) 사용

Claude Code에서 Manager API를 호출할 때 모든 curl에 키를 포함하세요:

```bash
# 프로젝트 생성
curl -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{"name":"my-task","request_text":"...","master_mode":"external"}'

# execute-plan
curl -X POST http://localhost:8000/projects/{id}/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d @/tmp/tasks.json
```

---

## 개발 모드 (인증 비활성화)

`OPSCLAW_API_KEY`를 빈 값으로 설정하거나 삭제하면 인증이 비활성화됩니다:

```bash
# .env에서 주석 처리 또는 빈 값
OPSCLAW_API_KEY=

# 확인
curl http://localhost:8000/health  # 200 OK (항상)
curl http://localhost:8000/projects  # OPSCLAW_API_KEY 없으면 200 OK
```

---

## 키 교체 방법

```bash
# 1. 새 키 생성 (권장: 32바이트 랜덤)
NEW_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
echo "New key: $NEW_KEY"

# 2. .env 업데이트
sed -i "s/^OPSCLAW_API_KEY=.*/OPSCLAW_API_KEY=$NEW_KEY/" .env

# 3. Manager API 재시작
kill $(pgrep -f "manager-api") && sleep 2
set -a && source .env && set +a && export PYTHONPATH=/home/opsclaw/opsclaw
nohup .venv/bin/python3.11 -m uvicorn apps.manager-api.src.main:app \
  --host 0.0.0.0 --port 8000 --log-level warning > /tmp/manager.log 2>&1 &
```

---

## 오류 응답

인증 실패 시 HTTP 401 반환:

```json
{
  "error": "Unauthorized",
  "detail": "Valid X-API-Key header required"
}
```

---

## 보안 고려사항

- API Key는 `.env` 파일에 저장 — `.gitignore`에 포함 필수
- 프로덕션에서는 강력한 랜덤 키 사용 (`secrets.token_hex(32)`)
- 타이밍 공격 방지: `secrets.compare_digest()` 사용
- 향후 M29: DB 기반 API Key 관리 (다중 키, 만료, 권한별 키)
