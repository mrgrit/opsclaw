# 2. 관련 연구 (Related Work)

## 2.1 LLM 기반 자동화 침투 테스트

LLM 에이전트를 침투 테스트에 적용하는 연구가 활발히 진행되고 있다. PentestGPT [1]는 추론(reasoning), 생성(generation), 파싱(parsing) 세 모듈로 침투 테스트 라이프사이클을 안내하는 도구로, HackTheBox 환경에서 GPT-4의 다단계 추론 능력을 실증하여 USENIX Security 2024 Distinguished Artifact Award를 수상하였다. PentestAgent [3]는 다중 에이전트 협업으로 정보 수집, 취약점 분석, 공격 단계를 자동화하며, 단일 에이전트 대비 태스크 완료율과 효율성의 우위를 보였다. Context Relay [4]는 장기 실행 침투 테스트에서 LLM의 컨텍스트 한계를 해결하기 위한 핸드오프 메커니즘을 도입하여, 컨텍스트 윈도우를 초과하는 세션에서도 테스트 연속성을 유지한다.

공격 능력의 실증 측면에서 Fang 등 [2]은 GPT-4가 15개 유형의 실제 웹 취약점을 73% 성공률로 자율 공격할 수 있음을 보였다. Happe 등 [5]은 GPT-4와 Claude가 Linux 권한 상승 시나리오 10건 중 5건에서 성공함을 실증하여, 호스트 기반 공격에서의 LLM 가능성을 확인하였다. AutoAttacker [6]는 LLM 기반의 공격 계획 수립과 메모리를 갖춘 엔드투엔드 자동화 공격 시스템을 제안하였다.

**한계.** 기존 연구는 (1) 공격 자동화에 편중되어 방어 자동화를 다루지 않으며, (2) 개별 공격 유형(웹 또는 권한 상승)을 분리 평가하여 ATT&CK 전술 체인의 통합 평가가 부재하고, (3) 공격-방어 반복 사이클의 효과를 측정하지 않는다. 본 논문은 Red/Blue/Purple Team의 통합 평가로 이러한 간극을 해소한다.

## 2.2 SIEM 기반 자동 탐지 및 대응

SIEM(Security Information and Event Management)을 활용한 자동 탐지·대응은 보안 운영의 핵심이다. Wazuh [7]는 오픈소스 SIEM으로 실시간 로그 분석, 무결성 모니터링, 취약점 탐지를 제공하며, SIGMA [8] 룰 포맷은 SIEM 벤더에 무관한 범용 탐지 룰 작성을 지원한다. Suricata [9]는 고성능 IDS/IPS로 시그니처 기반 네트워크 위협 탐지를 수행한다.

SOAR(Security Orchestration, Automation and Response) 플랫폼 [10]은 인시던트 대응의 자동화를 목표로 하나, 탐지 룰 자체의 생성은 여전히 보안 분석가의 수동 작업에 의존한다. LLM을 활용한 탐지 룰 자동 생성 연구는 초기 단계에 있으며, 체계적인 실증이 부족하다.

**한계.** SIEM 경보 분석→공격 유형 식별→탐지 룰 생성→검증의 전 과정을 LLM 에이전트가 자동으로 수행하는 연구는 보고되지 않았다. 본 논문은 LLM 에이전트가 Wazuh 로그를 분석하여 커스텀 탐지 룰과 Suricata 시그니처를 자동 생성하는 Blue Team 파이프라인을 실증한다.

## 2.3 Purple Team 자동화

Purple Team 운용은 Red Team과 Blue Team의 협업을 통해 방어 체계를 점진적으로 강화하는 방법론이다. MITRE의 CALDERA [11]는 ATT&CK 기반 자동화 공격 에뮬레이션을 제공하며, Atomic Red Team [12]은 ATT&CK 기법별 원자적 테스트를 정의한다. 그러나 이러한 도구들은 사전 정의된 공격만 실행하며, LLM의 적응적 판단 능력을 활용하지 않는다.

보안 벤치마크 측면에서 AgentHarm [13]은 LLM 에이전트의 유해 행동을 체계적으로 평가하고, Agent Security Bench [14]는 에이전트 보안 취약점을 다차원 측정한다. CyberSecEval 2 [15]는 공격과 방어 양면에서 LLM을 평가하는 포괄적 벤치마크를 제공하나, 공격-방어 반복 사이클의 효과 측정은 다루지 않는다.

**한계.** 기존 Purple Team 자동화 도구는 규칙 기반이며, LLM 에이전트의 적응적 추론을 활용한 공격→탐지→방어 강화→재공격의 반복적 개선 효과를 정량적으로 측정한 연구가 없다. 본 논문은 4회전의 Purple Team 사이클을 통해 방어 체계가 점진적으로 강화되어 최종적으로 모든 공격을 차단하는 과정을 실증한다.

## 2.4 본 연구의 위치

표 1은 본 연구와 주요 기존 연구의 범위를 비교한다.

**표 1. 기존 연구 대비 본 연구의 범위**

| | Red Team | Blue Team | Purple Team | ATT&CK 체인 | 실환경 |
|---|:---:|:---:|:---:|:---:|:---:|
| PentestGPT [1] | ✓ | | | 부분 | CTF |
| Fang et al. [2] | ✓ | | | 웹만 | 샌드박스 |
| Happe et al. [5] | ✓ | | | 권한상승만 | VM |
| CALDERA [11] | ✓ | | | ✓ | 에뮬레이션 |
| CyberSecEval 2 [15] | ✓ | ✓ | | | 벤치마크 |
| **본 연구** | **✓** | **✓** | **✓** | **4-Tier** | **실환경 4대** |

---

## References

[1] G. Deng et al., "PentestGPT: An LLM-empowered Automatic Penetration Testing Tool," in *Proc. USENIX Security*, 2024.

[2] R. Fang et al., "LLM Agents can Autonomously Hack Websites," *arXiv:2402.06664*, 2024.

[3] W. Ruan et al., "PentestAgent: Incorporating LLM Agents to Automated Penetration Testing," in *Proc. ACM ASIA CCS*, 2025.

[4] (Context Relay), "Context Relay for Long-Running Penetration-Testing Agents," in *Proc. NDSS*, 2026.

[5] A. Happe et al., "LLMs as Hackers: Autonomous Linux Privilege Escalation Attacks," *arXiv:2310.11409*, 2023.

[6] J. Xu et al., "AutoAttacker: A Large Language Model Guided System to Implement Automatic Cyber-attacks," *arXiv:2403.01038*, 2024.

[7] Wazuh Inc., "Wazuh: Open Source Security Platform," https://wazuh.com, 2024.

[8] F. Roth et al., "SIGMA: Generic Signature Format for SIEM Systems," GitHub Repository, 2024.

[9] Open Information Security Foundation, "Suricata: Open Source IDS/IPS," https://suricata.io, 2024.

[10] Gartner, "Market Guide for Security Orchestration, Automation and Response Solutions," 2024.

[11] MITRE, "CALDERA: Automated Adversary Emulation Platform," https://caldera.mitre.org, 2024.

[12] Red Canary, "Atomic Red Team: Small and Highly Portable Detection Tests," GitHub Repository, 2024.

[13] (AgentHarm), "AgentHarm: A Benchmark for Measuring Harmfulness of LLM Agents," in *Proc. ICLR*, 2025.

[14] (ASB), "Agent Security Bench: Formalizing and Benchmarking Attacks and Defenses in LLM-based Agents," in *Proc. ICLR*, 2025.

[15] M. Bhatt et al., "CyberSecEval 2: A Wide-Ranging Cybersecurity Evaluation Suite for Large Language Models," *arXiv:2404.13161*, 2024.
