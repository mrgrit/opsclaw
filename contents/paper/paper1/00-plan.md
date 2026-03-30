# Paper 1 상세 계획

## 제목
**OpsClaw: PoW 블록체인 기반 자기 개선형 에이전트 하네스 아키텍처**

OpsClaw: A Self-Improving Agent Harness Architecture with Proof-of-Work Blockchain Verification

---

## 핵심 연구 질문 (Research Questions)

| RQ | 질문 | 검증 실험 |
|----|------|---------|
| RQ1 | PoW 해시 체인으로 에이전트 실행 증적의 위변조를 완전히 탐지할 수 있는가? | 실험 A, H |
| RQ2 | 강화학습(Q-learning + UCB1)이 에이전트 위험도 정책을 자율적으로 수렴시킬 수 있는가? | 실험 B |
| RQ3 | Playbook 기반 실행이 LLM 에이전트의 비결정론 문제를 해결하는가? | 실험 G |
| RQ4 | 3계층 위임 아키텍처가 병렬 확장성과 증거 완전성을 동시에 보장하는가? | 실험 C, E, F |
| RQ5 | 경험 메모리(RAG)가 반복 실행의 품질을 개선하는가? | 실험 D |

---

## 논문 구성 및 섹션별 계획

### Abstract (~200 words)
- 문제: 단독 LLM 에이전트의 증적·재현성·학습 부재
- 제안: OpsClaw 하네스 (3계층 + PoW + RL + Playbook + 4-Layer Memory)
- 결과: 위변조 탐지 100%, RL epoch 5 수렴, 재현율 100%, 병렬 4.0x, 증거 완전 100%
- 의의: 감사 가능하고 자기 개선하는 에이전트 하네스의 첫 실증

### 1. Introduction (~1.5 pages)
- 1.1 연구 배경: LLM 에이전트의 IT 운영 자동화 확산과 한계
- 1.2 기존 연구 한계: 3가지 간극 (증적 무결성, 보안 운용 통합, 자율 개선)
- 1.3 제안 시스템: OpsClaw 4대 메커니즘
- 1.4 주요 기여: C1~C4
- 1.5 논문 구성
- **파일:** `01-introduction.md` (기존 `00-introduction.md` 이동)

### 2. Related Work (~1.5 pages)
- 2.1 AI 에이전트 오케스트레이션 프레임워크
  - AutoGPT, CrewAI, LangChain Agents, MetaGPT
  - 한계: 증적 없음, 비결정론, RL 없음
- 2.2 Infrastructure as Code (IaC)
  - Ansible, Terraform, Puppet
  - 한계: LLM 기반 동적 계획 불가
- 2.3 블록체인 기반 감사 추적
  - Hyperledger, 실행 로그 블록체인 기록 연구
  - 한계: IT 운영 에이전트와의 통합 사례 부재
- 2.4 시스템 관리를 위한 강화학습
  - DeepRM, Decima, RL for cloud scheduling
  - 한계: 보안 운용 위험도 정책에 미적용
- 2.5 에이전트 메모리 및 경험 학습
  - Generative Agents (Park et al.), MemGPT
  - 한계: 운영 컨텍스트의 구조화된 메모리 부재
- **파일:** `02-related-work.md`

### 3. System Architecture (~2 pages)
- 3.1 설계 원칙
  - 위임 분리 (Delegation Separation)
  - 증적 일체화 (Evidence-First)
  - 정책 자율 개선 (Self-Improving Policy)
- 3.2 3계층 아키텍처 개요
  - Master (LLM): 계획 수립, 재계획, 최종 검토
  - Manager: 프로젝트 라이프사이클, 증적, 보상, 오케스트레이션
  - SubAgent: 명령 실행, 파일 조작, 헬스 체크
  - 아키텍처 다이어그램
- 3.3 8단계 상태 머신
  - created → planning → planned → executing → executed → reviewing → completed/failed
  - replan 루프, 무효 전이 차단
  - 상태 전이 다이어그램
- 3.4 개념 계층 (Concept Hierarchy)
  - Tool (원자적) → Skill (재사용) → Playbook (절차) → Project (라이프사이클)
- 3.5 서비스 경계
  - manager-api(:8000), master-service(:8001), subagent-runtime(:8002)
  - scheduler-worker, watch-worker
- **파일:** `03-architecture.md`
- **참고:** `docs/m0/opsclaw-m0-design-baseline.md`

### 4. Design & Implementation (~2.5 pages)
- 4.1 PoW 블록체인
  - 블록 구조: block_id, project_id, task_order, nonce, block_hash, prev_hash, ts_raw
  - generate_proof(): SHA-256 + difficulty 기반 nonce 탐색
  - verify_chain(): linked-list 순회, orphan 분류
  - Advisory lock을 통한 동시성 제어
  - **핵심 수도코드 포함**
- 4.2 강화학습 정책 엔진
  - 상태 공간: (agent_id, risk_level)
  - 행동 공간: {low, medium, high, critical}
  - 보상 함수: base_reward + speed_bonus + risk_penalty
  - Q-learning 업데이트 규칙
  - UCB1 탐색 전략: Q(s,a) + c * sqrt(ln(N) / N(s,a))
  - **핵심 수도코드 포함**
- 4.3 Playbook 엔진
  - resolve_step_script(): 템플릿 → 결정론적 명령
  - Deterministic builder: 파라미터 바인딩으로 LLM 비결정론 제거
  - 재실행: 동일 Playbook → 동일 결과 보장
- 4.4 4-Layer 경험 메모리
  - Layer 1 — Evidence: 태스크 실행 즉시 기록
  - Layer 2 — Task Memory: 프로젝트 단위 집계
  - Layer 3 — Experience: 자동 승급 (reward ≥ 1.1)
  - Layer 4 — Retrieval (RAG): 유사 경험 검색 + LLM 컨텍스트 주입
- 4.5 병렬 Multi-Agent Dispatch
  - ThreadPoolExecutor 기반 태스크별 SubAgent 라우팅
  - task.subagent_url로 대상 서버 지정
  - 결과 수집 + evidence 병합
- **파일:** `04-implementation.md`

### 5. Experimental Evaluation (~3 pages)
- 5.1 실험 환경
  - 서버 4대: opsclaw(control), secu(IPS), web(WAF), siem(Wazuh)
  - 네트워크 토폴로지
  - SW 스택: Python 3.11, FastAPI, PostgreSQL 15, LangGraph
- 5.2 실험 A — PoW 체인 무결성
  - 방법: 블록 생성 → block_hash/nonce/prev_hash 변조 → verify_chain
  - 결과: 위변조 100% 탐지, 위양성 0%
  - RQ1 답변
- 5.3 실험 H — 시간대 불변성
  - 방법: 5개 TZ(UTC, KST, PST, EST, IST)에서 동일 태스크 실행
  - 결과: ts_raw 기반 50/50 해시 일치
  - RQ1 보충
- 5.4 실험 B — RL 수렴 및 탐색
  - 방법: 에피소드 생성 → 20회 학습 → Q-value delta 측정
  - 결과: epoch 5에서 delta < 0.001, UCB1 미방문 정확 추천
  - RQ2 답변
- 5.5 실험 G — Playbook 재현성
  - 방법: 동일 Playbook 10회 반복 실행 → stdout 비교
  - 결과: 의미적 완전 일치 100%
  - RQ3 답변
- 5.6 실험 E — 상태 머신 유효성
  - 방법: 무효 전이 5건 시도 (e.g., created→executing)
  - 결과: 5/5 거부, replan 복구 성공
  - RQ4 부분 답변
- 5.7 실험 C — 증거 완전성
  - 방법: 5-태스크 execute-plan → evidence/PoW/reward 카운트
  - 결과: 모든 카운트 태스크 수와 일치 (100%)
  - RQ4 부분 답변
- 5.8 실험 F — 병렬 스케일링
  - 방법: N=1,2,3,5 태스크, 순차 vs 병렬 실행 시간 비교
  - 결과: N=5에서 4.0x 가속 (이론 대비 80% 효율)
  - RQ4 부분 답변
- 5.9 실험 D — 경험 재활용
  - 방법: 20건 태스크 실행 → auto_promote 트리거 → RAG 검색
  - 결과: reward ≥ 1.1에서 [Auto] 승급 20건, 카테고리 분류는 기본값 이슈
  - RQ5 답변
- **파일:** `05-experiments.md`
- **참고:** `docs/paper/results/exp-*.md`

### 6. Discussion (~1 page)
- 6.1 주요 발견 요약 (RQ1~RQ5 답변 종합)
- 6.2 실운영 적용 경험
  - M0~M25 마일스톤 이력
  - 점진적 개발 과정에서의 설계 변경
- 6.3 한계점
  - L1: RL 커버리지 4.2% (48개 중 8개 상태)
  - L2: 단일 SubAgent 병목 (병렬 효율 80%)
  - L3: 한국어 FTS 미지원 (RAG 영문 기반)
  - L4: prev_hash 변조의 간접 탐지
  - L5: N=1 태스크 오버헤드
- 6.4 향후 연구
  - Deep RL (DQN/PPO)로 Q-table 한계 극복
  - 다중 SubAgent 분산 아키텍처
  - Multi-LLM 오케스트레이션 (Master 교체 가능)
  - 한국어 trigram FTS (pg_trgm)
- **파일:** `06-discussion.md`

### 7. Conclusion (~0.5 page)
- 기여 재강조
- 핵심 수치 최종 요약
- 향후 방향
- **파일:** `07-conclusion.md`

### References
- 예상 20~30편
- **파일:** `08-references.md`

---

## 예상 분량
- 전체: ~12~14 pages (단일 컬럼 기준)
- 학회 포맷 적용 시: ~8~10 pages (2-column)

## 필요 도표

| 번호 | 유형 | 내용 | 섹션 |
|------|------|------|------|
| Fig 1 | 아키텍처 다이어그램 | Master→Manager→SubAgent 3계층 | 3.2 |
| Fig 2 | 상태 전이 다이어그램 | 8단계 라이프사이클 | 3.3 |
| Fig 3 | PoW 블록 구조 | 해시 체인 연결 | 4.1 |
| Fig 4 | RL 수렴 그래프 | Q-value delta over epochs | 5.4 |
| Fig 5 | 병렬 스케일링 그래프 | N vs speedup | 5.8 |
| Fig 6 | 4-Layer 메모리 | evidence→experience 흐름 | 4.4 |
| Table 1 | 프레임워크 비교 | OpsClaw vs AutoGPT/CrewAI/LangChain | 2 |
| Table 2 | 실험 결과 요약 | 8개 실험 핵심 수치 | 5 |
| Table 3 | 한계점 및 개선안 | L1~L5 + I1~I6 | 6 |

---

## 소스 데이터

| 데이터 | 파일 |
|--------|------|
| 실험 A 결과 | `docs/paper/results/exp-A-chain-integrity.md` |
| 실험 B 결과 | `docs/paper/results/exp-B-rl-convergence.md` |
| 실험 C 결과 | `docs/paper/results/exp-C-evidence-completeness.md` |
| 실험 D 결과 | `docs/paper/results/exp-D-experience-reuse.md` |
| 실험 E 결과 | `docs/paper/results/exp-E-state-machine.md` |
| 실험 F 결과 | `docs/paper/results/exp-F-parallel-scaling.md` |
| 실험 G 결과 | `docs/paper/results/exp-G-playbook-determinism.md` |
| 실험 H 결과 | `docs/paper/results/exp-H-temporal-invariance.md` |
| 비교 실험 | `docs/paper/results/exp-compare-opsclaw-vs-claudecode.md` |
| 핵심 수치 | `docs/paper/results/findings-and-improvements.md` |
| 아키텍처 | `docs/m0/opsclaw-m0-design-baseline.md` |
| 비교 매트릭스 | `docs/paper/experiment-design/09-comparison-and-paper-structure.md` |
