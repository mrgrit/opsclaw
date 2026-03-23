# Web UI 가이드

OpsClaw Web UI는 React + Vite SPA로 구현되어 있으며, Manager API(`http://localhost:8000/app/`)에서 서빙된다.

---

## 접근 방법

```
http://localhost:8000/app/
```

`http://localhost:8000/`로 접근하면 자동으로 `/app/`으로 리다이렉트된다.

> **빌드 필요**: `apps/web-ui/dist/`는 gitignore 대상이므로 clone 후 직접 빌드해야 한다.

---

## 최초 빌드

```bash
# Node.js 없으면 먼저 설치
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

cd apps/web-ui
npm install
npm run build
```

빌드 완료 후 `dist/`가 생성되며, Manager API 재시작 시 자동으로 서빙된다.

> Manager API가 이미 실행 중이면 **재시작** 필요 (dist가 없는 상태로 기동된 경우 `/app/` 경로가 등록되지 않는다).

---

## 페이지 안내

### Dashboard

- 서비스 health 상태 (ok / error)
- 활성 프로젝트 수 및 에이전트 수
- 최근 프로젝트 목록
- 에이전트 보상 랭킹 (PoW leaderboard)

### Projects

- 프로젝트 목록 조회 및 신규 생성
- Stage 전환 버튼 (plan → execute → validate → close)
- Evidence 목록 (명령, exit code, stdout 미리보기)
- WebSocket 기반 실시간 stage 업데이트

### Playbooks

- Playbook 목록 조회
- Playbook 선택 시 step 목록 확인
- 새 Playbook 생성
- 특정 프로젝트에 Playbook 실행

### Replay

- Project ID 입력 → 실행 타임라인 조회
- 각 task: 순서, 제목, exit code, 소요시간, 보상 포인트, 블록 해시
- Chain 무결성 검증 결과 표시

### PoW Blocks

`execute-plan`으로 작업을 실행하면 자동으로 PoW 블록이 생성된다. 별도의 채굴 명령은 없다.

- 에이전트 목록 (잔액 기준 정렬)
- 에이전트 선택 시 블록 체인 조회
- 블록 상세: prev_hash, 보상, exit code, **Nonce, Difficulty**, 블록 해시, 생성시각
- Chain 무결성 검증 (tamper 감지: hash mismatch, difficulty 미충족, chain 끊김)

### Settings

- 알림 채널 추가 (Slack / Email / Webhook)
- 알림 규칙 추가 (event_type 매칭)
- 채널 및 규칙 목록 조회

---

## 개발 서버 (프론트엔드 개발용)

```bash
cd apps/web-ui
npm run dev
# → http://localhost:5173/app/
```

개발 서버는 `/api/*` 요청을 `http://localhost:8000`으로 프록시하므로 Manager API가 실행 중이어야 한다.

---

## 문제 해결

| 증상 | 원인 | 해결 |
|------|------|------|
| `/app/` → 404 | dist 없거나 서버 재시작 필요 | `npm run build` 후 Manager API 재시작 |
| `/` → `/ui` 로 리다이렉트 | 서버가 구 코드로 기동됨 | Manager API 재시작 |
| API 호출 실패 | Manager API 미실행 | `./dev.sh manager` |
| 빈 목록 | DB 미연결 또는 seed 미적재 | `./dev.sh manager` + seed_loader 실행 |
