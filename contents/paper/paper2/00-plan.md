# Paper 2 상세 계획 (수정)

## 관점 변경: 보안/모의해킹 자동화 중심

> 에이전트 하네스 관점이 아닌, **LLM 에이전트 기반 모의해킹 자동화의 실증 연구** 관점으로 작성.
> OpsClaw는 실험 인프라로 언급하되, 논문의 핵심은 LLM 에이전트의 보안 운용 능력과 한계.

## 제목
**LLM 에이전트 기반 자율 모의해킹 및 방어 자동화: MITRE ATT&CK 4-Tier 실증 연구**

Autonomous Penetration Testing and Defense Automation with LLM Agents: A MITRE ATT&CK 4-Tier Empirical Study

## 핵심 연구 질문 (RQ)

| RQ | 질문 |
|----|------|
| RQ1 | LLM 에이전트가 MITRE ATT&CK 다단계 공격 체인을 자율적으로 실행할 수 있는가? |
| RQ2 | LLM 에이전트가 SIEM 로그를 분석하여 탐지 룰을 자동 생성할 수 있는가? |
| RQ3 | Red/Blue 반복 사이클에서 LLM 에이전트가 방어 체계를 점진적으로 강화하는가? |
| RQ4 | LLM 에이전트 기반 모의해킹의 현실적 한계와 개선 방향은? |

## 논문 구성

1. Introduction — 모의해킹 자동화의 필요성과 LLM 에이전트의 가능성
2. Related Work — 자동화 침투 테스트, SIEM 자동 대응, Purple Team 연구
3. Experiment Design — ATT&CK 4-Tier 시나리오, 인프라, 평가 기준
4. Red Team Results — T1~T4 상세 결과, ATT&CK 커버리지
5. Blue Team Results — SIEM 분석, 룰 생성, 검증
6. Purple Team Results — 4회전 공방, 취약점 발견, 방어 강화 과정
7. Discussion — LLM 에이전트의 모의해킹 능력과 한계
8. Conclusion
