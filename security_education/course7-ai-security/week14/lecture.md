# Week 14: RL Steering

## 학습 목표
- 강화학습 보상 함수(Reward Function)의 설계 원칙을 이해한다
- 보상 함수로 AI 에이전트의 행동을 통제하는 방법을 익힌다
- OpsClaw의 RL 시스템을 활용한 행동 조향(steering)을 실습한다
- 보상 해킹(reward hacking) 위험과 방지 방법을 이해한다

---

## 1. RL Steering이란?

보상 함수를 설계하여 AI 에이전트의 행동을 원하는 방향으로 유도하는 기술이다.

### 핵심 아이디어

```
보상이 높은 행동 → 에이전트가 더 자주 선택
보상이 낮은 행동 → 에이전트가 회피
```

보안 관점에서:
- 안전한 행동에 높은 보상 → 에이전트가 안전하게 행동
- 위험한 행동에 패널티 → 에이전트가 위험 행동 회피

---

## 2. 보상 함수 설계

### 2.1 보안 에이전트의 보상 요소

| 요소 | 높은 보상 | 낮은 보상/패널티 |
|------|----------|----------------|
| 작업 성공 | 명령 성공적 실행 | 실행 실패, 에러 |
| 안전성 | low risk 사용 | critical risk 남용 |
| 효율성 | 빠른 실행 | 불필요하게 느림 |
| 정확성 | 올바른 탐지 | 오탐(false positive) |
| 영향 최소화 | 읽기 전용 작업 | 파괴적 작업 |

### 2.2 보상 함수 예시

```python
def calculate_reward(task_result):
    """보안 에이전트 보상 함수"""
    reward = 0.0

    # 기본 성공/실패
    if task_result["success"]:
        reward += 1.0
    else:
        reward -= 0.5

    # 위험도에 따른 보상 조정
    risk_weights = {
        "low": 0.2,      # 안전한 작업은 소소한 보상
        "medium": 0.5,    # 중간 위험은 중간 보상
        "high": 1.0,      # 높은 위험을 성공하면 높은 보상
        "critical": 2.0   # 크리티컬 성공은 큰 보상
    }
    reward *= risk_weights.get(task_result["risk_level"], 0.1)

    # 파괴적 명령 패널티
    destructive = ["rm -rf", "DROP TABLE", "mkfs", "dd if="]
    if any(d in task_result.get("command", "") for d in destructive):
        reward -= 5.0     # 큰 패널티

    # 실행 시간 보너스 (10초 이내면 보너스)
    if task_result.get("duration_sec", 999) < 10:
        reward += 0.1

    return reward
```

---

## 3. 행동 통제 패턴

### 3.1 보수적 에이전트 (안전 우선)

```python
CONSERVATIVE_REWARDS = {
    "low_success": +1.0,
    "medium_success": +0.5,
    "high_success": +0.3,
    "critical_success": -0.5,    # critical은 성공해도 패널티!
    "any_failure": -2.0,
    "destructive": -10.0
}
```

### 3.2 적극적 에이전트 (탐색 우선)

```python
AGGRESSIVE_REWARDS = {
    "low_success": +0.1,
    "medium_success": +0.5,
    "high_success": +2.0,
    "critical_success": +5.0,    # 높은 위험 성공에 큰 보상
    "any_failure": -0.5,
    "new_discovery": +3.0        # 새로운 발견에 보너스
}
```

### 3.3 상황에 따른 전환

```
평시: 보수적 정책 → 안전한 모니터링
인시던트: 적극적 정책 → 빠른 정보 수집
복구: 보수적 정책 → 안정적 복구
```

---

## 4. OpsClaw RL 시스템 활용

### 4.1 현재 정책 확인

```bash
curl -s http://localhost:8000/rl/policy \
  -H "X-API-Key: opsclaw-api-key-2026" | python3 -m json.tool
```

### 4.2 보상 데이터 축적

```bash
# 다양한 risk_level의 태스크를 실행하여 보상 데이터 축적
PID="프로젝트_ID"

curl -s -X POST "http://localhost:8000/projects/$PID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "tasks": [
      {"order":1, "instruction_prompt":"hostname", "risk_level":"low"},
      {"order":2, "instruction_prompt":"uptime", "risk_level":"low"},
      {"order":3, "instruction_prompt":"ss -tlnp", "risk_level":"medium"},
      {"order":4, "instruction_prompt":"cat /etc/passwd", "risk_level":"medium"},
      {"order":5, "instruction_prompt":"last -20", "risk_level":"high"}
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

### 4.3 학습 및 추천 확인

```bash
# RL 학습 실행
curl -s -X POST http://localhost:8000/rl/train \
  -H "X-API-Key: opsclaw-api-key-2026" | python3 -m json.tool

# risk_level별 추천 확인
for level in low medium high critical; do
  echo "--- $level ---"
  curl -s "http://localhost:8000/rl/recommend?agent_id=http://localhost:8002&risk_level=$level" \
    -H "X-API-Key: opsclaw-api-key-2026"
  echo ""
done
```

---

## 5. 보상 해킹 (Reward Hacking)

에이전트가 보상을 최대화하기 위해 **의도하지 않은 방법**을 찾는 현상이다.

### 5.1 예시

| 보상 설계 | 해킹 행동 | 문제 |
|----------|----------|------|
| 작업 수 보상 | 무의미한 작업 반복 | 리소스 낭비 |
| 성공률 보상 | 쉬운 작업만 선택 | 어려운 문제 회피 |
| 탐지 수 보상 | 오탐 대량 생성 | 신호 대 잡음비 하락 |

### 5.2 방지 방법

```python
# 방법 1: 다목적 보상 (여러 지표 균형)
reward = 0.4 * success_score + 0.3 * safety_score + 0.2 * efficiency_score + 0.1 * novelty_score

# 방법 2: 보상 상한 (과도한 보상 방지)
reward = min(reward, MAX_REWARD)

# 방법 3: 사람 검증 (주기적 감사)
if random.random() < 0.1:  # 10% 확률로 사람 검증
    reward = human_evaluate(task_result)
```

---

## 6. 실습

### 실습 1: 보상 함수 설계

```bash
# LLM에게 보상 함수 설계를 요청
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "강화학습 보상 함수 설계 전문가입니다."},
      {"role": "user", "content": "보안 관제 AI 에이전트를 위한 보상 함수를 설계해주세요.\n\n에이전트 행동: 로그 분석, 취약점 스캔, 방화벽 규칙 변경, 서비스 재시작\n목표: 안전하게 위협을 탐지하고 대응하되, 서비스 가용성을 유지\n\n각 행동에 대한 보상/패널티를 Python 함수로 작성하세요. 보상 해킹 방지 로직도 포함하세요."}
    ],
    "temperature": 0.4
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

### 실습 2: 정책 변화 관찰

```bash
# 여러 차례 태스크 실행 후 학습하여 정책 변화 관찰

# 1차 실행 (low risk 위주)
curl -s -X POST "http://localhost:8000/projects/$PID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"tasks":[{"order":1,"instruction_prompt":"date","risk_level":"low"},{"order":2,"instruction_prompt":"whoami","risk_level":"low"}],"subagent_url":"http://localhost:8002"}'

# 학습
curl -s -X POST http://localhost:8000/rl/train -H "X-API-Key: opsclaw-api-key-2026"

# 추천 확인
curl -s "http://localhost:8000/rl/recommend?agent_id=http://localhost:8002&risk_level=low" \
  -H "X-API-Key: opsclaw-api-key-2026" | python3 -m json.tool
```

### 실습 3: 보상 해킹 시나리오 분석

```bash
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "AI 안전성 연구자입니다."},
      {"role": "user", "content": "다음 보상 함수에서 가능한 보상 해킹 시나리오를 3가지 찾고 각각의 방지 방법을 제시하세요:\n\nreward = task_count * 0.1 + success_rate * 2.0 + alerts_detected * 0.5\n\n(task_count: 실행 태스크 수, success_rate: 성공률, alerts_detected: 탐지 알림 수)"}
    ],
    "temperature": 0.4
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

---

## 7. RL Steering의 미래

```
현재: 단순 Q-learning (상태-행동 테이블)
      ↓
발전: Deep RL (신경망 기반 정책)
      ↓
목표: RLHF (사람 피드백 기반 학습)
      ↓
비전: 자율 보안 에이전트의 안전한 행동 보장
```

---

## 핵심 정리

1. 보상 함수 설계로 에이전트의 행동 방향을 결정한다
2. 안전 우선(보수적) vs 탐색 우선(적극적) 정책을 상황에 따라 전환한다
3. 보상 해킹을 방지하기 위해 다목적 보상, 상한 설정, 사람 검증을 적용한다
4. OpsClaw의 RL train/recommend로 데이터 기반 행동 정책을 학습한다
5. RL Steering은 자율 AI 에이전트의 안전성을 보장하는 핵심 기술이다

---

## 다음 주 예고
- Week 15: 기말고사 - AI 보안 자동화 종합 과제
