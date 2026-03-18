---
name: opsclaw
description: OpsClaw IT operations orchestration. Use for creating projects, running playbooks, checking incidents, managing assets, and all OpsClaw operational tasks. Invoke with /skill:opsclaw.
---

# OpsClaw Operations Skill

This skill guides you through OpsClaw operations via the Manager API at `http://127.0.0.1:8000`.

## Quick Status Check

```bash
# 전체 시스템 상태 한번에 확인
curl -s http://127.0.0.1:8000/health && \
curl -s http://127.0.0.1:8000/admin/health && \
curl -s "http://127.0.0.1:8000/incidents?status=open" | python3 -c "
import sys,json
d=json.load(sys.stdin)
items=d.get('items',[])
print(f'Open incidents: {len(items)}')
for i in items: print(f'  [{i[\"severity\"]}] {i[\"summary\"]}')
"
```

## Project 생성 & Playbook 실행 (전체 흐름)

사용자가 운영 작업을 요청하면 이 순서로 진행한다:

### 1단계: Playbook 목록 확인
```bash
curl -s http://127.0.0.1:8000/registry/playbooks | python3 -c "
import sys,json
for p in json.load(sys.stdin)['items']:
    print(f'{p[\"id\"]:30} {p[\"name\"]}')
"
```

### 2단계: Project 생성
```bash
PROJECT=$(curl -s -X POST http://127.0.0.1:8000/projects \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"<작업명>\",\"request_text\":\"<요청내용>\",\"requester\":\"operator\"}")
PROJECT_ID=$(echo $PROJECT | python3 -c "import sys,json; print(json.load(sys.stdin)['project']['id'])")
echo "Project ID: $PROJECT_ID"
```

### 3단계: Playbook 연결
```bash
curl -s -X POST "http://127.0.0.1:8000/projects/${PROJECT_ID}/playbooks/<PLAYBOOK_ID>"
```

### 4단계: Plan 수립
```bash
curl -s -X POST "http://127.0.0.1:8000/projects/${PROJECT_ID}/plan" \
  -H "Content-Type: application/json" \
  -d '{"plan_summary":"<왜 이 작업을 하는지, 무엇을 할 것인지>","steps":[]}'
```

### 5단계: Execute 전환
```bash
curl -s -X POST "http://127.0.0.1:8000/projects/${PROJECT_ID}/execute"
```

### 6단계: Dry-run으로 실행 계획 확인
```bash
curl -s -X POST "http://127.0.0.1:8000/projects/${PROJECT_ID}/playbook/run" \
  -H "Content-Type: application/json" \
  -d "{\"dry_run\":true,\"params\":{\"host\":\"<TARGET_HOST>\"}}" | python3 -c "
import sys,json
r=json.load(sys.stdin)['result']
print(f'Playbook: {r[\"playbook_name\"]}  Steps: {r[\"steps_total\"]}')
for s in r['step_results']:
    print(f'  [{s[\"order\"]}] {s[\"type\"]:6} {s[\"ref\"]:35} script preview: {s[\"script\"][:60]}')
"
```

**→ 사용자에게 dry_run 결과를 보여주고 실행 승인을 받아라.**

### 7단계: 실제 실행 (사용자 승인 후)
```bash
curl -s -X POST "http://127.0.0.1:8000/projects/${PROJECT_ID}/playbook/run" \
  -H "Content-Type: application/json" \
  -d "{\"dry_run\":false,\"subagent_url\":\"http://<SUBAGENT_HOST>:8001\",\"params\":{\"host\":\"<TARGET_HOST>\"}}" \
  | python3 -c "
import sys,json
r=json.load(sys.stdin)['result']
print(f'Status: {r[\"status\"]}  ok:{r[\"steps_ok\"]} failed:{r[\"steps_failed\"]} skipped:{r[\"steps_skipped\"]}')
for s in r['step_results']:
    status_icon = '✅' if s['status']=='ok' else ('⚠️' if s['status']=='dry_run' else '❌')
    print(f'  {status_icon} [{s[\"order\"]}] {s[\"ref\"]} ({s[\"duration_s\"]}s)')
    if s.get('analysis'):
        print(f'     분석: {s[\"analysis\"]}')
"
```

## Incidents 관리

```bash
# 미해결 인시던트 목록
curl -s "http://127.0.0.1:8000/incidents?status=open" | python3 -c "
import sys,json
items=json.load(sys.stdin).get('items',[])
for i in items:
    print(f'[{i[\"severity\"]:8}] {i[\"id\"]} | {i[\"summary\"][:60]}')
"

# 인시던트 해결
curl -s -X POST "http://127.0.0.1:8000/incidents/<INCIDENT_ID>/resolve"
```

## Assets 관리

```bash
# 자산 목록
curl -s http://127.0.0.1:8000/assets | python3 -c "
import sys,json
for a in json.load(sys.stdin).get('items',[]):
    print(f'{a[\"id\"]:20} {a[\"type\"]:20} {a[\"name\"]}')
"

# 새 자산 등록
curl -s -X POST http://127.0.0.1:8000/assets \
  -H "Content-Type: application/json" \
  -d '{"name":"server-01","type":"linux_server","connection_info":{"host":"192.168.1.100","port":22}}'
```

## SubAgent 직접 조작 (디버그용)

```bash
# 대상 서버 bash 실행
curl -s -X POST "http://<SUBAGENT>:8001/a2a/run_script" \
  -H "Content-Type: application/json" \
  -d '{"project_id":"debug","job_run_id":"d1","script":"hostname && uptime && df -h"}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['detail']['stdout'])"

# 대상 서버 LLM 분석
curl -s -X POST "http://<SUBAGENT>:8001/a2a/analyze" \
  -H "Content-Type: application/json" \
  -d '{"project_id":"debug","job_run_id":"d2","command_output":"<OUTPUT>","question":"<QUESTION>"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['analysis'])"

# 도구 설치
curl -s -X POST "http://<SUBAGENT>:8001/a2a/install_tool" \
  -H "Content-Type: application/json" \
  -d '{"project_id":"debug","job_run_id":"d3","tool_name":"nmap","method":"apt"}'
```

## 운영 규칙 (반드시 준수)

1. **dry_run 먼저** — 모든 Playbook 실행은 dry_run으로 계획 확인 후 승인 받기
2. **고위험 작업 승인** — restart_service, patch_wave, write_file은 반드시 사용자 확인
3. **상태 먼저 확인** — 작업 전 /admin/health 확인
4. **Playbook 외 임의 실행 금지** — 시스템 일관성을 위해 등록된 Playbook 사용
5. **evidence 확인** — 실행 후 evidence_id가 있는지 확인 (증빙 없으면 완료 불가)
