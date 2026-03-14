# OldClaw M1 Next TODO

## 목표
- pi runtime을 OldClaw 서비스에 안전하게 임베드한다.
- pi_adapter 경계 정의 및 초기 구현 (model profile, tool bridge, session wrapper).
- Manager 가 pi 를 통해 tool 호출 가능하도록 API 설계.

## 주요 작업 항목
1. **packages/pi_adapter/**
   - `runtime/` : pi Session 생성/제어 래퍼
   - `tools/` : pi tool 호출 트랜슬레이션
   - `model_profiles/` : Master / Manager / SubAgent 별 모델 설정 파일
   - `translators/` : OldClaw DTO ↔ pi DTO 변환
2. **apps/manager-api**에 piAdapter 의 DI (Dependency Injection) 추가.
3. **tests/**에 pi_adapter mock 테스트 작성.
4. Dockerfile 업데이트: pi runtime 의 python 의존성 (`pip install pi-mono`) 포함.
5. 문서화: `docs/m1/`에 설계 상세와 인터페이스 정의.

## 미결 사항 (M0에서 보류)
- 실제 **LangGraph** 상태 머신 정의 (M2).
- SubAgent bootstrap 스크립트 (M3).
- Scheduler / Watcher 상세 설계 (M7).

## 다음 회의 안건
- pi_adapter 의 구체적인 인터페이스 (async call, timeout, streaming stdout) 합의.
- 초기 모델 프로파일 (gpt‑4‑turbo, gpt‑4‑o‑mini 등) 선택.

---
*Prepared by the coding agent based on OldClaw v2 plan.*
