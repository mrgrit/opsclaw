# 1. 서론 (Introduction)

## 1.1 연구 배경

대규모 언어 모델(LLM) 기반 에이전트가 소프트웨어 개발, IT 운영, 보안 자동화 등 다양한 분야에 적용되면서, 에이전트의 실행을 **관리·제어·기록**하는 프레임워크 — 에이전트 하네스(agent harness) — 의 중요성이 급증하고 있다.

하네스의 핵심 역할은 세 가지이다:
1. **제어(Control)**: 에이전트가 어떤 도구를 사용할 수 있고, 어떤 행동이 허용/금지되는지 관리
2. **기록(Record)**: 에이전트의 모든 실행을 추적 가능하게 기록
3. **학습(Learn)**: 과거 실행 경험을 축적하여 향후 의사결정에 반영

그런데 현재 에이전트 하네스는 크게 두 가지 패러다임으로 분화되고 있다:

**클라이언트 하네스(Client-Side Harness).** 사용자의 로컬 머신에서 LLM과 도구(파일 I/O, 셸, 검색 등)를 직접 연결한다. Anthropic의 Claude Code [1], GitHub Copilot Workspace [2], Cursor [3] 등이 이 접근을 취한다. LLM이 어떤 도구를 어떤 순서로 호출할지 자율적으로 결정하며(에이전틱 루프), 사용자 머신의 파일시스템과 터미널에 직접 접근한다.

**서버 하네스(Server-Side Harness).** 서버 사이드 API가 에이전트 실행을 중재하고, 모든 행동을 데이터베이스에 영구 기록하며, 분산 실행 노드(SubAgent)에 태스크를 위임한다. CALDERA [4], Ansible Tower, 그리고 본 연구의 OpsClaw가 이 접근을 취한다. 실행 계획은 API를 통해 선언적으로 전달되며, 증적(evidence)과 보상(reward)이 자동으로 생성된다.

두 패러다임은 동일한 목표(LLM 에이전트의 효과적 운용)를 추구하지만, **도구 구성, 스킬/플레이북, 메모리, 권한 관리, 피드백 루프** 등 모든 설계 차원에서 근본적으로 다른 선택을 한다. 그러나 이 두 접근의 체계적 비교는 아직 보고되지 않았다.

## 1.2 연구 목적

본 논문은 클라이언트 하네스(Claude Code)와 서버 하네스(OpsClaw)를 **10개 차원**에서 체계적으로 비교하고, 실험을 통해 각 패러다임의 강점과 한계를 정량적으로 평가한다. 또한 두 패러다임을 결합하는 **하이브리드 접근**의 가능성을 논의한다.

## 1.3 주요 기여

- **C1. 하네스 패러다임 분류 체계.** LLM 에이전트 하네스를 "클라이언트 하네스"와 "서버 하네스"로 분류하고, 10개 비교 차원(도구, 스킬, 훅, 메모리, 서브에이전트, 태스크 추적, 권한, 스케줄링, 피드백, 실행 모델)을 정의한다.

- **C2. 정량적 비교 실험.** 동일 5-태스크 다중 서버 벤치마크에서 실행 속도, 증적 완전성, 재현성, 메모리 활용을 비교하여, 서버 하네스의 "실행 후" 가치와 클라이언트 하네스의 유연성을 정량화한다.

- **C3. 하이브리드 아키텍처 제안.** Claude Code(클라이언트)가 Master 역할을 수행하고, OpsClaw(서버)가 Control Plane 역할을 수행하는 하이브리드 모델이 양쪽의 장점을 결합할 수 있음을 실증한다 — 실제로 본 연구의 모든 실험은 이 하이브리드 모드(Claude Code as External Master + OpsClaw Manager API)로 수행되었다.

## 1.4 논문 구성

2장에서 하네스의 정의와 관련 연구를 기술한다. 3장에서 클라이언트 하네스(Claude Code)와 서버 하네스(OpsClaw)의 아키텍처를 각각 상세히 기술한다. 4장에서 10개 비교 차원의 프레임워크를 제시하고, 5장에서 실험 결과를 보고한다. 6장에서 하이브리드 접근과 한계를 논의하며, 7장에서 결론을 맺는다.

---

## References

[1] Anthropic, "Claude Code: An agentic coding tool," https://docs.anthropic.com/en/docs/claude-code, 2025.

[2] GitHub, "GitHub Copilot Workspace: An AI-powered development environment," 2024.

[3] Cursor, "The AI Code Editor," https://cursor.sh, 2024.

[4] MITRE, "CALDERA: Automated Adversary Emulation Platform," https://caldera.mitre.org, 2024.
