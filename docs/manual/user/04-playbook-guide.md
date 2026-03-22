# Playbook 작성 및 실행 가이드

## Playbook이란?

Playbook은 반복 가능한 작업 절차를 단계(step) 단위로 정의한 템플릿이다.

```
Playbook
  └─ Step 1: skill  probe_linux_host    ← 호스트 현황 수집
  └─ Step 2: tool   query_metric        ← CPU/메모리/디스크 수치
  └─ Step 3: tool   run_command         ← 커스텀 명령
```

---

## 등록된 Playbook 조회

```bash
GET /playbooks          # 전체 목록
GET /playbooks/{id}     # 단건 (steps 포함)
```

---

## Playbook 생성

### 1. Playbook 등록

```bash
POST /playbooks
{
  "name": "nginx-install",
  "version": "1.0",
  "description": "Nginx 설치 및 서비스 확인",
  "risk_level": "medium",
  "dry_run_supported": true
}
```

응답: `{"playbook": {"id": "pb_...", ...}}`

### 2. Step 추가

각 step은 개별 POST로 추가한다.

**Skill step (절차 단위):**
```bash
POST /playbooks/{pb_id}/steps
{
  "step_order": 1,
  "step_type": "skill",
  "name": "probe_linux_host",
  "ref_id": "probe_linux_host"
}
```

**Tool step (단일 명령):**
```bash
POST /playbooks/{pb_id}/steps
{
  "step_order": 2,
  "step_type": "tool",
  "name": "run_command",
  "ref_id": "run_command",
  "params": {"command": "apt-get install -y nginx"}
}
```

**on_failure 옵션 (step 실패 시 동작):**
```bash
{
  ...,
  "on_failure": "abort"     # abort(기본) | continue | replan
}
```

---

## Playbook 실행

### 프로젝트에 연결 후 실행

```bash
# 1. 프로젝트 생성 및 stage 전환
PROJECT_ID=$(curl -s -X POST http://localhost:8000/projects \
  -d '{"name":"nginx-setup","master_mode":"external"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['project']['id'])")

curl -X POST http://localhost:8000/projects/$PROJECT_ID/plan
curl -X POST http://localhost:8000/projects/$PROJECT_ID/execute

# 2. Playbook 연결
curl -X POST http://localhost:8000/projects/$PROJECT_ID/playbooks/$PB_ID

# 3. dry_run 먼저 확인
curl -X POST http://localhost:8000/projects/$PROJECT_ID/playbook/run \
  -d '{"dry_run": true, "subagent_url": "http://localhost:8002"}'

# 4. 실제 실행
curl -X POST http://localhost:8000/projects/$PROJECT_ID/playbook/run \
  -d '{"dry_run": false, "subagent_url": "http://localhost:8002"}'
```

응답 구조:
```json
{
  "result": {
    "status": "success",
    "steps_total": 3,
    "steps_ok": 3,
    "step_results": [
      {"order": 1, "name": "probe_linux_host", "status": "ok", "stdout": "..."},
      {"order": 2, "name": "run_command",       "status": "ok", "stdout": "..."}
    ]
  }
}
```

---

## 등록된 Tool 목록

| name | 설명 | params |
|------|------|--------|
| `run_command` | 임의 shell 명령 | `command` (필수) |
| `fetch_log` | 로그 파일 조회 | `log_path`, `lines` |
| `query_metric` | CPU/메모리/디스크/네트워크 | (없음) |
| `read_file` | 파일 읽기 | `path` |
| `write_file` | 파일 쓰기 | `path`, `content` |
| `restart_service` | systemctl 재시작 | `service` |

---

## 등록된 Skill 목록

| name | 설명 |
|------|------|
| `probe_linux_host` | hostname/uptime/커널/디스크/메모리/프로세스/포트 종합 수집 |
| `check_tls_cert` | TLS 인증서 유효기간/발급자 확인 |
| `collect_web_latency_facts` | HTTP 응답 시간 3회 측정 |
| `monitor_disk_growth` | 디렉토리 디스크 사용량 추세 분석 |
| `summarize_incident_timeline` | 시스템 오류 로그 타임라인 요약 |
| `analyze_wazuh_alert_burst` | Wazuh 보안 알림 급증 원인 분석 |

---

## 커스텀 Playbook 예시

### 보안 점검 Playbook

```bash
# 1. 생성
PB_ID=$(curl -s -X POST http://localhost:8000/playbooks \
  -d '{"name":"security-check","version":"1.0","description":"기본 보안 점검"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['playbook']['id'])")

# 2. Steps 추가
curl -X POST http://localhost:8000/playbooks/$PB_ID/steps \
  -d '{"step_order":1,"step_type":"skill","name":"probe_linux_host","ref_id":"probe_linux_host"}'

curl -X POST http://localhost:8000/playbooks/$PB_ID/steps \
  -d '{"step_order":2,"step_type":"skill","name":"check_tls_cert","ref_id":"check_tls_cert"}'

curl -X POST http://localhost:8000/playbooks/$PB_ID/steps \
  -d '{"step_order":3,"step_type":"tool","name":"run_command","ref_id":"run_command",
       "params":{"command":"ss -tlnp | grep LISTEN"}}'
```
