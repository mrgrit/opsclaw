# 실험 E 결과: 상태 머신 유효성 검증

**실행일:** 2026-03-25
**프로젝트:** prj_f1e22ff1a2d5

## 결과 요약

| 지표 | 결과 | 기대값 | 판정 |
|------|------|--------|------|
| 무효 전이 차단율 | **100%** (5/5 차단) | 100% | **PASS** |
| 유효 전이 성공율 | **100%** (3/3 성공) | 100% | **PASS** |
| Replan 후 복구 | **성공** (failed→plan→execute→success) | 성공 | **PASS** |

## 상세 결과

### Phase 2: 전이 테스트

| 전이 | 유효성 | HTTP 코드 | 판정 |
|------|--------|---------|------|
| intake → plan | 유효 | 200 | OK |
| plan → validate | **무효** | **400** | 차단됨 |
| plan → close | **무효** | **400** | 차단됨 |
| plan → report/finalize | **무효** | **400** | 차단됨 |
| plan → execute | 유효 | 200 | OK |
| execute → plan (직접) | **무효** | **400** | 차단됨 |
| execute → close | **무효** | **400** | 차단됨 |

### Phase 3: Replan 복구

| 단계 | 결과 |
|------|------|
| 의도적 실패 실행 | overall=failed |
| replan 호출 | 200 (성공) |
| replan 후 stage | plan (execute→plan 복귀) |
| 재실행 (execute + execute-plan) | overall=success |

## 결론

OpsClaw의 LangGraph 기반 상태 머신은:
1. 무효 상태 전이를 **100% 차단**
2. replan을 통한 실패 복구가 정상 작동
3. 전이 규칙: intake→plan→execute→validate→report→close (bypass: plan→execute 허용)
