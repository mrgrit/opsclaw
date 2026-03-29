# OpsClaw 빠른 시작 (Quick Start)

> **문서 버전**: 1.0 | **최종 수정**: 2026-03-30
> **사전 조건**: [02-installation.md](02-installation.md) 의 설치가 완료된 상태

---

## 5분 안에 첫 프로젝트 실행하기

이 가이드에서는 OpsClaw의 두 가지 모드로 각각 프로젝트를 생성하고 실행하는 과정을 보여준다.

---

## 사전 확인

서비스가 정상 실행 중인지 확인한다.

```bash
# 서비스 헬스체크
curl -s http://localhost:8000/health  # Manager API
curl -s http://localhost:8002/health  # SubAgent Runtime
```

두 서비스 모두 `{"status": "ok"}` 를 반환해야 한다.
실행 중이 아니면 `./dev.sh all` 로 기동한다.

---

## 방법 1: Native 모드 (CLI)

OpsClaw CLI를 사용하여 자연어로 작업을 지시한다.
Master Service(:8001)의 LLM이 작업 계획을 자동 수립한다.

### 1-1. 로컬 서버 점검

```bash
# CLI 실행 (로컬 SubAgent에서 실행)
python3 apps/cli/opsclaw.py run "서버 현황을 점검해줘"
```

출력 예시:
```
요청: 서버 현황을 점검해줘
대상: http://localhost:8002

프로젝트: prj_a1b2c3d4e5f6
Master LLM이 계획 수립 중...
3개 태스크 생성:
   [1] 시스템 기본 정보 수집
   [2] 디스크 사용량 확인
   [3] 네트워크 상태 점검

실행 중...
============================================================
결과: success | 성공: 3/3
============================================================

[1] 시스템 기본 정보 수집 (1.24s)
   Linux opsclaw 6.8.0-106-generic
   ...

[2] 디스크 사용량 확인 (0.85s)
   /dev/sda1  50G  12G  38G  24%  /
   ...

[3] 네트워크 상태 점검 (0.92s)
   ...

Evidence: 3건 | 성공률: 100%
보고서 생성 완료

프로젝트 ID: prj_a1b2c3d4e5f6
```

### 1-2. 원격 서버 점검

```bash
# v-secu 서버 점검 (서버 별명 사용)
python3 apps/cli/opsclaw.py run "방화벽 규칙을 확인해줘" -t v-secu

# IP 직접 지정도 가능
python3 apps/cli/opsclaw.py run "Apache 상태 확인" -t 192.168.0.110
```

### 1-3. 단일 명령 직접 실행

LLM 계획 없이 명령을 직접 실행할 때:

```bash
# dispatch로 단일 명령 실행
python3 apps/cli/opsclaw.py dispatch "hostname && uptime" -t local

# v-web 서버의 Apache 상태 확인
python3 apps/cli/opsclaw.py dispatch "systemctl status apache2" -t v-web
```

### 1-4. 프로젝트 확인

```bash
# 최근 프로젝트 목록
python3 apps/cli/opsclaw.py list

# 특정 프로젝트 상태
python3 apps/cli/opsclaw.py status prj_a1b2c3d4e5f6

# 실행 이력 재현
python3 apps/cli/opsclaw.py replay prj_a1b2c3d4e5f6
```

---

## 방법 2: Claude Code 모드 (curl)

Claude Code 또는 curl을 사용하여 Manager API를 직접 호출한다.
사용자(또는 AI)가 작업 계획을 직접 구성한다.

### 환경변수 설정

```bash
export OPSCLAW_API_KEY="opsclaw-api-key-2026"
```

### 2-1. 프로젝트 생성

```bash
curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "quickstart-test",
    "request_text": "서버 현황 점검 및 디스크 사용량 확인",
    "master_mode": "external"
  }' | python3 -m json.tool
```

응답에서 `project.id` 를 저장한다:
```json
{
  "status": "ok",
  "project": {
    "id": "prj_a1b2c3d4e5f6",
    "name": "quickstart-test",
    "current_stage": "init",
    "master_mode": "external"
  }
}
```

```bash
# 프로젝트 ID 저장
PID="prj_a1b2c3d4e5f6"  # 실제 응답값으로 교체
```

### 2-2. Stage 전환

```bash
# plan 단계로 전환
curl -s -X POST http://localhost:8000/projects/$PID/plan \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool

# execute 단계로 전환
curl -s -X POST http://localhost:8000/projects/$PID/execute \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
```

> **중요**: `/plan` -> `/execute` 순서를 반드시 지켜야 한다. 이 순서를 건너뛰면 400 에러가 발생한다.

### 2-3. 작업 실행 (execute-plan)

```bash
curl -s -X POST http://localhost:8000/projects/$PID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "title": "시스템 정보 수집",
        "instruction_prompt": "hostname && uptime && uname -a",
        "risk_level": "low"
      },
      {
        "order": 2,
        "title": "디스크 사용량 확인",
        "instruction_prompt": "df -h",
        "risk_level": "low"
      },
      {
        "order": 3,
        "title": "메모리 상태 확인",
        "instruction_prompt": "free -m",
        "risk_level": "low"
      }
    ],
    "subagent_url": "http://localhost:8002",
    "dry_run": false
  }' | python3 -m json.tool
```

응답 예시:
```json
{
  "status": "ok",
  "tasks_total": 3,
  "tasks_ok": 3,
  "tasks_failed": 0,
  "overall": "success",
  "task_results": [
    {
      "order": 1,
      "title": "시스템 정보 수집",
      "status": "ok",
      "duration_s": 1.15,
      "detail": {
        "stdout": "opsclaw\n 10:30:45 up 5 days...",
        "stderr": "",
        "exit_code": 0
      }
    }
  ]
}
```

### 2-4. 단일 명령 실행 (dispatch)

간단한 확인 작업은 dispatch로 즉시 실행할 수 있다:

```bash
curl -s -X POST http://localhost:8000/projects/$PID/dispatch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "command": "cat /etc/os-release",
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

### 2-5. Evidence 확인

```bash
# Evidence 요약
curl -s http://localhost:8000/projects/$PID/evidence/summary \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
```

응답 예시:
```json
{
  "status": "ok",
  "total_evidence": 4,
  "success_rate": "100%",
  "total_duration_s": 3.92
}
```

```bash
# Evidence 전체 목록 (stdout/stderr 포함)
curl -s http://localhost:8000/projects/$PID/evidence \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
```

### 2-6. PoW 블록 확인

```bash
# 프로젝트의 PoW 블록
curl -s http://localhost:8000/projects/$PID/pow \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool

# 체인 무결성 검증
curl -s "http://localhost:8000/pow/verify?agent_id=http://localhost:8002" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
```

검증 응답:
```json
{
  "status": "ok",
  "result": {
    "agent_id": "http://localhost:8002",
    "valid": true,
    "blocks": 3,
    "orphans": 0,
    "tampered": []
  }
}
```

### 2-7. 완료보고서 제출

```bash
curl -s -X POST http://localhost:8000/projects/$PID/completion-report \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "summary": "서버 현황 점검 완료 - 시스템 정보, 디스크, 메모리 정상 확인",
    "outcome": "success",
    "work_details": [
      "시스템 정보 수집 완료",
      "디스크 사용량 24% 정상 범위",
      "메모리 여유 충분"
    ],
    "issues": [],
    "next_steps": ["주간 정기 점검 스케줄 등록 권장"]
  }' | python3 -m json.tool
```

### 2-8. Replay 확인

프로젝트의 전체 실행 타임라인을 확인한다:

```bash
curl -s http://localhost:8000/projects/$PID/replay \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
```

응답 예시:
```json
{
  "project_id": "prj_a1b2c3d4e5f6",
  "steps_total": 3,
  "steps_success": 3,
  "total_reward": 3.9,
  "timeline": [
    {
      "task_order": 1,
      "task_title": "시스템 정보 수집",
      "exit_code": 0,
      "duration_s": 1.15,
      "total_reward": 1.3,
      "block_hash": "0000a2f7..."
    }
  ]
}
```

---

## 전체 흐름 요약 (한 장 정리)

### Native 모드 (CLI)

```
opsclaw run "요청" -t 대상
  └→ 프로젝트 생성 → Master LLM 계획 → Stage 전환 → execute-plan → Evidence → 보고서
```

### Claude Code 모드 (API)

```
POST /projects              → 프로젝트 생성 (master_mode: external)
POST /projects/{id}/plan    → 계획 단계 진입
POST /projects/{id}/execute → 실행 단계 진입
POST /projects/{id}/execute-plan → tasks 배열 실행
 (또는 /dispatch            → 단일 명령 즉시 실행)
GET  /projects/{id}/evidence/summary → 결과 확인
POST /projects/{id}/completion-report → 완료보고서
POST /projects/{id}/close   → 프로젝트 종료 (선택)
```

---

## 원격 서버에서 실행하기

### 서버 별명 사용 (CLI)

```bash
# v-secu 서버 (가상 방화벽)
python3 apps/cli/opsclaw.py run "nftables 규칙 확인" -t v-secu

# v-web 서버 (가상 웹 서버)
python3 apps/cli/opsclaw.py dispatch "systemctl status apache2" -t v-web

# v-siem 서버 (가상 SIEM)
python3 apps/cli/opsclaw.py run "Wazuh 알림 확인" -t v-siem
```

### SubAgent URL 직접 지정 (API)

```bash
# secu 서버에서 실행
curl -s -X POST http://localhost:8000/projects/$PID/dispatch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "command": "nft list ruleset | head -30",
    "subagent_url": "http://192.168.208.150:8002"
  }'
```

### task별 다른 서버 지정 (execute-plan)

```bash
curl -s -X POST http://localhost:8000/projects/$PID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "title": "방화벽 규칙 확인",
        "instruction_prompt": "nft list ruleset | head -20",
        "risk_level": "low",
        "subagent_url": "http://192.168.208.150:8002"
      },
      {
        "order": 2,
        "title": "웹 서버 상태 확인",
        "instruction_prompt": "systemctl status apache2",
        "risk_level": "low",
        "subagent_url": "http://192.168.208.151:8002"
      },
      {
        "order": 3,
        "title": "SIEM 알림 수집",
        "instruction_prompt": "cat /var/ossec/logs/alerts/alerts.json | tail -5",
        "risk_level": "low",
        "subagent_url": "http://192.168.208.152:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }'
```

---

## 보상 확인

작업을 실행하면 자동으로 보상이 지급된다.

```bash
# 보상 랭킹
curl -s http://localhost:8000/pow/leaderboard \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool

# 특정 에이전트 잔액
curl -s "http://localhost:8000/rewards/agents?agent_id=http://localhost:8002" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -m json.tool
```

---

## 다음 단계

- **Native 모드 심화**: [../native-mode/01-overview.md](../native-mode/01-overview.md)
- **Claude Code 모드 심화**: [../claude-code-mode/01-overview.md](../claude-code-mode/01-overview.md)
- **CLI 전체 레퍼런스**: [../native-mode/02-cli-guide.md](../native-mode/02-cli-guide.md)
- **API 전체 레퍼런스**: [../claude-code-mode/02-api-guide.md](../claude-code-mode/02-api-guide.md)
