# OldClaw M1 Next TODO

## 목표
M1 단계에서는 **M0에서 고정된 설계·스키마** 를 기반으로 실제 실행 로직과 정책/검증 엔진을 구현한다.

## 주요 작업 리스트
1. **Policy Engine** 구현
   - 정책 DSL 파싱 및 적용
   - `policy_engine` 패키지에 검증 로직 추가
2. **pi Runtime 연동**
   - `packages/pi_adapter/runtime/` 에 모델 프로파일 로딩 구현
   - 세션 관리 및 Tool Bridge 실제 호출 구현
3. **서비스 비즈니스 로직**
   - `master-service` 에 검토·리플랜·Escalation 흐름 구현
   - `scheduler-worker` 와 `watch-worker` 에 잡 스케줄링·감시 루프 구현
4. **인덱스·성능 튜닝**
   - 주요 쿼리 프로파일링 후 복합 인덱스 추가
   - `audit_logs`, `messages` 등에 TTL 정책 적용
5. **테스트 커버리지**
   - unit / integration 테스트 작성
   - CI 파이프라인에 pytest + coverage 연동
6. **문서 정리**
   - M1 설계 문서(`docs/m1/`) 작성
   - API 계약 버전 관리 정책 수립

## 넘어갈 항목 (M0에서 미완성)
- 상세 정책 정의 및 바인딩 메커니즘
- 고도화된 검증/리포팅 파이프라인
- 모델 프로파일·세션 구체화
- 복합 인덱스·성능 최적화

---
*임의 적용*: 작업 순서는 프로젝트 리소스 상황에 따라 조정될 수 있습니다.*
