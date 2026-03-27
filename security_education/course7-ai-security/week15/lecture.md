# Week 15: 기말고사 - AI 보안 자동화

## 시험 개요

| 항목 | 내용 |
|------|------|
| 유형 | 종합 실기 (자동화 파이프라인 구축) |
| 시간 | 120분 |
| 배점 | 100점 |
| 환경 | Ollama (192.168.0.105:11434), OpsClaw (localhost:8000) |
| 제출 | 스크립트 + 실행 결과 + 최종 보고서 |

---

## 시험 범위

- Week 02~07: LLM 기초, 프롬프트, 로그 분석, 룰 생성, 취약점, 에이전트 아키텍처
- Week 09~14: OpsClaw, Playbook, RL, 자율 미션, Daemon, 분산 지식, RL Steering

---

## 문제 1: AI 보안 관제 파이프라인 (40점)

### 시나리오

"SecureCorp"의 보안팀에 AI 기반 관제 시스템을 구축하라.
다음 파이프라인을 완성해야 한다:

```
로그 수집 → LLM 분석 → 위협 분류 → 룰 생성 → 대응 실행
```

### 1-1. 로그 수집 + LLM 분석 (15점)

OpsClaw를 사용하여 여러 서버에서 보안 로그를 수집하고 LLM으로 분석하라.

```bash
# 프로젝트 생성
PID=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"name":"final-pipeline","request_text":"AI 보안 관제","master_mode":"external"}' \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")

# Stage 전환 + 다중 서버 로그 수집
# (execute-plan으로 최소 3개 서버에서 보안 로그 수집)

# LLM으로 수집된 로그 분석
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "SOC 분석가입니다. 수집된 로그를 분석하세요."},
      {"role": "user", "content": "[수집된 로그 데이터]"}
    ]
  }'
```

### 1-2. 위협 분류 + 룰 생성 (15점)

분석 결과에서 위협을 분류하고 탐지 룰을 자동 생성하라.

- 최소 2개의 SIGMA 또는 Wazuh 룰을 LLM으로 생성
- 생성된 룰을 LLM으로 상호 검증

### 1-3. 대응 실행 (10점)

탐지된 위협에 대한 대응 조치를 OpsClaw로 실행하라.

- execute-plan으로 대응 태스크 실행
- 결과 확인 및 완료 보고

---

## 문제 2: 자율 Purple Team (30점)

### 2-1. Red Team 미션 (10점)

LLM을 활용하여 대상 서버의 보안 취약점을 탐색하라.

```bash
# Red Team: 대상 서버 정보 수집 및 취약점 식별
# Ollama API를 사용하여 탐색 계획 수립
# OpsClaw로 실제 정보 수집 실행
```

### 2-2. Blue Team 대응 (10점)

Red Team 발견사항에 대한 방어 조치를 생성하고 실행하라.

```bash
# Blue Team: 발견된 취약점에 대한 방어 조치 생성
# LLM으로 방어 명령어 생성
# OpsClaw로 방어 조치 실행 (안전한 것만)
```

### 2-3. Purple Team 보고서 (10점)

Red/Blue Team 활동 결과를 종합 보고서로 작성하라.

포함 내용:
- 발견된 취약점 목록
- 대응 조치 내역
- 잔존 위험
- 개선 권고사항

---

## 문제 3: RL 정책 분석 (30점)

### 3-1. 보상 데이터 축적 (10점)

다양한 risk_level의 태스크를 실행하여 보상 데이터를 축적하라.

```bash
# low, medium, high 태스크 각 3개 이상 실행
# execute-plan으로 일괄 실행
```

### 3-2. RL 학습 및 정책 분석 (10점)

```bash
# 학습 실행
curl -s -X POST http://localhost:8000/rl/train \
  -H "X-API-Key: opsclaw-api-key-2026"

# 정책 확인
curl -s http://localhost:8000/rl/policy \
  -H "X-API-Key: opsclaw-api-key-2026"

# risk_level별 추천 분석
```

### 3-3. 보상 함수 설계 제안 (10점)

LLM을 활용하여 보안 에이전트를 위한 최적 보상 함수를 설계하라.

```bash
# LLM에게 보상 함수 설계를 요청
# 보상 해킹 방지 로직 포함
# Python 코드로 작성
```

---

## 채점 기준

| 항목 | 배점 | 기준 |
|------|------|------|
| 로그 수집 + 분석 | 15 | 다중 서버, 분석 깊이 |
| 룰 생성 + 검증 | 15 | 룰 정확성, 검증 충실 |
| 대응 실행 | 10 | 플로우 완성도 |
| Red Team | 10 | 탐색 체계성, 발견 내용 |
| Blue Team | 10 | 대응 적절성, 실행 결과 |
| Purple 보고서 | 10 | 종합 분석, 보고서 품질 |
| 보상 축적 | 10 | 다양한 데이터 |
| 정책 분석 | 10 | 분석 깊이 |
| 보상 설계 | 10 | 설계 합리성, 해킹 방지 |

---

## 참고: API 정리

```bash
# Ollama LLM
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"gemma3:12b","messages":[...]}'

# OpsClaw
HEADER="-H 'X-API-Key: opsclaw-api-key-2026'"

# 프로젝트: POST /projects
# Stage: POST /projects/{id}/plan, /execute
# 실행: POST /projects/{id}/dispatch, /execute-plan
# 증거: GET /projects/{id}/evidence/summary
# 완료: POST /projects/{id}/completion-report
# PoW: GET /pow/blocks, /pow/verify, /pow/leaderboard
# RL: POST /rl/train, GET /rl/recommend, /rl/policy
```

---

## 학기 마무리

이 과목에서 학습한 핵심:

1. **LLM 활용**: Ollama API로 보안 분석, 룰 생성, 보고서 작성
2. **프롬프트 엔지니어링**: 보안 업무 특화 프롬프트 설계
3. **AI 에이전트**: Master-Manager-SubAgent 계층 구조
4. **OpsClaw**: 프로젝트 관리, dispatch, execute-plan, Playbook
5. **자율 보안**: Red/Blue/Purple Team, Agent Daemon
6. **분산 지식**: local_knowledge, knowledge transfer
7. **RL Steering**: 보상 함수로 에이전트 행동 통제

AI는 보안 전문가를 대체하지 않는다. 보안 전문가의 능력을 **증폭**시키는 도구이다.
