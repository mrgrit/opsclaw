# Claude Code 모드 (Mode B) 개요

> **문서 버전**: 1.0 | **최종 수정**: 2026-03-30

---

## Claude Code 모드란 무엇인가

Claude Code 모드(Mode B)는 Anthropic의 Claude Code가 OpsClaw Manager API를 직접 호출하여
작업을 계획, 실행, 분석, 보고하는 모드이다. Claude가 "External Master" 역할을 수행하며,
OpsClaw는 실행 인프라(control-plane)로 동작한다.

```
사용자 → Claude Code (대형 LLM)
              │
              ├── curl로 Manager API(:8000) 직접 호출
              │       ↓
              │   Manager → SubAgent(:8002) → 명령 실행
              │       ↓
              │   Evidence + PoW 자동 기록
              │
              └── 결과 분석 → 다음 단계 결정 → 반복
```

---

## 핵심 개념: 역할 분담

| 주체 | 역할 | 하면 안 되는 것 |
|------|------|----------------|
| **Claude Code (당신)** | 사용자 요구 분석, 작업 계획, API 호출, 결과 해석, 완료보고 | 서버에 직접 SSH, SubAgent 직접 호출 |
| **Manager API (:8000)** | 프로젝트 상태 관리, 인증, Evidence 기록, PoW 생성 | 작업 계획 수립 (Mode B에서) |
| **SubAgent (:8002)** | 실제 shell 명령 실행, 파일 조작, 서비스 제어 | 독립 동작 (항상 Manager를 통해서만) |

**핵심 원칙**: Claude Code는 두뇌, Manager는 control-plane, SubAgent는 손이다.
Claude Code가 직접 서버를 건드리는 일은 없다.

---

## 동작 원리

### 전체 라이프사이클

```
1. POST /projects              → 프로젝트 생성 (master_mode: "external")
2. POST /projects/{id}/plan    → 계획 단계 진입
3. POST /projects/{id}/execute → 실행 단계 진입
4. POST /projects/{id}/execute-plan  → tasks 배열 실행
   또는 POST /projects/{id}/dispatch → 단일 명령 실행
5. GET  /projects/{id}/evidence/summary → 결과 확인
6. (필요시) 결과 분석 후 추가 dispatch/execute-plan
7. POST /projects/{id}/completion-report → 완료보고서
8. POST /projects/{id}/close  → 프로젝트 종료 (선택)
```

### Stage 전환 규칙

프로젝트는 반드시 다음 순서로 Stage를 전환해야 한다:

```
init → plan → execute → (작업 실행) → (close)
```

| 전환 | API | 설명 |
|------|-----|------|
| init → plan | `POST /projects/{id}/plan` | 계획 수립 완료 선언 |
| plan → execute | `POST /projects/{id}/execute` | 실행 준비 완료 선언 |

> Stage 전환 없이 `execute-plan`이나 `dispatch`를 호출하면 **400 에러**가 발생한다.

---

## 언제 Claude Code 모드를 사용하는가

### Claude Code 모드가 유리한 경우

| 시나리오 | 이유 |
|----------|------|
| **복잡한 보안 사고 대응** | 1단계 결과를 분석하고 동적으로 다음 조치를 결정해야 함 |
| **다단계 보안 감사** | 방화벽 → TLS → 계정 → 로그 순차 점검 + 종합 분석 |
| **인프라 변경 작업** | 변경 전 점검 → 변경 → 변경 후 검증의 동적 흐름 |
| **장애 원인 분석** | 증상 수집 → 가설 수립 → 검증 → 결론의 반복 과정 |
| **다중 서버 협업 작업** | secu + web + siem 서버의 결과를 교차 분석 |
| **설정 파일 분석/수정** | 설정 내용을 읽고 해석하여 수정 방안을 결정 |

### Native 모드로 충분한 경우

| 시나리오 | 이유 |
|----------|------|
| 단순 상태 점검 | LLM 계획으로 충분 |
| 반복 작업 자동화 | Playbook + Schedule로 처리 |
| 한 줄 명령 실행 | dispatch가 더 빠름 |

---

## CLAUDE.md의 역할

프로젝트 루트의 `CLAUDE.md` 파일은 Claude Code가 OpsClaw를 운용하기 위한 핵심 가이드이다.
Claude Code는 이 파일을 읽고 다음 정보를 파악한다:

- **인프라 구성**: 서버 IP, SubAgent URL, 서비스 포트
- **API 사용법**: curl 명령 예시, 인증 방법
- **안전 규칙**: risk_level 처리, 파괴적 명령 제한
- **PoW/RL**: 블록체인 무결성 검증, 강화학습 추천

```
/home/opsclaw/opsclaw/
  CLAUDE.md          ← Claude Code 오케스트레이션 가이드 (이 파일)
  docs/
    agent-system-prompt.md  ← 에이전트 시스템 프롬프트
    api/
      external-master-guide.md  ← 상세 API 레퍼런스
```

---

## 인증

모든 Manager API 호출에는 X-API-Key 헤더가 필수이다.

```bash
# 환경변수 설정
export OPSCLAW_API_KEY="opsclaw-api-key-2026"

# 모든 curl 호출에 포함
curl -H "X-API-Key: $OPSCLAW_API_KEY" http://localhost:8000/projects
```

인증 없이 호출하면:
```json
{"detail": "Missing or invalid API key"}
```

---

## 실행 방법 3가지

### 방법 A: execute-plan (추천 — 다단계 작업)

사용자 요청을 분석하여 tasks 배열을 직접 구성하고 일괄 실행한다.

```bash
curl -s -X POST http://localhost:8000/projects/$PID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {"order": 1, "title": "현황 수집", "instruction_prompt": "df -h && free -m", "risk_level": "low"},
      {"order": 2, "title": "패키지 업데이트", "instruction_prompt": "apt-get update -y", "risk_level": "low"}
    ],
    "subagent_url": "http://localhost:8002"
  }'
```

특징:
- 여러 태스크를 한 번에 실행
- PoW 블록과 보상이 자동 생성
- task별로 다른 SubAgent URL 지정 가능
- 병렬/순차 실행 선택 가능

### 방법 B: dispatch (단일 명령)

한 줄 명령을 즉시 실행한다. 상태 확인, 진단용으로 적합하다.

```bash
curl -s -X POST http://localhost:8000/projects/$PID/dispatch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{"command": "systemctl status nginx", "subagent_url": "http://localhost:8002"}'
```

### 방법 C: playbook/run (사전 등록 절차)

등록된 Playbook을 프로젝트에 연결하여 실행한다.

```bash
# Playbook 생성
curl -s -X POST http://localhost:8000/playbooks \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{"name": "server-check", "version": "1.0"}'

# Step 추가
curl -s -X POST http://localhost:8000/playbooks/$PBID/steps \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{"step_order": 1, "step_type": "skill", "name": "probe_linux_host", "ref_id": "probe_linux_host"}'

# 프로젝트에 연결
curl -s -X POST http://localhost:8000/projects/$PID/playbooks/$PBID \
  -H "X-API-Key: $OPSCLAW_API_KEY"

# 실행
curl -s -X POST http://localhost:8000/projects/$PID/playbook/run \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{"dry_run": false, "subagent_url": "http://localhost:8002"}'
```

---

## risk_level 규칙

| 레벨 | 설명 | 예시 | 동작 |
|------|------|------|------|
| `low` | 읽기 전용, 무해한 명령 | `hostname`, `df -h`, `cat` | 즉시 실행 |
| `medium` | 시스템 상태 변경 가능 | `apt-get update`, `systemctl restart` | 즉시 실행 |
| `high` | 중요 변경, 서비스 영향 가능 | 설정 파일 수정, 방화벽 규칙 변경 | 실행 (주의) |
| `critical` | 파괴적 가능성 있는 명령 | `rm -rf`, `DROP TABLE` | **dry_run 자동 강제** |

`critical` 태스크는:
1. 자동으로 `dry_run`이 적용되어 실제 실행되지 않는다
2. 사용자가 결과를 확인한 후, `"confirmed": true`를 추가하여 재호출해야 실제 실행된다

```bash
# critical 태스크 실제 실행 (사용자 확인 후)
curl -s -X POST http://localhost:8000/projects/$PID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [{"order": 1, "instruction_prompt": "rm -rf /tmp/old-data", "risk_level": "critical"}],
    "subagent_url": "http://localhost:8002",
    "confirmed": true
  }'
```

---

## Claude Code 모드의 장점

### 1. 대형 LLM의 추론 능력

Native 모드의 8B~120B 모델 대비 Claude의 추론 능력이 월등히 높다.
복잡한 로그 분석, 보안 이벤트 상관 분석, 설정 파일 해석 등에 적합하다.

### 2. 동적 워크플로우

1단계 결과를 분석하고 2단계 계획을 동적으로 수정할 수 있다.

```
[1단계] df -h 실행 → 디스크 90% 사용 확인
  → [2단계] du -sh /var/log/* 로 원인 파악 (동적 결정)
  → [3단계] journalctl --vacuum-time=7d 로 정리 (동적 결정)
  → [4단계] df -h 로 결과 확인 (동적 결정)
```

### 3. 대화형 작업

사용자와 왕복 대화하며 작업을 진행할 수 있다.
"이 결과가 정상인가요?" → 사용자 판단 → 다음 단계 결정

### 4. 다중 서버 교차 분석

여러 서버의 결과를 한 곳에서 분석하여 상관관계를 파악할 수 있다.

```
secu 서버: nftables 규칙 수집
web 서버:  Apache 접근 로그 수집
siem 서버: Wazuh 알림 수집
  → Claude가 세 서버의 결과를 교차 분석하여 보안 이슈 도출
```

### 5. 완료보고서 품질

Claude가 전체 작업 과정을 이해하고 있으므로, 정확하고 상세한 완료보고서를 작성할 수 있다.

---

## 에러 처리

### 자주 발생하는 에러와 대응

| 에러 | 상태 코드 | 원인 | 대응 |
|------|-----------|------|------|
| `Missing or invalid API key` | 401 | X-API-Key 누락/오류 | 헤더 확인 |
| `stage must be plan` | 400 | Stage 전환 순서 위반 | `/plan` → `/execute` 순서 확인 |
| `project not found` | 404 | 잘못된 project_id | `GET /projects`로 확인 |
| `SubAgent connection refused` | 502 | SubAgent 다운 | `/health` 확인, 재배포 |
| `task status: failed` | 200 | 명령 실행 실패 | evidence에서 stderr 확인 |

### 에러 복구 패턴

```bash
# 1. Stage 에러 복구 — plan/execute를 순서대로 재호출
curl -s -X POST http://localhost:8000/projects/$PID/plan \
  -H "X-API-Key: $OPSCLAW_API_KEY"
curl -s -X POST http://localhost:8000/projects/$PID/execute \
  -H "X-API-Key: $OPSCLAW_API_KEY"

# 2. 부분 실패 복구 — 실패한 태스크만 재실행
curl -s -X POST http://localhost:8000/projects/$PID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [{"order": 3, "title": "재시도", "instruction_prompt": "...", "risk_level": "low"}],
    "subagent_url": "http://localhost:8002"
  }'

# 3. SubAgent 연결 확인
curl -s http://192.168.208.150:8002/health
```

---

## 안전 규칙

1. **SubAgent에 직접 POST 금지** — 반드시 Manager API를 통해서만 호출
2. **risk_level=critical 태스크는 dry_run 먼저** — 결과 확인 후 실행 승인
3. **파괴적 명령은 사용자 확인 후에만** — rm -rf, DROP TABLE, format 등
4. **한 프로젝트 = 한 작업 단위** — 관련 없는 작업을 같은 project에 섞지 않음
5. **Evidence 직접 조작 금지** — 모든 기록은 Manager가 자동 관리
6. **SubAgent URL 임의 변경 금지** — 사용자가 지정한 서버만 사용

---

## 실전 시나리오: 보안 사고 대응

```
1. 프로젝트 생성
   POST /projects {name:"incident-response", master_mode:"external"}

2. Stage 전환
   POST /projects/{id}/plan
   POST /projects/{id}/execute

3. 1차 수집 — 알림 확인
   POST /projects/{id}/dispatch
   {command: "cat /var/ossec/logs/alerts/alerts.json | tail -20", subagent_url:"http://192.168.208.152:8002"}

4. 결과 분석 → 의심 IP 식별

5. 2차 수집 — 방화벽 로그 확인
   POST /projects/{id}/dispatch
   {command: "nft list ruleset | grep 10.0.0.99", subagent_url:"http://192.168.208.150:8002"}

6. 3차 조치 — 차단 규칙 추가
   POST /projects/{id}/execute-plan
   {tasks:[{order:1, instruction_prompt:"nft add rule ...", risk_level:"high"}], ...}

7. 완료보고서
   POST /projects/{id}/completion-report
   {summary:"의심 IP 10.0.0.99 차단 완료", outcome:"success", ...}
```

---

## 다음 단계

- **Manager API 전체 레퍼런스**: [02-api-guide.md](02-api-guide.md)
- **Native 모드 비교**: [../native-mode/01-overview.md](../native-mode/01-overview.md)
- **CLI 가이드**: [../native-mode/02-cli-guide.md](../native-mode/02-cli-guide.md)
