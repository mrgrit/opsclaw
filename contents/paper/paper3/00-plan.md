# Paper 3 상세 계획 (재구성 B)

## 상태: 계획만 — 추가 실험 후 본문 작성 예정

## 제목
**OpsClaw: IT 운영 자동화 플랫폼의 설계·구축·운용 25 마일스톤 사례 연구**

OpsClaw: A 25-Milestone Case Study on Designing, Building, and Operating an IT Operations Automation Platform

---

## 관점
- 아키텍처 논문(Paper 1)이나 보안 실험(Paper 2)과 달리, **실운영 구축 과정의 교훈과 경험**에 초점
- M0(설계 기준선)부터 M25(인프라 완성)까지 25개 마일스톤에 걸친 점진적 개발 여정
- "이렇게 만들었다"가 아니라 **"이렇게 만들면서 이런 것을 배웠다"**

## 핵심 연구 질문 (RQ)

| RQ | 질문 |
|----|------|
| RQ1 | LLM 에이전트 기반 IT 자동화 플랫폼을 점진적으로 구축할 때 어떤 설계 결정이 핵심이었는가? |
| RQ2 | 실운영 중 발견된 버그·아키텍처 문제는 무엇이며, 어떻게 해결하였는가? |
| RQ3 | 하네스 vs 단독 에이전트의 실질적 차이는 무엇인가? (추가 비교 실험 필요) |
| RQ4 | 동일 플랫폼에서 Red/Blue/Purple 보안 운용을 수행한 운영 교훈은? |

---

## 논문 구성 (안)

### 1. Introduction
- IT 운영 자동화에서 LLM 에이전트 플랫폼 구축의 도전
- 기존 사례 연구 부재 (대부분 프레임워크 제안, 구축 여정은 미공개)
- 본 논문의 기여: 25 마일스톤 설계·구축·운용 사례

### 2. Platform Overview
- OpsClaw 아키텍처 요약 (Paper 1 인용)
- 기술 스택: Python 3.11, FastAPI, LangGraph, PostgreSQL 15
- 인프라: 4대 서버 (control plane, IPS, WAF, SIEM)

### 3. Development Journey: 25 Milestones
- 3.1 설계 기준선 확립 (M0~M2)
  - 역할 분리 원칙, 서비스/패키지 경계, DB 스키마
  - 교훈: "설계 기준 문서를 먼저 고정하라"
- 3.2 핵심 서비스 구현 (M3~M12)
  - Project lifecycle, Asset registry, Evidence, Skill/Tool/Playbook
  - 교훈: "pi runtime 연동의 경계를 명확히", "LangGraph 상태 머신의 이점과 비용"
- 3.3 모드 분리와 외부 Master (M13~M15)
  - Mode A(Native) vs Mode B(External) 분기점
  - 교훈: "Master 교체 가능성이 아키텍처를 결정"
- 3.4 PoW 블록체인과 RL (M18, M27)
  - PoW 도입 동기, 시간대 버그(B-02), linked-list 재구성
  - RL Q-learning 도입, UCB1 탐색
  - 교훈: "타임스탬프에 의존하지 마라", "advisory lock의 중요성"
- 3.5 버그 수정과 보안 패치 (M21, M28)
  - 5건 버그 일괄 수정 (B-01~B-05)
  - API 인증 미들웨어 긴급 추가 (Purple Team에서 RCE 발견)
  - 교훈: "control-plane 보안은 보호 대상만큼 중요"
- 3.6 보안 실험 운용 (M25~)
  - Red/Blue/Purple Team 16시간 자율 실행
  - Wazuh Agent 버전 불일치 이슈
  - 교훈: "인프라 호환성 검증을 실험 전에"

### 4. Comparative Experiment (추가 실험 필요)
- **OpsClaw vs Claude Code 단독** — 공정한 비교 설계
  - 동일 태스크를 양쪽 모두 병렬 실행 허용
  - 비교 차원: 증적 완전성, 재현성, 프로젝트 추적성, RL 정책 활용
  - (속도 비교는 공정성 문제로 제외하거나, 양쪽 모두 병렬 조건에서 측정)
- **OpsClaw vs Codex CLI** (환경 구축 후)
- **OpsClaw vs CALDERA** (보안 자동화 비교)

### 5. Lessons Learned
- 5.1 아키텍처 교훈
  - 위임 분리의 가치와 비용
  - 상태 머신의 무효 전이 차단 효과
  - Playbook 결정론 vs LLM 유연성의 트레이드오프
- 5.2 운영 교훈
  - PoW 체인의 실용적 가치 (감사, 디버깅, 보상 추적)
  - 한국어 FTS 미지원의 실무 영향
  - SubAgent 배포·업데이트의 운영 부담
- 5.3 보안 운용 교훈
  - LLM 에이전트의 sudo 발견 능력
  - SIEM 무력화 가능성과 대응
  - 네트워크 차단 vs 탐지의 상호보완

### 6. Discussion
- 유사 플랫폼 구축 시 권장사항
- 한계점 (단일 팀 개발, LLM 의존성, 비용)
- 향후 연구

### 7. Conclusion

---

## 추가 실험 필요 항목

| 실험 | 내용 | 상태 |
|------|------|------|
| OpsClaw vs Claude Code (공정 비교) | 양쪽 병렬 허용, 증적/재현성/추적성 비교 | ⬜ 미실행 |
| OpsClaw vs Codex CLI | Codex 환경 구축 후 동일 시나리오 | ⬜ 미실행 |
| OpsClaw vs CALDERA | 보안 에뮬레이션 비교 | ⬜ 미실행 |
| Blue Team T2~T4 | 네트워크/권한상승/SIEM 우회 방어 룰 생성 | ⬜ 미실행 |

## 대상 학회
- 산업 트랙: ICSE-SEIP, ASE Industry, SoCC Industry
- 경험 보고: IEEE Software, ACM Queue
- 보안 운용: ACSAC Practitioner, USENIX LISA

## 소스 데이터
- 마일스톤 보고서: `docs/m0/` ~ `docs/m20/`
- 로드맵: `docs/roadmap.md`
- 버그 이력: CLAUDE.md 버그/패치 테이블
- 보안 실험: `docs/paper/results/`, `docs/usr_report/260325/`
