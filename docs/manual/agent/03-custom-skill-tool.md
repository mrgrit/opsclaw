# 커스텀 Skill / Tool / Playbook 추가 가이드

## 개념 정리

| 개념 | 단위 | 설명 |
|------|------|------|
| **Tool** | 단일 명령 | 실행 가능한 shell 명령/스크립트 단위 |
| **Skill** | Tool 조합 | 특정 목적을 달성하는 절차 단위 |
| **Playbook** | Step 목록 | Skill/Tool을 순서대로 실행하는 작업 템플릿 |
| **Experience** | 과거 결과 | 작업 완료 후 축적되는 패턴/교훈 |

---

## Tool 추가

### API로 등록

```bash
POST /tools
{
  "name": "check_port",
  "description": "특정 포트 리스닝 여부 확인",
  "script_template": "ss -tlnp | grep :{port}",
  "params_schema": {
    "port": {"type": "integer", "description": "확인할 포트 번호"}
  },
  "tags": ["network", "diagnostics"]
}
```

### 스크립트 템플릿 작성 규칙

- `{변수명}` 형식으로 params 참조
- bash 문법 사용
- 대화형 입력 없이 완결되어야 함

예시:
```bash
# run_command 스타일
"script_template": "{command}"

# 파라미터 조합
"script_template": "tail -n {lines} {log_path}"

# 다중 명령
"script_template": "systemctl stop {service} && sleep 2 && systemctl start {service} && systemctl status {service}"
```

### Seed YAML로 일괄 등록

`seed/tools/` 디렉토리에 YAML 파일 추가:

```yaml
# seed/tools/custom_tools.yaml
- name: check_port
  description: "포트 리스닝 확인"
  script_template: "ss -tlnp | grep :{port}"
  params_schema:
    port:
      type: integer

- name: get_process_info
  description: "프로세스 정보 조회"
  script_template: "ps aux | grep {process_name} | grep -v grep"
  params_schema:
    process_name:
      type: string
```

```bash
PYTHONPATH=. .venv/bin/python3 tools/dev/seed_loader.py
```

---

## Skill 추가

### API로 등록

```bash
POST /skills
{
  "name": "check_service_health",
  "description": "서비스 상태 종합 점검 (포트, 프로세스, 로그 오류)",
  "required_tools": ["check_port", "run_command", "fetch_log"],
  "optional_tools": ["query_metric"],
  "script_template": "# check_service_health\nPORT={port}\nSERVICE={service}\n\necho '=== 포트 확인 ==='\nss -tlnp | grep :$PORT\n\necho '=== 프로세스 확인 ==='\nps aux | grep $SERVICE | grep -v grep\n\necho '=== 최근 오류 로그 ==='\njournalctl -u $SERVICE --since '1 hour ago' | grep -i error | tail -20",
  "params_schema": {
    "port": {"type": "integer"},
    "service": {"type": "string"}
  }
}
```

### Skill 스크립트 작성 요령

- `# === 섹션명 ===` 형식으로 출력 구분
- 각 섹션이 독립적으로 실행 가능해야 함
- 실패해도 다음 섹션 계속 실행: `command || true`

```bash
#!/bin/bash
echo "=== probe_linux_host: {hostname} ==="

echo "--- 기본 정보 ---"
hostname && uname -r && uptime

echo "--- 디스크 ---"
df -h

echo "--- 메모리 ---"
free -m

echo "--- 주요 프로세스 ---"
ps aux --sort=-%cpu | head -10

echo "--- 리스닝 포트 ---"
ss -tlnp | grep LISTEN
```

---

## Playbook 추가

### 단계별 등록

```bash
# 1. Playbook 생성
PB_ID=$(curl -s -X POST http://localhost:8000/playbooks \
  -H "Content-Type: application/json" \
  -d '{
    "name": "service-health-full",
    "version": "1.0",
    "description": "서비스 종합 헬스체크",
    "risk_level": "low",
    "dry_run_supported": true,
    "execution_mode": "sequential"
  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['playbook']['id'])")

# 2. Steps 추가
curl -X POST http://localhost:8000/playbooks/$PB_ID/steps \
  -d '{"step_order":1,"step_type":"skill","name":"probe_linux_host","ref_id":"probe_linux_host"}'

curl -X POST http://localhost:8000/playbooks/$PB_ID/steps \
  -d '{"step_order":2,"step_type":"skill","name":"check_service_health","ref_id":"check_service_health",
       "params":{"port":80,"service":"nginx"}}'

curl -X POST http://localhost:8000/playbooks/$PB_ID/steps \
  -d '{"step_order":3,"step_type":"tool","name":"fetch_log","ref_id":"fetch_log",
       "params":{"log_path":"/var/log/nginx/error.log","lines":50}}'
```

### Seed YAML로 일괄 등록

```yaml
# seed/playbooks/service_health_full.yaml
name: service-health-full
version: "1.0"
description: "서비스 종합 헬스체크"
risk_level: low
steps:
  - step_order: 1
    step_type: skill
    name: probe_linux_host
    ref_id: probe_linux_host
  - step_order: 2
    step_type: skill
    name: check_service_health
    ref_id: check_service_health
    params:
      port: 80
      service: nginx
```

---

## Experience 활용

작업 완료 후 Experience를 생성하면 이후 유사 작업에서 자동 참조된다.

```bash
# Experience 생성 (완료보고서 기반 자동 생성됨)
GET /projects/{id}/experience    # 이미 생성된 experience 조회

# 수동 생성
POST /experience
{
  "title": "Nginx 설치 성공 패턴",
  "content": "Ubuntu 22.04에서 nginx 설치: apt-get update -y && apt-get install -y nginx && systemctl enable --now nginx",
  "tags": ["nginx", "installation", "ubuntu"],
  "outcome": "success"
}

# 검색 (새 작업 계획 수립 시 참조)
GET /experience/search?q=nginx+설치
```

---

## Tool/Skill 실행 테스트

등록 후 즉시 테스트:

```bash
# Tool 실행 테스트 (dispatch로 직접 확인)
PROJECT_ID=<테스트용 project_id>

curl -X POST http://localhost:8000/projects/$PROJECT_ID/dispatch \
  -d '{"command":"ss -tlnp | grep :80","subagent_url":"http://localhost:8002"}'

# Skill을 Playbook으로 묶어 dry_run 테스트
curl -X POST http://localhost:8000/projects/$PROJECT_ID/playbook/run \
  -d '{"dry_run":true,"subagent_url":"http://localhost:8002"}'
```
