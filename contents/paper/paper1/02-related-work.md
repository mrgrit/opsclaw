# 2. 관련 연구 (Related Work)

본 장에서는 OpsClaw의 설계와 관련된 다섯 가지 연구 영역을 분석하고, 각 영역에서의 기존 연구 한계와 OpsClaw가 해결하는 간극을 명확히 한다.

## 2.1 LLM 기반 에이전트 오케스트레이션 프레임워크

대규모 언어 모델을 활용한 자율 에이전트 시스템은 2023년 이후 급속히 발전하였다. Park 등 [1]은 25개의 생성형 에이전트가 메모리 스트림, 반성(reflection), 계획(planning)을 통해 자율적으로 행동하는 아키텍처를 제안하여, 에이전트 메모리 설계의 기초를 확립하였다. Voyager [2]는 Minecraft 환경에서 LLM이 코드를 생성하고 스킬 라이브러리를 축적하여 개방형 탐험을 수행하는 에이전트를 구현하였으며, 재사용 가능한 스킬의 축적이라는 개념을 정립하였다.

다중 에이전트 협업 측면에서 CAMEL [3]은 두 LLM 에이전트가 역할극(role-playing)을 통해 자율적으로 협업하는 "inception prompting" 기법을 제안하였고, MetaGPT [4]는 SOP(Standard Operating Procedure)를 다중 에이전트 워크플로에 인코딩하여 PM, 아키텍트, 엔지니어, QA 역할을 분담하는 구조화된 협업 프레임워크를 구현하였다. 최근 SELFORG [5]는 Shapley 기반 기여도 평가로 에이전트 간 통신 그래프를 동적으로 구성하는 자기 조직화 오케스트레이션을 제안하였다.

도구 활용 측면에서 Toolformer [6]는 LLM이 외부 API 호출 시점과 방법을 자기지도 학습으로 습득하는 접근을 제시하였다. 에이전트 벤치마크로는 AgentBench [7]가 8개 환경에서 LLM의 에이전트 능력을 다차원 평가하고, SWE-bench [8]가 실제 GitHub 이슈 2,294건에 대한 패치 생성 능력을 측정한다.

**한계와 간극.** 기존 프레임워크들은 에이전트 실행 결과의 암호학적 무결성 보장(PoW), 강화학습 기반 정책 자율 개선, 그리고 Playbook 기반 결정론적 재현을 제공하지 않는다. MetaGPT의 SOP는 코드 생성에 특화되어 있으며 IT 운영의 다단계 라이프사이클 관리에는 적합하지 않다. OpsClaw는 이러한 간극을 3계층 위임 아키텍처와 8단계 상태 머신으로 해결한다.

## 2.2 LLM 에이전트의 보안 운용 적용

LLM 에이전트를 침투 테스트에 적용하는 연구가 활발히 진행되고 있다. PentestGPT [9]는 추론(reasoning), 생성(generation), 파싱(parsing) 세 모듈을 결합하여 침투 테스트 라이프사이클을 안내하는 도구로, HackTheBox 환경에서 평가되어 USENIX Security 2024 Distinguished Artifact Award를 수상하였다. PentestAgent [10]는 다중 에이전트 협업으로 정보 수집, 취약점 분석, 공격 단계를 자동화하는 프레임워크를 제안하였다. 최근 Context Relay [11]는 장기 실행 침투 테스트에서 에이전트의 컨텍스트 한계를 해결하기 위한 컨텍스트 핸드오프 메커니즘을 도입하였다.

Fang 등 [12]은 GPT-4가 실제 웹 취약점(XSS, SQLi, CSRF)을 73% 성공률로 자율 공격할 수 있음을 실증하였다. 보안 벤치마크 측면에서 AgentHarm [13]은 LLM 에이전트의 유해 행동을 체계적으로 평가하고, Agent Security Bench [14]는 에이전트 보안 취약점을 다차원으로 측정한다. Meta의 CyberSecEval 2 [15]는 공격(exploit 생성)과 방어(보안 코드 생성) 양면에서 LLM을 평가하는 포괄적 벤치마크를 제공한다.

**한계와 간극.** 기존 연구는 단독 에이전트의 공격 능력 평가에 집중하며, 에이전트 하네스를 통한 Red/Blue/Purple Team 통합 운용은 다루지 않는다. PentestGPT가 지적한 "전체 테스트 컨텍스트 유지의 어려움"은 OpsClaw의 Manager가 프로젝트 단위로 해결하며, PoW 블록체인이 모든 보안 운용의 감사 추적을 보장한다.

## 2.3 블록체인 기반 감사 추적 및 출처 증명

실행 로그의 위변조 방지를 위한 블록체인 활용 연구는 꾸준히 진행되어 왔다. Cucurull 등 [16]은 허가형 블록체인(Hyperledger) 기반의 안전하고 투명한 감사 로그 시스템 BlockAudit를 제안하여, 제3자 없이도 로그 무결성을 보장하는 구조를 실증하였다. 최근 IEEE TDSC에 발표된 연구 [17]는 블록체인 기반의 감사 가능한 접근 제어를 사업 프로세스에 적용하여, 이벤트 기반 정책의 투명한 실행을 보장하였다. VLDB FAB Workshop 2024에서는 블록체인을 출처 증명(provenance)에 적용한 연구의 체계적 지식 정리(SoK) [18]가 발표되어, IoT, 공급망, 과학적 워크플로 등 다양한 도메인에서의 활용을 조망하였다.

출처 그래프(provenance graph) 분석 측면에서 TREC [19]는 APT(Advanced Persistent Threat)의 전술·기법을 소수 샘플 학습으로 출처 서브그래프에서 인식하는 기법을 제안하여, 보안 영역에서의 출처 추적 고도화를 보여주었다.

**한계와 간극.** 기존 블록체인 감사 연구는 범용 로그 무결성에 초점을 맞추며, AI 에이전트의 작업 흐름(task execution, evidence, reward)과 통합된 사례는 보고되지 않았다. OpsClaw는 에이전트 태스크 실행과 PoW 블록 생성을 원자적으로 결합하여, 계획→실행→증적→보상의 전 과정을 하나의 해시 체인으로 기록한다. 또한 합의 프로토콜(consensus) 없이 경량 해시 체인만으로 단일 조직 환경의 감사 요구를 충족하는 실용적 접근을 취한다.

## 2.4 시스템 관리를 위한 강화학습

강화학습을 IT 인프라 관리에 적용하는 연구는 스케줄링과 자원 할당 분야에서 주로 진행되었다. Decima [20]는 그래프 신경망과 RL을 결합하여 DAG 구조 작업의 스케줄링 정책을 학습하고, 수동 설계 휴리스틱 대비 21~30%의 작업 완료 시간 개선을 달성하였다. FIRM [21]은 마이크로서비스 환경에서 SLO 준수를 위한 세밀한 자원 관리에 다중 에이전트 RL을 적용하였으며, Cilantro [22]는 다중 팔 밴딧/컨텍스트 밴딧 기반 온라인 학습으로 변화하는 워크로드에 적응하는 클라우드 자원 할당을 구현하였다. DeepScaling [23]은 Alibaba 규모의 마이크로서비스 오토스케일링에 심층 RL을 적용하여 버스트 워크로드와 서비스 간 연쇄 효과를 처리하였다. 최근 EuroSys 2025에서는 심층 RL 기반 VM 재스케줄링 [24]이 정적 규칙 대비 데이터센터 효율을 개선함을 보였다.

**한계와 간극.** 기존 RL 연구는 리소스 스케줄링과 오토스케일링에 특화되어 있으며, 보안 운용에서의 위험도(risk level) 정책 최적화에는 적용되지 않았다. OpsClaw의 Q-learning + UCB1 정책 엔진은 태스크별 보상을 기반으로 low/medium/high/critical 위험도의 최적 실행 전략을 자율적으로 학습하며, 이는 기존 연구에서 다루지 않은 새로운 적용 영역이다.

## 2.5 에이전트 메모리 및 경험 학습

LLM 에이전트의 자기 개선을 위한 메모리 및 경험 학습 연구가 최근 급속히 발전하고 있다. Reflexion [25]은 에이전트가 실패한 시도를 언어적으로 반성하여 에피소드 메모리에 저장하고, 후속 시도에서 이를 활용하는 "verbal reinforcement learning"을 제안하여 HumanEval에서 91% pass@1을 달성하였다. ExpeL [26]은 과거 태스크 궤적에서 재사용 가능한 통찰(insight)을 자연어로 추출하여 저장하고, 추론 시 검색하여 활용하는 경험적 학습 프레임워크를 제시하였다.

메모리 관리 측면에서 MemGPT [27]는 운영체제의 메모리 계층(RAM/디스크)에서 영감을 받아, LLM이 함수 호출로 자체 컨텍스트를 페이징(paging)하는 가상 컨텍스트 관리를 구현하였다. A-MEM [28]은 Zettelkasten 방법론을 차용하여 동적 인덱싱과 링킹으로 상호 연결된 지식 네트워크를 구성하는 에이전틱 메모리 시스템을 제안하였다. 계획 최적화 측면에서 LATS [29]는 몬테카를로 트리 탐색과 LLM을 결합하여 에이전트의 추론-행동-계획을 통합하였다.

검색 증강 생성(RAG) 분야에서 RAPTOR [30]는 서로 다른 추상화 수준의 텍스트 요약 트리를 구축하여 상세 로그부터 고수준 요약까지의 검색을 지원한다.

**한계와 간극.** Reflexion과 ExpeL의 경험 학습은 단일 태스크 반복에 초점을 맞추며, IT 운영의 구조화된 증적(evidence → task_memory → experience → retrieval) 계층과는 다르다. MemGPT의 메모리 관리는 대화 컨텍스트에 최적화되어 있으며, 운영 태스크의 보상 기반 자동 승급과 RL 정책 연결은 제공하지 않는다. OpsClaw는 4-Layer 메모리 구조와 RAG를 통해 실행 증적을 경험으로 승급시키고, 이를 RL 보상과 연결하여 정책 개선에 활용하는 통합 자기 개선 루프를 구현한다.

## 2.6 요약: 기존 연구 대비 OpsClaw의 위치

표 1은 OpsClaw와 주요 기존 시스템의 기능을 비교한다.

**표 1. 에이전트 오케스트레이션 프레임워크 비교**

| 차원 | OpsClaw | MetaGPT [4] | AutoGPT | CrewAI | LangChain Agents |
|------|---------|-------------|---------|--------|-----------------|
| 실행 증명 | SHA-256 PoW 체인 | 없음 | 로그 파일 | 없음 | Callback 로그 |
| 위변조 탐지 | 100% | 불가 | 불가 | 불가 | 불가 |
| 라이프사이클 관리 | 8단계 상태 머신 | SOP 순차 | 단일 루프 | 역할 기반 | 체인 순차 |
| 경험 학습 | 4-Layer + RAG | 없음 | 파일 로그 | Knowledge base | Context window |
| 강화학습 | Q-learning + UCB1 | 없음 | 없음 | 없음 | 없음 |
| 실행 재현성 | 100% (Playbook) | 비결정론 | 비결정론 | 비결정론 | 비결정론 |
| 병렬 실행 | Task별 라우팅 | 없음 | 없음 | asyncio | 없음 |
| 위험도 관리 | 4단계 + dry_run | 없음 | 없음 | 없음 | 없음 |

---

## References

[1] J. S. Park, J. C. O'Brien, C. J. Cai, M. R. Morris, P. Liang, and M. S. Bernstein, "Generative Agents: Interactive Simulacra of Human Behavior," in *Proc. ACM UIST*, 2023. (Best Paper Award)

[2] G. Wang, Y. Xie, Y. Jiang, A. Mandlekar, C. Xiao, Y. Zhu, L. Fan, and A. Anandkumar, "Voyager: An Open-Ended Embodied Agent with Large Language Models," in *Proc. NeurIPS*, 2023. (Spotlight)

[3] G. Li, H. A. A. K. Hammoud, H. Itani, D. Khizbullin, and B. Ghanem, "CAMEL: Communicative Agents for 'Mind' Exploration of Large Language Model Society," in *Proc. NeurIPS*, 2023.

[4] S. Hong, M. Zhuge, J. Chen, X. Zheng, Y. Cheng, C. Zhang, J. Wang, Z. Wang, S. K. S. Yau, Z. Lin, L. Zhou, C. Ran, L. Xiao, C. Wu, and J. Schmidhuber, "MetaGPT: Meta Programming for a Multi-Agent Collaborative Framework," in *Proc. ICLR*, 2024.

[5] (SELFORG), "Self-Organizing Multi-Agent Systems via LLM Orchestration," in *Proc. ICLR*, 2026.

[6] T. Schick, J. Dwivedi-Yu, R. Dessì, R. Raileanu, M. Lomeli, E. Hambro, L. Zettlemoyer, N. Cancedda, and T. Scialom, "Toolformer: Language Models Can Teach Themselves to Use Tools," in *Proc. NeurIPS*, 2023.

[7] X. Liu, H. Yu, H. Zhang, Y. Xu, X. Lei, H. Lai, Y. Gu, H. Ding, K. Men, K. Yang, S. Zhang, X. Deng, A. Zeng, Z. Du, C. Zhang, S. Shen, T. Zhang, Y. Su, H. Sun, M. Huang, Y. Dong, and J. Tang, "AgentBench: Evaluating LLMs as Agents," in *Proc. ICLR*, 2024.

[8] C. E. Jimenez, J. Yang, A. Wettig, S. Yao, K. Pei, O. Press, and K. Narasimhan, "SWE-bench: Can Language Models Resolve Real-World GitHub Issues?," in *Proc. ICLR*, 2024.

[9] G. Deng, Y. Liu, V. Mayoral-Vilches, P. Liu, Y. Li, Y. Xu, T. Zhang, Y. Liu, M. Pinzger, and S. Rass, "PentestGPT: An LLM-empowered Automatic Penetration Testing Tool," in *Proc. USENIX Security Symposium*, 2024. (Distinguished Artifact Award)

[10] W. Ruan, Y. Zhang, and N. Pang, "PentestAgent: Incorporating LLM Agents to Automated Penetration Testing," in *Proc. ACM ASIA CCS*, 2025.

[11] (Context Relay), "Context Relay for Long-Running Penetration-Testing Agents," in *Proc. NDSS Symposium*, 2026.

[12] R. Fang, R. Bindu, A. Gupta, and D. Kang, "LLM Agents can Autonomously Hack Websites," *arXiv preprint arXiv:2402.06664*, 2024.

[13] (AgentHarm), "AgentHarm: A Benchmark for Measuring Harmfulness of LLM Agents," in *Proc. ICLR*, 2025.

[14] (Agent Security Bench), "Agent Security Bench (ASB): Formalizing and Benchmarking Attacks and Defenses in LLM-based Agents," in *Proc. ICLR*, 2025.

[15] M. Bhatt, S. Chennabasappa, C. Nikolaidis, S. Wan, I. Evtimov, D. Gabi, D. Song, F. Ahmad, C. Aber, and others, "CyberSecEval 2: A Wide-Ranging Cybersecurity Evaluation Suite for Large Language Models," *arXiv preprint arXiv:2404.13161*, 2024.

[16] J. Cucurull and J. Puiggalí, "Towards Blockchain-Driven, Secure and Transparent Audit Logs," in *Proc. ACM MobiQuitous*, 2018; extended in *Journal of Network and Computer Applications*, 2019.

[17] (Blockchain Auditable Access Control), "Blockchain Based Auditable Access Control for Business Processes With Event Driven Policies," *IEEE Trans. Dependable and Secure Computing (TDSC)*, vol. 21, no. 5, 2024.

[18] (SoK: Blockchain for Provenance), "SOK: Blockchain for Provenance," in *VLDB FAB Workshop*, 2024.

[19] (TREC), "TREC: APT Tactic/Technique Recognition via Few-Shot Provenance Subgraph Learning," in *Proc. ACM CCS*, 2024.

[20] H. Mao, M. Schwarzkopf, S. B. Venkatakrishnan, Z. Meng, and M. Alizadeh, "Learning Scheduling Algorithms for Data Processing Clusters," in *Proc. ACM SIGCOMM*, pp. 270–288, 2019.

[21] H. Qiu, S. S. Banerjee, S. Jha, Z. T. Kalbarczyk, and R. K. Iyer, "FIRM: An Intelligent Fine-grained Resource Management Framework for SLO-Oriented Microservices," in *Proc. USENIX OSDI*, 2023.

[22] R. Bhardwaj, N. Anand, R. Agarwal, and I. Stoica, "Cilantro: Performance-Aware Resource Allocation for General Objectives via Online Feedback," in *Proc. USENIX OSDI*, 2023.

[23] C. Meng, Y. Zhang, and others, "DeepScaling: Microservices AutoScaling for Stable CPU Utilization in Large Scale Cloud Systems," in *Proc. ACM SoCC*, 2023.

[24] X. Ding, Y. Zhang, B. Chen, and others, "Towards VM Rescheduling Optimization Through Deep Reinforcement Learning," in *Proc. ACM EuroSys*, 2025.

[25] N. Shinn, F. Cassano, A. Gopinath, K. Narasimhan, and S. Yao, "Reflexion: Language Agents with Verbal Reinforcement Learning," in *Proc. NeurIPS*, 2023.

[26] A. Zhao, D. Huang, Q. Xu, M. Lin, Y.-J. Liu, and G. Huang, "ExpeL: LLM Agents Are Experiential Learners," in *Proc. AAAI*, 2024.

[27] C. Packer, S. Wooders, K. Lin, V. Fang, S. G. Patil, I. Stoica, and J. E. Gonzalez, "MemGPT: Towards LLMs as Operating Systems," in *Proc. ICLR*, 2024. (Spotlight)

[28] (A-MEM), "A-MEM: Agentic Memory for LLM Agents," in *Proc. NeurIPS*, 2025.

[29] A. Zhou, Y. Yan, M. Shlapentokh-Rothman, H. Wang, and Y.-X. Wang, "Language Agent Tree Search Unifies Reasoning, Acting, and Planning in Language Models," in *Proc. ICML*, 2024.

[30] P. Sarthi, S. Abdullah, A. Tuli, S. Khanna, A. Goldie, and C. D. Manning, "RAPTOR: Recursive Abstractive Processing for Tree-Organized Retrieval," in *Proc. ICLR*, 2024.
