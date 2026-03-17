# OpsClaw M4 Completion Report

## 1. M4 목표

- Asset Registry 전체 CRUD 구현
- 신규 자산 온보딩 워크플로우 (identity check → create → bootstrap → resolve)
- 자산으로부터 Target 자동 도출 (subagent ping → target upsert)
- Manager API에 asset 전용 라우터 완성

---

## 2. 실제 반영한 것

### packages/asset_registry/__init__.py (신규)

**기본 CRUD**
- `create_asset()`: 이름 중복 시 `AssetConflictError`, PostgreSQL INSERT
- `get_asset()`: ID 기반 조회, 없으면 `AssetNotFoundError`
- `get_asset_by_name()`: 이름 기반 조회
- `update_asset()`: partial update (지정 필드만 SET)
- `delete_asset()`: 물리 삭제
- `list_assets()`: env/type 필터 지원

**Target Resolution**
- `resolve_target_from_asset()`: subagent health 확인 → `targets` 테이블 upsert → `subagent_status` 갱신
- `check_asset_health()`: ping only, target upsert 없음

**Onboarding**
- `onboard_asset()`: 이름 중복 확인 → create → (옵션) bootstrap → resolve → 결과 반환

### apps/manager-api/src/main.py (수정 — asset 라우터)

| 메서드 | 경로 | 기능 |
|---|---|---|
| GET | /assets | 목록 조회 (env, type 필터) |
| POST | /assets | 자산 생성 |
| POST | /assets/onboard | 온보딩 워크플로우 |
| GET | /assets/{id} | 단건 조회 |
| PUT | /assets/{id} | 수정 |
| DELETE | /assets/{id} | 삭제 |
| POST | /assets/{id}/resolve | Target 도출 |
| GET | /assets/{id}/health | SubAgent ping 확인 |
| POST | /assets/{id}/bootstrap | 원격 bootstrap 실행 |

---

## 3. 테스트 결과

| 스크립트 | 결과 |
|---|---|
| `tools/dev/asset_registry_smoke.py` | 12/12 통과 |
| `tools/dev/manager_asset_crud_http_smoke.py` | 10/10 통과 |

---

## 4. 한계 및 다음 단계로 넘기는 것

- `resolve_target_from_asset()`의 subagent ping은 실 네트워크 없이는 unreachable로 처리됨
- bootstrap은 SSH 접근 가능한 환경에서만 동작
- asset의 `subagent_status` 갱신은 ping 결과에만 의존; 실 health check 로직은 확장 필요
