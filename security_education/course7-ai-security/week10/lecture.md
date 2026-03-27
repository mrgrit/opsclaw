# Week 10: OpsClaw (2) - Playbook + RL

## 학습 목표
- OpsClaw Playbook의 개념과 구조를 이해한다
- Playbook을 생성하고 실행할 수 있다
- 강화학습(RL) 보상 시스템의 원리를 이해한다
- RL 학습과 정책 추천 기능을 활용할 수 있다

---

## 1. Playbook이란?

Playbook은 반복적인 보안 작업을 재사용 가능한 절차로 정의한 것이다.
Ansible Playbook과 유사한 개념이다.

### Playbook vs 수동 실행

| 항목 | 수동 dispatch | Playbook |
|------|-------------|----------|
| 재사용 | 매번 작성 | 한 번 정의, 반복 사용 |
| 일관성 | 사람마다 다름 | 항상 동일 |
| 감사 | 명령어 추적 어려움 | 실행 이력 자동 기록 |
| 공유 | 개인 지식 | 팀 공유 가능 |

---

## 2. Playbook 구조

```json
{
  "name": "ssh-security-audit",
  "description": "SSH 보안 설정 점검 Playbook",
  "steps": [
    {
      "order": 1,
      "tool": "run_command",
      "params": {"command": "sshd -T | grep -E 'permitrootlogin|passwordauthentication|maxauthtries'"},
      "risk_level": "low",
      "description": "SSH 설정 확인"
    },
    {
      "order": 2,
      "tool": "run_command",
      "params": {"command": "last -20"},
      "risk_level": "low",
      "description": "최근 로그인 이력 확인"
    },
    {
      "order": 3,
      "tool": "run_command",
      "params": {"command": "grep 'Failed password' /var/log/auth.log | tail -20"},
      "risk_level": "low",
      "description": "인증 실패 로그 확인"
    }
  ]
}
```

---

## 3. Playbook 실행

### 3.1 Playbook을 execute-plan으로 실행

```bash
PID="프로젝트_ID"

# Playbook의 steps를 tasks로 변환하여 실행
curl -s -X POST "http://localhost:8000/projects/$PID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "sshd -T 2>/dev/null | grep -E \"permitrootlogin|passwordauthentication|maxauthtries\" || echo SSH_NOT_RUNNING",
        "risk_level": "low"
      },
      {
        "order": 2,
        "instruction_prompt": "last -10",
        "risk_level": "low"
      },
      {
        "order": 3,
        "instruction_prompt": "grep \"Failed password\" /var/log/auth.log 2>/dev/null | tail -10 || echo NO_AUTH_LOG",
        "risk_level": "low"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

---

## 4. 강화학습 (RL) 보상 시스템

### 4.1 PoW와 보상의 관계

```
태스크 실행 → PoW 블록 생성 → 보상(reward) 자동 계산
```

execute-plan으로 태스크를 실행하면 자동으로:
1. PoW 블록이 생성된다
2. 태스크 결과에 따라 보상이 기록된다
3. 보상 데이터가 RL 학습에 사용된다

### 4.2 보상 요소

| 요소 | 설명 | 보상 영향 |
|------|------|----------|
| 성공/실패 | 명령 실행 결과 | 성공 +1, 실패 -1 |
| risk_level | 태스크 위험도 | 높을수록 보상 큼 |
| 실행 시간 | 태스크 소요 시간 | 빠를수록 보상 큼 |
| 에이전트 | 실행한 SubAgent | 에이전트별 통계 |

### 4.3 Q-learning 기초

OpsClaw는 Q-learning 알고리즘으로 최적 행동을 학습한다.

```
Q(상태, 행동) = 현재 보상 + 감가율 * 미래 최대 보상
```

- **상태(State)**: 에이전트 ID + risk_level
- **행동(Action)**: 태스크 실행 여부
- **보상(Reward)**: 성공/실패 + 위험도 가중치

---

## 5. RL API 사용

### 5.1 학습 실행

```bash
# 축적된 보상 데이터로 Q-learning 학습
curl -s -X POST http://localhost:8000/rl/train \
  -H "X-API-Key: opsclaw-api-key-2026" | python3 -m json.tool
```

### 5.2 정책 추천

```bash
# 특정 에이전트+위험수준에 대한 최적 행동 추천
curl -s "http://localhost:8000/rl/recommend?agent_id=http://localhost:8002&risk_level=low" \
  -H "X-API-Key: opsclaw-api-key-2026" | python3 -m json.tool

curl -s "http://localhost:8000/rl/recommend?agent_id=http://localhost:8002&risk_level=high" \
  -H "X-API-Key: opsclaw-api-key-2026" | python3 -m json.tool
```

### 5.3 정책 상태 확인

```bash
# 현재 학습된 Q-table 상태
curl -s http://localhost:8000/rl/policy \
  -H "X-API-Key: opsclaw-api-key-2026" | python3 -m json.tool
```

### 5.4 보상 랭킹

```bash
# SubAgent별 누적 보상 순위
curl -s http://localhost:8000/pow/leaderboard \
  -H "X-API-Key: opsclaw-api-key-2026" | python3 -m json.tool
```

---

## 6. 실습

### 실습 1: 보안 점검 Playbook 실행

```bash
# 프로젝트 생성
PID=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"name":"playbook-lab","request_text":"Playbook 실습","master_mode":"external"}' \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")

# Stage 전환
curl -s -X POST "http://localhost:8000/projects/$PID/plan" \
  -H "X-API-Key: opsclaw-api-key-2026" > /dev/null
curl -s -X POST "http://localhost:8000/projects/$PID/execute" \
  -H "X-API-Key: opsclaw-api-key-2026" > /dev/null

# 시스템 보안 점검 Playbook 실행
curl -s -X POST "http://localhost:8000/projects/$PID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "tasks": [
      {"order":1, "instruction_prompt":"uname -a", "risk_level":"low"},
      {"order":2, "instruction_prompt":"ss -tlnp | head -20", "risk_level":"low"},
      {"order":3, "instruction_prompt":"df -h", "risk_level":"low"},
      {"order":4, "instruction_prompt":"free -h", "risk_level":"low"},
      {"order":5, "instruction_prompt":"who", "risk_level":"low"}
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

### 실습 2: RL 학습 체험

```bash
# 현재 정책 확인
curl -s http://localhost:8000/rl/policy \
  -H "X-API-Key: opsclaw-api-key-2026" | python3 -m json.tool

# 학습 실행
curl -s -X POST http://localhost:8000/rl/train \
  -H "X-API-Key: opsclaw-api-key-2026" | python3 -m json.tool

# 학습 후 추천 확인
for level in low medium high critical; do
  echo "=== $level ==="
  curl -s "http://localhost:8000/rl/recommend?agent_id=http://localhost:8002&risk_level=$level" \
    -H "X-API-Key: opsclaw-api-key-2026" | python3 -m json.tool
done
```

### 실습 3: LLM으로 Playbook 설계

```bash
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "OpsClaw 보안 자동화 전문가입니다. 보안 점검 Playbook을 JSON 형식으로 설계합니다."},
      {"role": "user", "content": "Linux 서버의 보안 하드닝 상태를 점검하는 Playbook을 설계하세요.\n점검 항목: SSH 설정, 패스워드 정책, 방화벽 상태, 불필요 서비스, 파일 권한\n\nJSON 형식: {\"name\": \"\", \"steps\": [{\"order\": N, \"tool\": \"run_command\", \"params\": {\"command\": \"\"}, \"risk_level\": \"\", \"description\": \"\"}]}"}
    ],
    "temperature": 0.3
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

---

## 7. RL이 보안 자동화에 주는 가치

```
                 ┌──────────────┐
                 │  위험 판단    │
                 │  (Q-table)   │
                 └──────┬───────┘
                        │
    태스크 요청 ─────────▶ RL 추천 ─────▶ 실행/거부
                        │
                  과거 데이터 기반
                  자동 의사결정
```

- **반복적 작업**: 과거 성공/실패 데이터로 최적 전략 학습
- **위험 관리**: risk_level별 행동 정책 자동 조정
- **에이전트 평가**: SubAgent별 신뢰도 축적

---

## 핵심 정리

1. Playbook은 반복 가능한 보안 작업을 표준화한 절차이다
2. execute-plan의 tasks가 Playbook의 steps에 대응한다
3. PoW 블록과 보상이 자동 생성되어 RL 학습 데이터가 된다
4. Q-learning으로 에이전트별, 위험수준별 최적 행동을 추천한다
5. LLM으로 Playbook을 설계하고, RL로 실행 정책을 최적화한다

---

## 다음 주 예고
- Week 11: 자율 미션 - /a2a/mission Red/Blue Team
