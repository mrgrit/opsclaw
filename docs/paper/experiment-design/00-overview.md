# OpsClaw 논문 실험 설계 — 에이전트 하네스 우수성 입증

**작성일:** 2026-03-25
**대상 시스템:** OpsClaw v0.10 (M0~M26, 공개 저장소)
**실험 환경:** 4대 서버 (opsclaw/secu/web/siem), 실운영 인프라
**비교 대상:** AutoGPT, CrewAI, LangChain Agents (문헌 기반)

---

## 논문 제목 (안)

**"OpsClaw: 작업증명 기반 자기강화형 IT 운영 자동화 에이전트 하네스"**

영문: *"OpsClaw: A Self-Improving Agent Harness for IT Operations Automation with Proof-of-Work Verification and Reinforcement Learning"*

---

## OpsClaw의 핵심 우수성 5가지

| # | 우수성 | 기존 프레임워크 | OpsClaw |
|---|--------|---------------|---------|
| **U1** | 작업 증명 가능성 | 로그만 남김, 위변조 검증 불가 | PoW 블록체인 + 해시 체인 무결성 검증 |
| **U2** | 자기강화 학습 | 보상 체계 없음, 정적 동작 | Q-learning + UCB1 탐색 → 정책 자동 개선 |
| **U3** | 경험 축적 및 재활용 | 대화 히스토리 수준 | 4-Layer Memory → RAG 기반 경험 검색 |
| **U4** | 결정론적 실행 | LLM 의존 → 매번 다른 결과 | Playbook 기반 스크립트 생성, 재현율 >95% |
| **U5** | 병렬 멀티에이전트 | 순차 실행 또는 수동 관리 | task별 SubAgent 라우팅 + 병렬 dispatch |

---

## 실험 구성 (8개 실험, 5개 우수성 입증)

```
U1 → 실험 A (체인 무결성), 실험 H (시간대 불변성)
U2 → 실험 B (RL 수렴 + 커버리지)
U3 → 실험 C (증거 완전성), 실험 D (경험 재활용 효과)
U4 → 실험 G (Playbook 재현성)
U5 → 실험 F (병렬 스케일링)
추가 → 실험 E (상태 머신 유효성)
```

---

## 실험 목록

| 실험 | 파일 | 입증 대상 | 자동화 |
|------|------|---------|--------|
| A. 체인 무결성 검증 | `01-chain-integrity.md` | U1 | 스크립트 |
| B. RL 정책 수렴 + UCB1 커버리지 | `02-rl-convergence.md` | U2 | 스크립트 |
| C. 증거 완전성 감사 | `03-evidence-completeness.md` | U3 | 스크립트 |
| D. 경험 재활용 효과 (A/B) | `04-experience-reuse.md` | U3 | 수동+스크립트 |
| E. 상태 머신 유효성 | `05-state-machine.md` | 기반 | 스크립트 |
| F. 병렬 스케일링 | `06-parallel-scaling.md` | U5 | 스크립트 |
| G. Playbook 재현성 | `07-playbook-determinism.md` | U4 | 스크립트 |
| H. PoW 시간대 불변성 | `08-temporal-invariance.md` | U1 | 스크립트 |
