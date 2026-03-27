# Week 11: 자율 미션

## 학습 목표
- 자율 미션(Autonomous Mission)의 개념을 이해한다
- Red Team / Blue Team 자율 에이전트의 동작 원리를 익힌다
- /a2a/mission API를 통한 자율 미션 실행을 실습한다
- Purple Team 자동화의 보안적 가치를 설명할 수 있다

---

## 1. 자율 미션이란?

자율 미션은 SubAgent가 **LLM의 추론 능력**을 활용하여 사람의 개입 없이 보안 작업을 수행하는 기능이다.

### 수동 실행 vs 자율 미션

| 항목 | 수동 (dispatch) | 자율 (mission) |
|------|---------------|---------------|
| 명령 | 사람이 직접 지정 | LLM이 스스로 결정 |
| 판단 | 사람이 결과 해석 | LLM이 결과 분석 후 다음 행동 결정 |
| 범위 | 단일 명령 | 목표 기반 다중 단계 |
| 자율성 | 없음 | 높음 |

---

## 2. Red Team vs Blue Team

### 2.1 역할 정의

| 팀 | 목표 | LLM 모델 | 성격 |
|----|------|---------|------|
| **Red Team** | 취약점 탐색, 공격 시뮬레이션 | gemma3:12b | 공격적, 탐색적 |
| **Blue Team** | 방어, 탐지, 대응 | llama3.1:8b | 방어적, 분석적 |

### 2.2 Purple Team

Red와 Blue를 동시에 운영하여 서로 상호작용하게 한다.

```
Red Team: 취약점 발견 → 공격 시도
    ↕ (정보 공유)
Blue Team: 공격 탐지 → 방어 강화
    ↕ (결과 피드백)
보안 수준 지속 향상
```

---

## 3. /a2a/mission API

### 3.1 미션 실행

```bash
# Red Team 미션: web 서버 취약점 탐색
curl -s -X POST "http://localhost:8000/projects/$PID/dispatch" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "command": "RED_MISSION: web 서버(10.20.30.80)의 열린 포트와 서비스를 탐색하고 보안 취약점을 식별하라",
    "subagent_url": "http://192.168.208.150:8002"
  }' | python3 -m json.tool
```

### 3.2 미션 구조

SubAgent가 /a2a/mission 요청을 받으면:

```
1. 미션 목표 파악 (LLM 추론)
2. 실행 계획 수립 (어떤 명령을 실행할지)
3. 명령 실행 (run_command 도구 호출)
4. 결과 분석 (LLM이 결과 해석)
5. 다음 행동 결정 (추가 탐색 또는 완료)
6. 보고서 생성
```

### 3.3 Red Team 미션 예시

```bash
# 포트 스캔 → 서비스 식별 → 취약점 탐색
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "Red Team 보안 전문가입니다. 주어진 대상의 보안 취약점을 체계적으로 탐색합니다. 교육/테스트 환경에서만 수행합니다."},
      {"role": "user", "content": "대상: web 서버 (10.20.30.80)\n\n다음 순서로 탐색 계획을 수립하세요:\n1. 포트 스캔 명령어\n2. 서비스 버전 확인 명령어\n3. 발견된 서비스별 취약점 확인 방법\n\n각 단계의 실행 명령어를 제시하세요."}
    ],
    "temperature": 0.3
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

### 3.4 Blue Team 미션 예시

```bash
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1:8b",
    "messages": [
      {"role": "system", "content": "Blue Team 방어 전문가입니다. 시스템의 보안 상태를 점검하고 강화 방안을 제시합니다."},
      {"role": "user", "content": "web 서버(10.20.30.80)에서 다음 Red Team 발견사항에 대한 방어 조치를 제시하세요:\n- SSH 포트(22) 외부 노출\n- 웹 서버 버전 헤더 노출\n- Docker 소켓 접근 가능\n\n각 취약점에 대한 구체적인 방어 명령어를 제시하세요."}
    ],
    "temperature": 0.3
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

---

## 4. Purple Team 자동화

### 4.1 Red → Blue 루프

```bash
# Step 1: Red Team이 취약점 발견
RED_FINDING="SSH 포트(22)가 0.0.0.0에 바인딩되어 외부에서 접근 가능"

# Step 2: Blue Team이 방어 조치 생성
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"llama3.1:8b\",
    \"messages\": [
      {\"role\": \"system\", \"content\": \"Blue Team입니다. Red Team 발견사항에 대한 방어 조치를 생성합니다.\"},
      {\"role\": \"user\", \"content\": \"Red Team 발견: $RED_FINDING\\n\\n즉시 실행 가능한 방어 조치 명령어를 제시하세요.\"}
    ],
    \"temperature\": 0.3
  }" | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"

# Step 3: OpsClaw로 방어 조치 실행 (승인 후)
```

### 4.2 자동화 스크립트

```python
#!/usr/bin/env python3
"""purple_team_auto.py - 자율 Purple Team 시뮬레이션"""
import requests

OLLAMA = "http://192.168.0.105:11434/v1/chat/completions"
OPSCLAW = "http://localhost:8000"
API_KEY = "opsclaw-api-key-2026"
HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

def red_team_scan(target):
    """Red Team: 취약점 탐색"""
    resp = requests.post(OLLAMA, json={
        "model": "gemma3:12b",
        "messages": [
            {"role": "system", "content": "Red Team 전문가. 취약점을 JSON 리스트로 보고."},
            {"role": "user", "content": f"대상 {target}의 일반적인 Linux 서버 취약점 3가지를 식별하세요."}
        ],
        "temperature": 0.3
    })
    return resp.json()["choices"][0]["message"]["content"]

def blue_team_defend(findings):
    """Blue Team: 방어 조치 생성"""
    resp = requests.post(OLLAMA, json={
        "model": "llama3.1:8b",
        "messages": [
            {"role": "system", "content": "Blue Team 전문가. 각 취약점에 대한 방어 명령어를 제시."},
            {"role": "user", "content": f"다음 취약점에 대한 방어 조치:\n{findings}"}
        ],
        "temperature": 0.3
    })
    return resp.json()["choices"][0]["message"]["content"]

# 실행
findings = red_team_scan("10.20.30.80")
print("=== Red Team 발견 ===")
print(findings)
print("\n=== Blue Team 방어 ===")
print(blue_team_defend(findings))
```

---

## 5. 실습

### 실습 1: Red Team 미션 실행

```bash
# 프로젝트 생성 및 준비
PID=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"name":"purple-team-lab","request_text":"Purple Team 실습","master_mode":"external"}' \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")

curl -s -X POST "http://localhost:8000/projects/$PID/plan" -H "X-API-Key: opsclaw-api-key-2026" > /dev/null
curl -s -X POST "http://localhost:8000/projects/$PID/execute" -H "X-API-Key: opsclaw-api-key-2026" > /dev/null

# Red Team: 정보 수집
curl -s -X POST "http://localhost:8000/projects/$PID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "tasks": [
      {"order":1, "instruction_prompt":"ss -tlnp", "risk_level":"low"},
      {"order":2, "instruction_prompt":"curl -sI http://10.20.30.80 | head -10", "risk_level":"low"},
      {"order":3, "instruction_prompt":"cat /etc/passwd | grep -v nologin | grep -v false", "risk_level":"low"}
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

### 실습 2: Red 결과를 LLM으로 분석

```bash
# 수집된 정보를 LLM에 전달하여 취약점 식별
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "Red Team 분석가입니다. 수집된 정보에서 보안 취약점을 식별합니다."},
      {"role": "user", "content": "다음은 대상 서버에서 수집한 정보입니다:\n\n1. 열린 포트: 22(SSH), 80(HTTP), 8000(API), 8002(SubAgent)\n2. HTTP 헤더: Server: nginx/1.24.0\n3. 셸 접근 가능 사용자: root, opsclaw, student\n\n보안 취약점과 공격 가능 경로를 분석하세요."}
    ],
    "temperature": 0.3
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

---

## 6. 안전 고려사항

자율 미션은 강력하지만 위험할 수 있다.

| 위험 | 방어 |
|------|------|
| 과도한 스캔 | rate limiting, 대상 화이트리스트 |
| 파괴적 명령 실행 | risk_level + dry_run |
| 정보 유출 | 미션 결과 접근 제어 |
| 무한 루프 | 최대 단계 수 제한 |

### 안전 규칙

1. 자율 미션은 **테스트 환경에서만** 실행한다
2. critical risk 명령은 **사용자 확인 필수**이다
3. 모든 미션 결과는 **PoW 체인에 기록**된다
4. **프로덕션 환경**에서는 읽기 전용 미션만 허용한다

---

## 핵심 정리

1. 자율 미션은 LLM이 스스로 판단하고 행동하는 보안 작업이다
2. Red Team은 공격 시뮬레이션, Blue Team은 방어 강화를 수행한다
3. Purple Team은 Red/Blue를 결합하여 보안 수준을 지속 향상시킨다
4. 안전 장치(risk_level, dry_run, PoW)로 자율 미션의 위험을 관리한다
5. 자율 미션은 보조 도구이며, 최종 판단은 사람이 내린다

---

## 다음 주 예고
- Week 12: Agent Daemon - explore + daemon + stimulate
