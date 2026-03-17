# M9 완료 보고서: RBAC / Audit / Monitoring / Reporting / Backup

**완료일**: 2026-03-18
**담당**: Claude Code
**기준 커밋**: (M9 커밋 후 기재)

---

## 1. 목표

M9 목표는 OpsClaw 플랫폼을 운영 환경에서 실제로 사용 가능한 수준으로 강화하는 것이다.

- **RBAC**: 역할 기반 접근 제어 (roles + actor_roles 테이블)
- **Audit**: 감사 로그 기록 + JSON/CSV 내보내기
- **Monitoring**: 시스템 헬스/메트릭 집계
- **Reporting**: 프로젝트 전체 보고서 + evidence pack 내보내기
- **Backup**: pg_dump 기반 DB 백업

---

## 2. 구현 내역

### 2.1 DB 마이그레이션 (`migrations/0005_rbac.sql`)

```sql
CREATE TABLE roles (id UUID PK, name TEXT UNIQUE, permissions JSONB, ...);
CREATE TABLE actor_roles (id UUID PK, actor_id TEXT, actor_type TEXT, role_id UUID FK, ...);
```

시드 데이터: `admin (*), operator, viewer, auditor` 4개 기본 역할 자동 삽입.

---

### 2.2 `packages/audit_service/__init__.py`

| 함수 | 설명 |
|------|------|
| `log_audit_event(event_type, actor_type, actor_id, ...)` | audit_logs INSERT |
| `query_audit_logs(event_type, actor_id, project_id, asset_id, limit)` | 다중 필터 조회 |
| `get_audit_event(log_id)` | 단건 조회 |
| `export_audit_json(...)` | JSON 문자열 내보내기 |
| `export_audit_csv(...)` | CSV 문자열 내보내기 (헤더 포함) |

---

### 2.3 `packages/rbac_service/__init__.py`

| 함수 | 설명 |
|------|------|
| `create_role / get_role / get_role_by_name / list_roles` | 역할 CRUD |
| `update_role_permissions / delete_role` | 역할 수정/삭제 |
| `assign_role(actor_id, role_id)` | ON CONFLICT DO UPDATE (멱등) |
| `revoke_role / get_actor_roles` | 할당 관리 |
| `get_actor_permissions(actor_id)` | 모든 역할 permissions 병합 |
| `check_permission(actor_id, permission)` | `*` 권한 및 정확 일치 체크 |

---

### 2.4 `packages/monitoring_service/__init__.py`

| 함수 | 설명 |
|------|------|
| `get_system_health()` | projects/assets/incidents/schedules/watchers/evidence 상태 집계, `status=healthy/degraded` |
| `get_operational_metrics()` | evidence 성공률, validation 통과율, 7일 집계, top assets, audit 통계 |

---

### 2.5 `packages/reporting_service/__init__.py`

| 함수 | 설명 |
|------|------|
| `generate_project_report(project_id)` | 프로젝트 전체 데이터 집계 (assets/evidence/validation/reports/job_runs/master_reviews/task_memory) |
| `export_evidence_pack(project_id)` | 컴플라이언스용 evidence pack dict |
| `export_evidence_pack_json(project_id)` | JSON 문자열 |

---

### 2.6 `packages/backup_service/__init__.py`

| 함수 | 설명 |
|------|------|
| `create_backup(backup_dir)` | pg_dump 실행 → `opsclaw_backup_{timestamp}.sql` |
| `list_backups(backup_dir)` | 백업 파일 목록 (mtime 내림차순) |
| `get_backup_info(backup_path)` | 단건 파일 정보 |

---

### 2.7 Manager API (`apps/manager-api/src/main.py`) — 버전 `0.9.0-m9`

**`/admin` 라우터 (create_admin_router):**

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/admin/health` | 시스템 헬스 |
| GET | `/admin/metrics` | 운영 메트릭 |
| GET | `/admin/audit` | 감사 로그 조회 |
| POST | `/admin/audit/export` | 감사 로그 내보내기 |
| GET | `/admin/roles` | 역할 목록 |
| POST | `/admin/roles` | 역할 생성 |
| GET | `/admin/roles/{role_id}` | 역할 단건 |
| POST | `/admin/roles/assign` | 역할 부여 |
| GET | `/admin/roles/actor/{actor_id}/permissions` | 권한 목록 |
| GET | `/admin/roles/actor/{actor_id}/check` | 권한 확인 |
| POST | `/admin/backup` | 백업 실행 |
| GET | `/admin/backups` | 백업 목록 |

**`/reports` 라우터 (create_reports_router):**

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/reports/project/{id}` | 프로젝트 전체 보고서 |
| GET | `/reports/project/{id}/evidence-pack` | Evidence pack dict |
| GET | `/reports/project/{id}/evidence-pack/json` | Evidence pack JSON |

---

## 3. 검증 결과

### M9 smoke test: 35/35 passed

| 섹션 | 항목 | 결과 |
|------|------|------|
| A. audit_service unit | 1–7 | 7/7 PASS |
| B. rbac_service unit | 8–15 | 8/8 PASS |
| C. monitoring_service unit | 16–20 | 5/5 PASS |
| D. reporting_service unit | 21–25 | 5/5 PASS |
| E. backup_service unit | 26–28 | 3/3 PASS |
| F. Manager API /admin + /reports | 29–35 | 7/7 PASS |

### 회귀 테스트

| 테스트 | 결과 |
|--------|------|
| pre_m7_smoke | 30/30 PASS |
| m6_integrated_smoke | 14/14 PASS |
| m7_integrated_smoke | 35/35 PASS |
| m8_integrated_smoke | 35/35 PASS |

---

## 4. 변경 파일 목록

| 파일 | 작업 |
|------|------|
| `migrations/0005_rbac.sql` | 신규 — roles + actor_roles + 시드 |
| `packages/audit_service/__init__.py` | 신규 패키지 |
| `packages/rbac_service/__init__.py` | 신규 패키지 |
| `packages/monitoring_service/__init__.py` | 신규 패키지 |
| `packages/reporting_service/__init__.py` | 구현 완료 (기존 비어있음) |
| `packages/backup_service/__init__.py` | 신규 패키지 |
| `apps/manager-api/src/main.py` | /admin + /reports 라우터 추가, v0.9.0-m9 |
| `tools/dev/m9_integrated_smoke.py` | 신규 (35개 항목) |
| `docs/m9/opsclaw-m9-completion-report.md` | 본 문서 |
| `README.md` | M9 완료 반영 |

---

## 5. 완료 기준 달성

- [x] 35/35 M9 smoke 항목 통과
- [x] 기존 pre_m7 30/30, m6 14/14, m7 35/35, m8 35/35 유지
- [x] 0005_rbac.sql 마이그레이션 적용
- [x] 5개 M9 서비스 패키지 구현
- [x] Manager API v0.9.0-m9 12개 /admin + 3개 /reports 엔드포인트
- [x] docs/m9 완료 보고서
- [x] README.md M9 완료 반영
- [x] git commit + push
