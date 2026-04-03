# Week 09: AI vs AI 공방전 (1) — AI 공격 에이전트 아키텍처

## 학습 목표
- AI 기반 사이버 공격 에이전트의 아키텍처와 동작 원리를 이해한다
- LLM 기반 Red Agent의 킬체인 자동화 구현 방법을 실습한다
- LLM 기반 Blue Agent의 실시간 방어 아키텍처를 설계할 수 있다
- OpsClaw의 자율 SubAgent 미션 시스템을 활용한 AI 공방전을 구성할 수 있다
- AI 에이전트의 의사결정 프로세스와 제어 메커니즘을 이해한다

## 선수 지식
- 공방전 기초 과정 이수
- Week 01-08 공격/방어 기법 전반 이해
- LLM(대규모 언어 모델) 기본 개념

## 실습 환경

| 호스트 | IP | 역할 | 접속 |
|--------|-----|------|------|
| opsclaw | 10.20.30.201 | Control Plane | `ssh opsclaw@10.20.30.201` |
| secu | 10.20.30.1 | Blue Agent 환경 | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 공방전 대상 | `sshpass -p1 ssh web@10.20.30.80` |
| dgx-spark | 192.168.0.105 | GPU / Ollama LLM | `ssh dgx-spark` |

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | AI 에이전트 아키텍처 이론 | 강의 |
| 0:40-1:10 | Red Agent 설계 실습 | 실습 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | Blue Agent 설계 실습 | 실습 |
| 2:00-2:40 | OpsClaw AI 공방전 실행 | 실습 |
| 2:40-2:50 | 휴식 | - |
| 2:50-3:30 | AI 윤리 및 제어 토론 + 퀴즈 | 토론 |

---

# Part 1: AI 에이전트 아키텍처 이론 (40분)

## 1.1 AI 보안 에이전트 개요

AI 보안 에이전트는 LLM을 핵심 두뇌로 사용하여 **자율적으로 공격/방어 의사결정**을 수행하는 시스템이다.

```
[LLM Brain] → 상황 분석 → 계획 수립 → 도구 선택 → 실행 → 결과 해석 → 반복
     ↑                                        ↓
[System Prompt]                          [Tool Bridge]
(역할, 규칙, 지식)                    (run_command, fetch_log, ...)
```

## 1.2 Red Agent vs Blue Agent

| 특성 | Red Agent (공격) | Blue Agent (방어) |
|------|-----------------|-----------------|
| 목표 | 킬체인 완수 | 공격 차단/탐지 |
| LLM | 공격 기법 특화 | 방어/탐지 특화 |
| 도구 | nmap, curl, nc 등 | iptables, fail2ban 등 |
| 판단 기준 | 성공/실패/탐지 여부 | 위협 수준/오탐률 |
| 학습 | 공격 성공률 최대화 | 탐지율 최대화, 오탐 최소화 |

## 1.3 OpsClaw AI 에이전트 계층

```
Master (계획 수립)
  └── Manager API (조율, 기록, PoW)
        ├── Red SubAgent (gemma3:12b) → 공격 실행
        └── Blue SubAgent (llama3.1:8b) → 방어 실행
```

---

# Part 2: Red Agent 설계 실습 (30분)

## 2.1 Red Agent 시스템 프롬프트

```python
RED_AGENT_PROMPT = """
당신은 Red Team AI 에이전트입니다.
목표: 대상 시스템(10.20.30.80)에서 킬체인을 완수합니다.

규칙:
1. 먼저 정찰(nmap)을 수행합니다
2. 발견된 서비스의 취약점을 탐색합니다
3. 초기 침투를 시도합니다
4. 성공하면 persistence를 설치합니다
5. 각 단계에서 탐지 회피를 고려합니다

사용 가능한 도구: run_command, fetch_log
위험 제한: critical 명령은 dry_run으로 실행
"""
```

## 실습 2.1: Red Agent 미션 실행

> **목적**: AI가 자율적으로 정찰부터 침투까지 수행하는 과정을 관찰한다
> **배우는 것**: AI 에이전트의 의사결정 과정, 자율성 수준

```bash
# Red Agent 미션 실행 (OpsClaw SubAgent)
curl -X POST http://10.20.30.80:8002/a2a/mission \
  -H "Content-Type: application/json" \
  -d '{
    "role": "red",
    "objective": "10.20.30.80의 웹 서비스 취약점을 탐색하고 초기 침투를 시도하라",
    "constraints": ["파괴적 명령 금지", "데이터 유출 금지"],
    "max_steps": 10,
    "model": "gemma3:12b"
  }'
```

---

# Part 3: Blue Agent 설계 실습 (40분)

## 3.1 Blue Agent 시스템 프롬프트

```python
BLUE_AGENT_PROMPT = """
당신은 Blue Team AI 에이전트입니다.
목표: 시스템에 대한 공격을 탐지하고 차단합니다.

규칙:
1. 로그를 주기적으로 분석합니다
2. 이상 징후를 발견하면 원인을 분석합니다
3. 확인된 공격은 즉시 차단합니다
4. 오탐을 최소화합니다
5. 모든 판단에 대해 근거를 기록합니다

사용 가능한 도구: run_command, fetch_log, query_metric
"""
```

## 실습 3.1: Blue Agent 방어 미션

> **목적**: AI가 실시간으로 공격을 탐지하고 대응하는 과정을 관찰한다
> **배우는 것**: 방어 에이전트의 판단 루프

```bash
# Blue Agent 미션 실행
curl -X POST http://10.20.30.1:8002/a2a/mission \
  -H "Content-Type: application/json" \
  -d '{
    "role": "blue",
    "objective": "내부 네트워크에 대한 공격을 탐지하고 차단하라. Suricata/auth.log를 분석하라",
    "constraints": ["정상 트래픽 차단 금지", "서비스 중단 금지"],
    "max_steps": 10,
    "model": "llama3.1:8b"
  }'
```

---

# Part 4: AI 공방전 구성 및 제어 (40분)

## 실습 4.1: 동시 Red vs Blue 실행

> **목적**: Red와 Blue 에이전트를 동시에 실행하여 AI 공방전을 수행한다
> **배우는 것**: 에이전트 간 상호작용, 결과 분석

```bash
# OpsClaw 프로젝트로 AI 공방전 관리
curl -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "ai-battle-round1",
    "request_text": "AI Red vs Blue 공방전 1라운드",
    "master_mode": "external"
  }'

# 결과 확인: PoW 블록으로 공방전 기록 추적
curl -H "X-API-Key: $OPSCLAW_API_KEY" \
  "http://localhost:8000/pow/blocks?limit=20"

# 보상 비교
curl -H "X-API-Key: $OPSCLAW_API_KEY" \
  http://localhost:8000/pow/leaderboard
```

## 4.2 AI 에이전트 제어 메커니즘

| 제어 수준 | 메커니즘 | 설명 |
|----------|---------|------|
| 프롬프트 | System Prompt | 역할, 규칙, 제약 |
| 도구 | Tool Whitelist | 사용 가능 도구 제한 |
| 위험도 | Risk Level | critical → dry_run 강제 |
| 승인 | Human-in-the-Loop | 위험 작업 사전 승인 |
| 예산 | Cost Tracker | 토큰/비용 제한 |

---

## 검증 체크리스트
- [ ] AI 공격/방어 에이전트의 아키텍처를 도식으로 설명할 수 있다
- [ ] Red Agent의 킬체인 자동화 시스템 프롬프트를 설계할 수 있다
- [ ] Blue Agent의 탐지-대응 루프를 구현할 수 있다
- [ ] OpsClaw의 mission API를 사용하여 AI 공방전을 실행할 수 있다
- [ ] AI 에이전트의 5가지 제어 메커니즘을 설명할 수 있다

## 자가 점검 퀴즈
1. AI Red Agent가 기존 자동화 도구(Metasploit 자동공격)보다 우수한 점 3가지를 서술하시오.
2. Blue Agent가 오탐을 줄이기 위해 사용할 수 있는 전략은?
3. AI 에이전트의 "자율성 수준"을 정의하는 기준 3가지를 제시하시오.
4. Human-in-the-Loop 없이 AI 에이전트를 실행할 때의 위험은?
5. Red Agent와 Blue Agent에 서로 다른 LLM 모델을 사용하는 이유는?
