---
name: Paper 8 아이디어 — CTF 자동 생성 및 적응형 난이도 조절
description: LLM이 학생 수준에 맞춰 CTF 문제를 자동 생성하고 난이도를 적응적으로 조절. JuiceShop 기반.
type: project
---

## 핵심 주장
LLM 에이전트가 학생의 실습 이력(VWR)을 분석하여 개인화된 CTF 문제를 자동 생성하고, RL 보상 기반으로 난이도를 적응적으로 조절할 수 있다.

## 메커니즘
1. 학생이 이전 실습에서 성공한 기법 → VWR로 추적
2. LLM이 학생이 못 푼 유형의 문제를 자동 생성
3. RL이 성공률 기반으로 난이도 조절 (너무 쉬우면 올리고, 어려우면 내리고)
4. JuiceShop + 커스텀 취약점 환경에서 실행

## 필요 실험
- CTF 문제 자동 생성 파이프라인 구축
- 학생 그룹 A/B 테스트 (고정 난이도 vs 적응형)
- 학습 효과 측정 (사전/사후 점검 점수)

## 대상 학회
교육: ACM SIGCSE, ACM ITiCSE
AI 교육: AAAI Symposium on Educational Advances in AI
게이미피케이션: CHI, CSCW
