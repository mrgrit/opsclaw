# OldClaw M0 Design Baseline

## 목적
- OldClaw 프로젝트 초기 설계 기반을 고정하기 위한 문서.
- 설계 원칙, 책임 경계, 핵심 데이터 모델을 명확히 정의한다.

## 설계 이유
- 계획서 v2에 정의된 **Asset‑first**, **Evidence‑first**, **Master‑Manager‑SubAgent** 구조를 구현하기 위한 기준점.

## 책임 경계
- **pi_adapter**: pi 런타임과의 통신만 담당.
- **core**: 도메인 엔티티, 애플리케이션 서비스, 인프라스트럭처.
- **apps/**: 각각 실행 가능한 서비스 (manager, master, subagent).

## 관련 디렉터리/모듈
- `packages/core/`
- `packages/pi_adapter/`
- `apps/manager-api/`
- `apps/master-service/`
- `apps/subagent-runtime/`

## 핵심 데이터 구조
- `assets`, `targets`, `projects`, `job_runs`, `evidence`, `validation_runs` 등은 **asset‑first**와 **evidence‑first** 원칙을 반영한다.

## 향후 구현 연결점
- M1: pi_adapter 구현
- M2: manager graph & project lifecycle
- M3: subagent runtime

## 의도적 미이행 항목 (다음 마일스톤으로 넘김)
- 실제 API 구현
- LangGraph 상태 머신 정의
- Scheduler / Watcher 구현
