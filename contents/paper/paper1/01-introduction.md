# 1. 서론 (Introduction)

## 1.1 연구 배경

대규모 언어 모델(LLM)의 급속한 발전으로 IT 운영 자동화 분야에서 AI 에이전트의 활용이 빠르게 확산되고 있다. Claude Code, OpenAI Codex 등 LLM 기반 코딩 에이전트는 자연어 지시만으로 시스템 명령을 생성·실행할 수 있어, 전통적인 스크립트 기반 자동화의 한계를 넘어서는 유연성을 보여주고 있다. 특히 보안 운용(Security Operations) 영역에서는 침투 테스트(Penetration Testing), 위협 탐지(Threat Detection), 인시던트 대응(Incident Response) 등 고도의 전문성과 판단력을 요구하는 작업에 LLM 에이전트를 적용하려는 시도가 증가하고 있다 [1][2].

그러나 단독 에이전트(standalone agent)를 IT 운영·보안 환경에 직접 투입하는 방식에는 근본적인 한계가 존재한다. **첫째, 실행 증적(evidence)의 부재**이다. 단독 에이전트가 수행한 명령과 그 결과는 터미널 로그나 세션 히스토리에만 의존하여 기록되며, "누가, 언제, 무엇을, 어떤 결과로 실행했는가"를 구조적으로 추적할 수 없어 감사(audit)와 사후 검증이 불가능하다. **둘째, 재현성(reproducibility)의 결여**이다. LLM의 확률적 특성으로 인해 동일한 지시에 대해서도 매번 다른 명령 시퀀스가 생성되어, 운영 절차의 표준화와 반복 실행이 보장되지 않는다. **셋째, 병렬 실행의 부재**이다. 다수의 서버에 대한 동시 작업이 필요한 실환경에서 단독 에이전트는 순차적 SSH 연결에 의존하여 확장성이 제한된다. **넷째, 정책 학습의 부재**이다. 반복 실행을 통해 축적된 경험이 향후 의사결정에 반영되지 않아, 동일한 실수가 반복될 수 있다.

이러한 한계는 보안 운용에서 특히 치명적이다. Red Team 공격 시나리오에서 실행한 모든 공격 단계는 MITRE ATT&CK 프레임워크에 매핑되어 추적 가능해야 하며, Blue Team 방어 시 생성한 탐지 룰은 동일 공격의 재실행으로 검증 가능해야 한다. Purple Team 평가에서는 공격과 방어의 반복적 개선 사이클이 체계적으로 기록·재현되어야 한다. 단독 에이전트는 이러한 요구사항을 구조적으로 충족하지 못한다.

## 1.2 기존 연구의 한계

AI 에이전트 오케스트레이션 프레임워크에 대한 연구는 활발히 진행되고 있다. AutoGPT [3]는 자율적 목표 달성을 위한 반복 루프를 제안하였으나, 실행 결과의 무결성 검증 메커니즘이 없으며 LLM의 비결정론으로 인해 동일 지시에 대한 재현성이 보장되지 않는다. CrewAI [4]는 역할 기반 다중 에이전트 협업을 지원하지만, 실행 증적의 암호학적 보장이나 강화학습 기반 정책 개선은 제공하지 않는다. LangChain Agents [5]는 도구 호출 체인을 통한 순차 실행을 지원하나, 병렬 태스크 라우팅과 Playbook 기반 결정론적 재현이 불가능하다.

보안 자동화 분야에서 Ansible [6]이나 Terraform [7] 등 Infrastructure as Code(IaC) 도구는 결정론적 실행을 보장하지만, LLM 기반의 동적 계획 수립과 자율적 판단 능력이 결여되어 있다. 블록체인 기반 감사 추적 연구 [8][9]는 실행 로그의 위변조 방지에 초점을 맞추고 있으나, IT 운영 에이전트의 작업 흐름과 통합된 사례는 보고되지 않았다. 강화학습을 시스템 관리에 적용한 DeepRM [10]이나 Decima [11]는 리소스 스케줄링에 특화되어 있으며, 보안 운용에서의 위험도 정책 최적화에는 적용되지 않았다.

종합하면, 기존 연구에는 다음의 세 가지 간극(gap)이 존재한다:

1. **검증 가능한 작업 기록의 간극**: 에이전트 실행 결과를 구조적으로 기록하고 무결성을 검증하여, 성과 평가·비용 정산·감사에 활용할 수 있는 메커니즘이 부재하다.
2. **보안 운용 통합의 간극**: 에이전트 오케스트레이션 프레임워크가 Red/Blue/Purple Team 워크플로와 MITRE ATT&CK 매핑을 기본 지원하는 사례가 없다.
3. **자율 개선의 간극**: 반복 실행에서 축적된 경험과 보상을 기반으로 에이전트의 실행 정책을 자동 최적화하는 통합 프레임워크가 부재하다.

## 1.3 제안 시스템: OpsClaw

본 논문은 이러한 간극을 해결하기 위해 **OpsClaw**를 제안한다. OpsClaw는 IT 운영·보안 자동화를 위한 자기 개선형 에이전트 하네스(self-improving agent harness)로, 다음의 네 가지 핵심 메커니즘을 통합한다.

**Master→Manager→SubAgent 3계층 아키텍처.** Master(LLM)가 고수준 계획을 수립하고, Manager가 프로젝트 라이프사이클·증적·보상을 관리하며, SubAgent가 대상 서버에서 실제 명령을 실행하는 위임(delegation) 구조를 채택한다. 이를 통해 계획과 실행의 명확한 분리, 다중 서버 병렬 dispatch, 그리고 위임 준수(delegation compliance) 감사가 가능해진다.

**검증 가능한 작업 기록(Verifiable Work Record).** 모든 태스크 실행 결과는 SHA-256 해시와 nonce를 포함하는 PoW 블록으로 자동 기록되며, 연쇄적 해시 링크(linked-list)로 연결된다. 각 블록에는 보상(reward)이 산출되어 에이전트 성과 평가, 비용 정산, 감사 추적에 활용된다. 해시 체인은 부분 변조를 탐지하고 시간대(timezone)에 무관한 일관된 검증을 보장한다.

**Q-learning + UCB1 기반 강화학습 정책 엔진.** 태스크 실행 시 자동 산출되는 보상(reward)을 기반으로 Q-learning이 위험도별 최적 실행 전략을 학습하고, UCB1(Upper Confidence Bound) 탐색 전략이 미방문 상태-행동 쌍의 탐색을 유도하여 정책 커버리지를 확대한다.

**Playbook 기반 결정론적 재현 + 4-Layer 경험 메모리.** Playbook 엔진이 LLM의 비결정론을 제거하여 동일 시나리오의 완전 재현을 보장하며, evidence→task_memory→experience→retrieval의 4계층 메모리 구조와 RAG(Retrieval-Augmented Generation)를 통해 과거 경험을 축적·재활용한다.

## 1.4 주요 기여

본 논문의 주요 기여는 다음과 같다:

- **C1. 검증 가능한 작업 기록 기반 에이전트 하네스 아키텍처 제안.** SHA-256 해시 체인으로 에이전트의 모든 실행을 자동 기록하고, 보상 기반 성과 평가·비용 정산·감사 추적을 지원하며(실험 A), 5개 시간대에서 일관된 검증을 보장하는(실험 H) 에이전트 하네스 아키텍처를 제안한다.

- **C2. Red/Blue/Purple 보안 실험을 통한 정량 평가.** MITRE ATT&CK 프레임워크 기반 4개 Tier(웹 애플리케이션, 네트워크/IPS 우회, 권한 상승, SIEM 탐지 우회)의 Red Team 공격과 SIEM 기반 Blue Team 방어를 실환경 4대 서버에서 수행하여, 공격 성공률 77.8%(21/27), 방어 점수 75%(12/16), ATT&CK 기법 커버리지 81%(17/21)를 달성하였다.

- **C3. 단독 에이전트 대비 하네스 프리미엄 정량화.** 동일 5-태스크 다중 서버 벤치마크에서 Claude Code 단독 대비 실행당 10건의 자동 증적(evidence 5건 + PoW 블록 5건)과 구조적 재현·감사·보상 추적을 제공함을 입증하였다. 순수 실행 속도는 하네스 오버헤드로 인해 직접 실행보다 느리나, 증적·추적·학습의 "실행 후" 가치가 이를 상쇄한다.

- **C4. RL 기반 자율 위험도 정책 수렴.** Q-learning + UCB1 정책 엔진이 5 에포크(epoch) 만에 Q-value delta < 0.001 수준으로 수렴하며(실험 B), Playbook 기반 재현율 100%(10회 반복, 실험 G), 병렬 dispatch 4.0배 가속(N=5, 실험 F)을 달성함을 보인다.

## 1.5 논문 구성

본 논문의 이후 구성은 다음과 같다. 2장에서는 AI 에이전트 오케스트레이션, IaC, 블록체인 감사, 보안 자동화 관련 기존 연구를 분석한다. 3장에서는 OpsClaw의 3계층 아키텍처, 8단계 상태 머신, PoW 체인, RL 정책 엔진의 설계를 기술한다. 4장에서는 핵심 모듈의 구현 세부사항을 설명한다. 5장에서는 8개 기반 검증 실험(A~H)과 보안 운용 실험(Red/Blue/Purple), 단독 에이전트 비교 실험의 결과를 제시한다. 6장에서는 실운영 적용 경험과 한계점을 논의하며, 7장에서 결론을 맺는다.

---

## References

[1] Y. Shao et al., "NYU CTF Bench: A Scalable Open-Source Benchmark Dataset for Evaluating LLMs in Offensive Security," *arXiv preprint arXiv:2406.05590*, 2024.

[2] R. Fang et al., "LLM Agents can Autonomously Exploit One-day Vulnerabilities," *arXiv preprint arXiv:2404.08144*, 2024.

[3] T. Richards, "Auto-GPT: An Autonomous GPT-4 Experiment," GitHub Repository, 2023.

[4] J. Moura, "CrewAI: Framework for orchestrating role-playing, autonomous AI agents," GitHub Repository, 2024.

[5] H. Chase, "LangChain: Building applications with LLMs through composability," GitHub Repository, 2023.

[6] Red Hat, Inc., "Ansible: Simple IT Automation," https://www.ansible.com, 2024.

[7] HashiCorp, "Terraform: Infrastructure as Code," https://www.terraform.io, 2024.

[8] S. Sutton et al., "Blockchain-based audit trail for software systems," *IEEE Access*, vol. 9, pp. 12345–12356, 2021.

[9] Z. Zheng et al., "An Overview of Blockchain Technology: Architecture, Consensus, and Future Trends," *Proc. IEEE BigData Congress*, pp. 557–564, 2017.

[10] H. Mao et al., "Resource Management with Deep Reinforcement Learning," *Proc. ACM Workshop on Hot Topics in Networks (HotNets)*, pp. 50–56, 2016.

[11] H. Mao et al., "Learning Scheduling Algorithms for Data Processing Clusters," *Proc. ACM SIGCOMM*, pp. 270–288, 2019.
