# OpsClaw M6 Completion Report

## 1. M6 목표

- Skill/Playbook Registry 전체 CRUD 구현 (Tool / Skill / Playbook)
- Seed loader: YAML 정의 → PostgreSQL upsert
- 10개 핵심 playbook 정의 (YAML)
- Composition engine: playbook → step → skill → tool 전체 트리 resolve
- Explain mode: 사람이 읽을 수 있는 playbook 설명 렌더링
- Manager API에 registry 라우터 완성

---

## 2. 실제 반영한 것

### packages/registry_service/__init__.py (신규)

**Tools**
- `upsert_tool()`: ON CONFLICT(name, version) DO UPDATE
- `get_tool()`, `get_tool_by_name()`, `list_tools(enabled 필터)`

**Skills**
- `upsert_skill()`: required_tools / optional_tools JSON 저장
- `get_skill()`, `get_skill_by_name()`, `list_skills(category 필터)`

**Playbooks**
- `upsert_playbook()`: execution_mode / risk_level / dry_run_supported 포함
- `get_playbook()`, `get_playbook_by_name()`, `list_playbooks(category, enabled 필터)`
- `upsert_playbook_steps()`: DELETE + re-INSERT 방식으로 멱등 갱신
- `get_playbook_steps()`: order 정렬

**Composition & Explain**
- `resolve_playbook()`: step → skill/tool 전체 참조 트리 반환
- `explain_playbook()`: 마크다운 형식 사람 가독 설명 반환

### seed/playbooks/ — 10개 YAML 파일

| 파일명 | 카테고리 | risk |
|---|---|---|
| cleanup_disk_usage.yaml | reliability | low |
| diagnose_db_performance.yaml | reliability | low |
| diagnose_web_latency.yaml | reliability | low |
| investigate_compromise.yaml | security | critical |
| monitor_siem_and_raise_incident.yaml | security | medium |
| nightly_health_baseline_check.yaml | reliability | low |
| onboard_new_linux_server.yaml | operations | medium |
| patch_wave.yaml | operations | high |
| renew_certificate.yaml | operations | medium |
| tune_siem_noise.yaml | security | low |

각 YAML: name / version / category / description / execution_mode / risk_level / dry_run_supported / steps[]

### tools/dev/seed_loader.py (신규)

- `--dry-run` 플래그 지원
- tools / skills / playbooks YAML → DB upsert
- 실행 결과: 6 tools, 6 skills, 10 playbooks 적재 확인

### apps/manager-api/src/main.py (수정 — registry 라우터)

stub `create_playbook_router()` → 전체 `create_registry_router()`로 대체:

| 메서드 | 경로 | 기능 |
|---|---|---|
| GET | /tools | 도구 목록 (enabled 필터) |
| GET | /tools/{id} | 도구 단건 (이름 우선, id 폴백) |
| GET | /skills | 스킬 목록 (category 필터) |
| GET | /skills/{id} | 스킬 단건 |
| GET | /playbooks | 플레이북 목록 (category, enabled 필터) |
| GET | /playbooks/{id} | 플레이북 단건 |
| GET | /playbooks/{id}/steps | 플레이북 스텝 목록 |
| GET | /playbooks/{id}/resolve | Composition 트리 |
| GET | /playbooks/{id}/explain | 마크다운 설명 |

---

## 3. 테스트 결과

| 스크립트 | 결과 |
|---|---|
| `tools/dev/m6_integrated_smoke.py` | 14/14 통과 |

검증 범위: tools/skills/playbooks 목록 · 필터 · 이름/ID 단건 조회 · steps · resolve · explain · 404 guard

---

## 4. 한계 및 다음 단계로 넘기는 것

- seed/playbooks의 tool/skill ref는 이름 기반; DB에 해당 이름이 없으면 resolve 시 빈 참조
- 실행 엔진(playbook → 실제 명령 실행)은 M7 Batch Execution에서 구현 예정
- dry_run 실제 실행 분기 로직 미구현
