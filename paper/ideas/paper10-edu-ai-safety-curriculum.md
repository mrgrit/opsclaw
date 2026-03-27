---
name: Paper 10 아이디어 — AI Safety 교육 커리큘럼 설계
description: 프롬프트 인젝션부터 에이전트 위협까지. 실습형 AI Safety 교육과정 설계 및 평가.
type: project
---

## 핵심 주장
AI Safety는 이론 중심 교육이 대부분이나, 프롬프트 인젝션/탈옥/적대적 공격을 실제로 실습하는 커리큘럼이 학습 효과가 더 높다.

## 커리큘럼 구성 (15주)
- 프롬프트 인젝션 (직접/간접/다단계)
- LLM 탈옥 (DAN, 역할극, 다국어)
- 가드레일과 방어
- 적대적 입력
- 데이터 오염
- 모델 보안 (추출, 멤버십 추론)
- 에이전트 보안 위협
- RAG 보안
- AI 윤리/규제

## 실습 환경
- Ollama (로컬 LLM: gemma3:12b, llama3.1:8b)
- OpsClaw (에이전트 보안 시나리오)
- 각 주차에 실제 공격/방어 실습

## 필요 실험
- 15주 파일럿 수업 실시
- 학생의 AI Safety 인식도 사전/사후 비교
- 실습 vs 이론 그룹 비교

## 대상 학회
AI Safety: AAAI Workshop on AI Safety, NeurIPS SoLaR
교육: ACM SIGCSE, IEEE FIE
AI 윤리: AIES (AAAI/ACM Conference on AI, Ethics, and Society)
