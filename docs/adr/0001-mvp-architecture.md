# ADR-0001: OpsClaw MVP 아키텍처

## 상태
승인 대기 (Proposed)

## 결정
- Manager는 Python 기반 단일 프로세스 오케스트레이터로 시작한다.
- SubAgent는 명령 실행기(실행/타임아웃/결과 수집)를 최소 기능으로 구현한다.
- 상태 저장은 SQLite + JSON artifact 혼합으로 시작한다.
- 외부 Master 호출 전 MasterGate를 필수 통과시킨다.

## 근거
- 빠른 MVP 출시와 폐쇄망 배포 단순화
- 추후 gRPC/메시지 브로커/분산 확장이 가능

## 결과
- Sprint A에서 end-to-end 실행 경로를 확보한다.
- Sprint B에서 정책/보안 게이트를 강화한다.
