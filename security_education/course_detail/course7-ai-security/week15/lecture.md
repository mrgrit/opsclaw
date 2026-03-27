# Week 15: 기말고사 - AI 보안 자동화 (상세 버전)

## 학습 목표

- 각 개념의 보안 관점에서의 위험과 대응 방안을 분석할 수 있다
- OpsClaw를 활용하여 실습 작업을 자동화하고 증적을 관리할 수 있다
- 실제 보안 사고 사례와 연결하여 학습 내용을 적용할 수 있다


## 실습 환경 (공통)

| 서버 | IP | 역할 | 접속 |
|------|-----|------|------|
| opsclaw | 10.20.30.201 | Control Plane (OpsClaw) | `ssh opsclaw@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS (nftables, Suricata) | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 웹서버 (JuiceShop:3000, Apache:80) | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh:443, OpenCTI:9400) | `sshpass -p1 ssh siem@10.20.30.100` |
| dgx-spark | 192.168.0.105 | AI/GPU (Ollama:11434) | 원격 API만 |

**OpsClaw API:** `http://localhost:8000` / Key: `opsclaw-api-key-2026`


## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | 이론 강의 (Part 1) | 강의 |
| 0:40-1:10 | 이론 심화 + 사례 분석 (Part 2) | 강의/토론 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | 실습 (Part 3) | 실습 |
| 2:00-2:40 | 심화 실습 + 도구 활용 (Part 4) | 실습 |
| 2:40-2:50 | 휴식 | - |
| 2:50-3:20 | 응용 실습 + OpsClaw 연동 (Part 5) | 실습 |
| 3:20-3:40 | 복습 퀴즈 + 과제 안내 (Part 6) | 퀴즈 |

---


---

## 용어 해설 (AI/LLM 보안 활용 과목)

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **LLM** | Large Language Model | 대규모 언어 모델 (GPT, Claude, Llama 등) | 방대한 텍스트로 훈련된 AI 두뇌 |
| **Ollama** | Ollama | 로컬에서 LLM을 실행하는 도구 | 내 PC에서 돌리는 AI |
| **프롬프트** | Prompt | LLM에게 보내는 입력 텍스트 | AI에게 하는 질문/지시 |
| **토큰** | Token (LLM) | LLM이 처리하는 텍스트의 최소 단위 (~4글자) | 단어의 조각 |
| **컨텍스트 윈도우** | Context Window | LLM이 한 번에 처리할 수 있는 최대 토큰 수 | AI의 단기 기억 용량 |
| **파인튜닝** | Fine-tuning | 사전 학습된 모델을 특정 목적에 맞게 추가 학습 | 일반의가 전공 수련 |
| **RAG** | Retrieval-Augmented Generation | 외부 데이터를 검색하여 LLM 응답에 반영 | AI가 자료를 찾아보고 답변 |
| **에이전트** | Agent (AI) | 도구를 사용하여 자율적으로 작업하는 AI 시스템 | AI 비서 (스스로 판단하고 실행) |
| **도구 호출** | Tool Calling | LLM이 외부 도구/API를 호출하는 기능 | AI가 계산기를 꺼내서 계산 |
| **하네스** | Harness | 에이전트를 관리·제어하는 프레임워크 | AI 비서의 업무 규칙·관리 시스템 |
| **Playbook** | Playbook | 자동화된 작업 절차 (도구/스킬의 순서화된 묶음) | 표준 작업 지침서 (SOP) |
| **PoW** | Proof of Work | 작업 증명 (해시 체인 기반 실행 기록) | 작업 일지 + 영수증 |
| **보상** | Reward (RL) | 태스크 실행 결과에 따른 점수 (+성공, -실패) | 성과급 |
| **Q-learning** | Q-learning | 보상을 기반으로 최적 행동을 학습하는 RL 알고리즘 | 시행착오로 최적 경로를 찾는 학습 |
| **UCB1** | Upper Confidence Bound | 탐험(exploration)과 활용(exploitation)을 균형 잡는 전략 | "가본 길 vs 안 가본 길" 선택 전략 |
| **SubAgent** | SubAgent | 대상 서버에서 명령을 실행하는 경량 런타임 | 현장 파견 직원 |


# 본 강의 내용

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


---

---

## 심화: AI/LLM 보안 활용 보충

### Ollama API 상세 가이드

#### 기본 호출 구조

```bash
# Ollama는 OpenAI 호환 API를 제공한다
# URL: http://192.168.0.105:11434/v1/chat/completions

curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",        ← 사용할 모델
    "messages": [
      {"role": "system", "content": "역할 부여"},  ← 시스템 프롬프트
      {"role": "user", "content": "실제 질문"}      ← 사용자 입력
    ],
    "temperature": 0.1,            ← 출력 다양성 (0=결정론, 1=창의적)
    "max_tokens": 1000             ← 최대 출력 길이
  }'
```

> **각 파라미터의 의미:**
> - `model`: 어떤 AI 모델을 사용할지. 큰 모델일수록 정확하지만 느림
> - `messages`: 대화 내역. system(역할)→user(질문)→assistant(답변) 순서
> - `temperature`: 0에 가까우면 같은 질문에 항상 같은 답. 1에 가까우면 매번 다른 답
> - `max_tokens`: 출력 길이 제한. 토큰 ≈ 글자 수 × 0.5 (한국어)

#### 모델별 특성

| 모델 | 크기 | 응답 시간 | 정확도 | 권장 용도 |
|------|------|---------|--------|---------|
| gemma3:12b | 12B | ~5초 | 양호 | 분석, 룰 생성, 보고서 |
| llama3.1:8b | 8B | ~3초 | 보통 | 빠른 분류, 검증 |
| qwen3:8b | 8B | ~5초 | 보통 | 교차 검증 (다른 벤더) |
| gpt-oss:120b | 120B | ~25초 | 높음 | 복잡한 분석 (시간 여유 시) |

#### 프롬프트 엔지니어링 패턴

**패턴 1: 역할 부여 (Role Assignment)**
```json
{"role":"system","content":"당신은 10년 경력의 SOC 분석가입니다. MITRE ATT&CK에 정통합니다."}
```

**패턴 2: 출력 형식 강제 (Format Control)**
```json
{"role":"system","content":"반드시 JSON으로만 응답하세요. 마크다운, 설명, 주석을 포함하지 마세요."}
```

**패턴 3: Few-shot (예시 제공)**
```json
{"role":"user","content":"예시:\n입력: SSH 실패 5회\n출력: {\"severity\":\"HIGH\",\"attack\":\"brute_force\"}\n\n이제 분석하세요: SSH 실패 20회 후 성공"}
```

**패턴 4: Chain of Thought (단계별 사고)**
```json
{"role":"system","content":"단계별로 분석하세요: 1)현상 파악 2)원인 추론 3)ATT&CK 매핑 4)대응 방안"}
```

### OpsClaw API 핵심 흐름 요약

```
[1] POST /projects                     → 프로젝트 생성
    Body: {"name":"...", "master_mode":"external"}
    Response: {"project":{"id":"prj_xxx"}}

[2] POST /projects/{id}/plan           → plan 단계로 전환
[3] POST /projects/{id}/execute        → execute 단계로 전환

[4] POST /projects/{id}/execute-plan   → 태스크 실행
    Body: {"tasks":[...], "parallel":true, "subagent_url":"..."}
    Response: {"overall":"success", "tasks_ok":N}

[5] GET /projects/{id}/evidence/summary → 증적 확인
[6] GET /projects/{id}/replay           → 타임라인 재구성
[7] POST /projects/{id}/completion-report → 완료 보고

모든 API에 필수: -H "X-API-Key: opsclaw-api-key-2026"
```

## 보충 실습

### 보충 실습 1: 기본 동작 확인

이론에서 배운 내용을 직접 확인하는 기초 실습이다.

```bash
# Step 1: 현재 상태 확인
echo "=== 현재 상태 ==="
# (해당 주차에 맞는 확인 명령)

# Step 2: 설정/변경 적용
echo "=== 변경 적용 ==="
# (해당 주차에 맞는 실습 명령)

# Step 3: 결과 검증
echo "=== 결과 확인 ==="
# (변경 결과 확인 명령)
```

> **트러블슈팅:**
> - 명령이 실패하면: 권한(sudo), 경로, 서비스 상태를 먼저 확인
> - 예상과 다른 결과: 이전 실습의 설정이 남아있을 수 있으므로 초기화 후 재시도
> - 타임아웃: 네트워크 연결 또는 서비스 가동 상태 확인

### 보충 실습 2: 탐지/모니터링 관점

공격자가 아닌 **방어자 관점**에서 동일한 활동을 모니터링하는 실습이다.

```bash
# siem 서버에서 관련 로그 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100 \
  "sudo cat /var/ossec/logs/alerts/alerts.json | tail -5" 2>/dev/null

# Suricata 알림 확인 (해당 시)
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \
  "sudo tail -20 /var/log/suricata/fast.log" 2>/dev/null
```

> **왜 방어자 관점도 배우는가?**
> 공격 기법만 알면 "스크립트 키디"에 불과하다.
> 공격이 어떻게 탐지되는지 이해해야 진정한 보안 전문가이다.
> 이 과목의 모든 공격 실습에는 대응하는 탐지/방어 관점이 포함된다.

### 보충 실습 3: OpsClaw 자동화

이번 주차의 핵심 실습을 OpsClaw execute-plan으로 자동화한다.

```bash
# 프로젝트 생성 (이번 주차용)
RESULT=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"name":"weekXX-lab","request_text":"이번 주차 실습 자동화","master_mode":"external"}')
PID=$(echo $RESULT | python3 -c "import sys,json; print(json.load(sys.stdin)['project']['id'])")

# Stage 전환
curl -s -X POST "http://localhost:8000/projects/$PID/plan" -H "X-API-Key: opsclaw-api-key-2026" > /dev/null
curl -s -X POST "http://localhost:8000/projects/$PID/execute" -H "X-API-Key: opsclaw-api-key-2026" > /dev/null

# 실습 태스크 실행 (해당 주차에 맞게 수정)
curl -s -X POST "http://localhost:8000/projects/$PID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "tasks": [
      {"order":1,"title":"실습 태스크 1","instruction_prompt":"echo 실습1","risk_level":"low","subagent_url":"http://localhost:8002"},
      {"order":2,"title":"실습 태스크 2","instruction_prompt":"echo 실습2","risk_level":"low","subagent_url":"http://10.20.30.80:8002"}
    ],
    "subagent_url":"http://localhost:8002",
    "parallel":true
  }'

# Evidence 확인
curl -s "http://localhost:8000/projects/$PID/evidence/summary" \
  -H "X-API-Key: opsclaw-api-key-2026" | python3 -m json.tool
```


---

## 자가 점검 퀴즈 (10문항)

이번 주차의 핵심 내용을 점검한다. 8/10 이상 정답을 목표로 한다.

**Q1.** 이번 주차 "Week 15: 기말고사 - AI 보안 자동화"의 핵심 목적은 무엇인가?
- (a) 네트워크 속도 향상  (b) **LLM 기법/개념의 이해와 실습**  (c) 데이터베이스 관리  (d) UI 디자인

**Q2.** 이 주제에서 AI 보안의 역할은?
- (a) 성능 최적화  (b) 비용 절감  (c) **체계적 분류와 대응 기준 제공**  (d) 사용자 편의

**Q3.** 실습에서 사용한 주요 도구/명령어의 1차 목적은?
- (a) 파일 복사  (b) **OpsClaw 수행 및 결과 확인**  (c) 메모리 관리  (d) 화면 출력

**Q4.** OpsClaw를 통해 실습을 실행하는 가장 큰 이점은?
- (a) 속도  (b) **모든 실행의 자동 증적(evidence) 기록**  (c) 무료  (d) 간편함

**Q5.** 이 주제의 보안 위험이 높은 이유는?
- (a) 비용이 많이 들어서  (b) 복잡해서  (c) **악용 시 시스템/데이터에 직접적 피해**  (d) 법적 문제

**Q6.** 방어/대응의 핵심 원칙은?
- (a) 모든 트래픽 차단  (b) **최소 권한 + 탐지 + 대응의 조합**  (c) 서버 재시작  (d) 비밀번호 변경

**Q7.** 실습 결과를 분석할 때 가장 먼저 확인해야 하는 것은?
- (a) 서버 이름  (b) **exit_code (성공/실패 여부)**  (c) 파일 크기  (d) 날짜

**Q8.** 이 주제와 관련된 MITRE ATT&CK 전술은?
- (a) Impact만  (b) Reconnaissance만  (c) **주제에 해당하는 전술(들)**  (d) 해당 없음

**Q9.** 실무에서 이 기법/도구를 사용할 때 가장 주의할 점은?
- (a) 속도  (b) **법적 허가와 범위 준수**  (c) 비용  (d) 보고서 양식

**Q10.** 다음 주차와의 연결 포인트는?
- (a) 관련 없음  (b) **이번 주 결과를 다음 주에서 활용/심화**  (c) 완전히 다른 주제  (d) 복습만

**정답:** Q1:b, Q2:c, Q3:b, Q4:b, Q5:c, Q6:b, Q7:b, Q8:c, Q9:b, Q10:b

---

## 과제 (다음 주까지)

### 과제 1: 이론 정리 보고서 (30점)

이번 주차의 핵심 개념을 자신의 말로 정리하라.

| 항목 | 배점 |
|------|------|
| 핵심 개념 정의 및 설명 | 10점 |
| 실습 결과 캡처 및 해석 | 10점 |
| 보안 관점 분석 (공격↔방어) | 10점 |

### 과제 2: 실습 수행 보고서 (40점)

이번 주차의 모든 실습을 수행하고 결과를 보고서로 작성하라.

| 항목 | 배점 |
|------|------|
| 실습 명령어 및 실행 결과 캡처 | 15점 |
| 결과 해석 및 보안 의미 분석 | 15점 |
| 트러블슈팅 경험 (있는 경우) | 10점 |

### 과제 3: OpsClaw 자동화 (30점)

이번 주차의 핵심 실습을 OpsClaw execute-plan으로 자동화하라.

| 항목 | 배점 |
|------|------|
| 프로젝트 생성 + stage 전환 | 5점 |
| execute-plan 태스크 설계 (3개 이상) | 10점 |
| evidence/summary 결과 | 5점 |
| replay 타임라인 결과 | 5점 |
| 자동화의 이점 분석 (직접 실행 대비) | 5점 |

**제출:** 보고서(PDF 또는 MD) + OpsClaw project_id


---

## 검증 체크리스트

이번 주차의 학습을 완료하려면 다음 항목을 모두 확인하라:

- [ ] 이론 강의 내용 이해 (핵심 용어 설명 가능)
- [ ] 기본 실습 모두 수행 완료
- [ ] 보충 실습 1 (기본 동작 확인) 완료
- [ ] 보충 실습 2 (탐지/모니터링 관점) 수행
- [ ] 보충 실습 3 (OpsClaw 자동화) 수행
- [ ] 자가 점검 퀴즈 8/10 이상 정답
- [ ] 과제 1 (이론 정리) 작성
- [ ] 과제 2 (실습 보고서) 작성
- [ ] 과제 3 (OpsClaw 자동화) 완료

