# OpsClaw M3 Completion Report

## 1. M3 목표

- A2A(Agent-to-Agent) 실행 경로 확립: Manager → SubAgent HTTP dispatch
- SubAgent 런타임에 실제 subprocess 실행 구현
- 원격 호스트에 SubAgent를 자동 설치하는 Bootstrap 서비스 구현
- Evidence gate: close 전에 반드시 evidence가 존재해야 하는 정책 적용
- Replan: execute/validate/report 단계에서 plan으로 되돌리는 경로 확보

---

## 2. 실제 반영한 것

### packages/a2a_protocol/__init__.py (신규)
- `A2ARunRequest`, `A2ARunResult`, `A2AError`, `A2AClientConfig`, `A2AClient`
- `A2AClient.run_script()`: `POST /a2a/run_script` 호출 → 결과 반환
- timeout, error handling, HTTP status 처리 포함

### apps/subagent-runtime/src/main.py (수정)
- `/a2a/run_script` 엔드포인트: 501 stub → `subprocess.run()` 실제 실행
- `timeout_s` 파라미터 준수, `TimeoutExpired` 처리
- stdout/stderr/exit_code/status 반환

### packages/bootstrap_service/__init__.py (신규)
- `BootstrapConfig`, `BootstrapError`, `bootstrap_asset()`
- SSH(`-o StrictHostKeyChecking=no`)로 원격 접속 후 `install.sh` 파이프 실행

### deploy/bootstrap/install.sh (신규)
- Python3 가용성 확인 → pip 설치 → 의존성 설치
- `/opt/opsclaw/subagent_main.py` 작성
- systemd 서비스(`opsclaw-subagent.service`) 등록 및 시작

### packages/project_service/__init__.py (수정)
- `dispatch_command_to_subagent()`: project execute 단계에서 SubAgent로 명령 전송
- `update_asset_subagent_status()`: 실행 결과 기반으로 asset subagent_status 갱신
- `replan_project()`: execute/validate/report → plan 전이 (이유 기록)
- `close_project()`: evidence gate 적용 — evidence 0건이면 `ProjectStageError` 발생

### packages/pi_adapter/runtime/__init__.py (수정)
- `PiAdapterError` 누락 export 수정 (ImportError 해결)

---

## 3. 테스트 결과

| 스크립트 | 결과 |
|---|---|
| `tools/dev/subagent_a2a_smoke.py` | 5/5 통과 |
| `tools/dev/manager_dispatch_smoke.py` | 5/5 통과 |

---

## 4. 한계 및 다음 단계로 넘기는 것

- SSH 기반 bootstrap은 실 환경에서 SSH 키 설정이 필요함
- A2A dispatch는 project_service에서 subagent_url을 수동으로 지정해야 함 (자동 resolve는 M4에서 구현)
- evidence gate는 최소 1건 존재 여부만 확인; 내용 검증은 M5에서 구현
