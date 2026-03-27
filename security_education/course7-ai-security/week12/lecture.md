# Week 12: Agent Daemon

## 학습 목표
- Agent Daemon의 3가지 모드(explore, daemon, stimulate)를 이해한다
- 자율 보안 관제의 개념과 동작 원리를 설명할 수 있다
- Daemon 모드의 지속적 모니터링 기능을 실습한다
- Stimulate 모드로 능동적 보안 테스트를 수행할 수 있다

---

## 1. Agent Daemon이란?

Agent Daemon은 SubAgent가 **백그라운드에서 지속적으로** 보안 관제를 수행하는 기능이다.
단발성 명령 실행을 넘어 자율적인 보안 모니터링을 가능하게 한다.

### 3가지 모드

| 모드 | 목적 | 동작 |
|------|------|------|
| **explore** | 환경 탐색 | 시스템 상태 파악, 자산 목록 작성 |
| **daemon** | 지속 감시 | 주기적 점검, 이상 탐지 |
| **stimulate** | 능동 테스트 | 보안 이벤트 생성, 탐지 능력 검증 |

---

## 2. Explore 모드

시스템 환경을 자동으로 탐색하여 보안 기준선(baseline)을 수립한다.

### 2.1 Explore 실행

```bash
# LLM이 환경을 파악하기 위한 탐색 수행
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "보안 관제 에이전트입니다. 시스템 환경을 탐색하여 보안 기준선을 수립합니다. 실행해야 할 명령어 목록을 제시하세요."},
      {"role": "user", "content": "Linux 서버의 보안 기준선을 수립하기 위해 수집해야 할 정보를 나열하세요. 각 항목에 대한 명령어를 포함하세요.\n\n범주: 시스템정보, 네트워크, 사용자, 서비스, 파일시스템"}
    ],
    "temperature": 0.3
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

### 2.2 OpsClaw로 Explore 실행

```bash
PID="프로젝트_ID"

curl -s -X POST "http://localhost:8000/projects/$PID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "tasks": [
      {"order":1, "instruction_prompt":"uname -a && cat /etc/os-release | head -5", "risk_level":"low"},
      {"order":2, "instruction_prompt":"ss -tlnp", "risk_level":"low"},
      {"order":3, "instruction_prompt":"cat /etc/passwd | wc -l && who", "risk_level":"low"},
      {"order":4, "instruction_prompt":"systemctl list-units --type=service --state=running | head -20", "risk_level":"low"},
      {"order":5, "instruction_prompt":"df -h && mount | grep -v cgroup | head -10", "risk_level":"low"}
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

---

## 3. Daemon 모드

주기적으로 보안 상태를 점검하고 이상을 탐지한다.

### 3.1 Daemon 점검 항목

```
매 5분마다:
├── 열린 포트 변화 확인
├── 로그인 사용자 변화 확인
├── 프로세스 이상 확인
└── 로그 이상 패턴 확인

매 1시간마다:
├── 파일 무결성 확인
├── 디스크 사용량 확인
├── 보안 업데이트 확인
└── 설정 파일 변경 확인
```

### 3.2 Daemon 루프 개념

```python
"""daemon_loop.py - 개념 코드 (실제 OpsClaw Daemon은 내부 구현)"""
import time
import requests

OPSCLAW = "http://localhost:8000"
API_KEY = "opsclaw-api-key-2026"
HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

def check_ports(pid):
    """열린 포트 변화 감지"""
    return requests.post(
        f"{OPSCLAW}/projects/{pid}/dispatch",
        headers=HEADERS,
        json={"command": "ss -tlnp", "subagent_url": "http://localhost:8002"}
    ).json()

def check_users(pid):
    """로그인 사용자 변화 감지"""
    return requests.post(
        f"{OPSCLAW}/projects/{pid}/dispatch",
        headers=HEADERS,
        json={"command": "who", "subagent_url": "http://localhost:8002"}
    ).json()

def analyze_with_llm(data):
    """LLM으로 이상 탐지"""
    resp = requests.post(
        "http://192.168.0.105:11434/v1/chat/completions",
        json={
            "model": "gemma3:12b",
            "messages": [
                {"role": "system", "content": "보안 관제 에이전트. 이상을 탐지하면 ALERT, 정상이면 OK를 응답."},
                {"role": "user", "content": f"점검 결과:\n{data}\n\n이상 여부를 판단하세요."}
            ],
            "temperature": 0
        }
    )
    return resp.json()["choices"][0]["message"]["content"]
```

### 3.3 변화 탐지 원리

```
이전 상태 (baseline)    현재 상태          비교 결과
열린 포트: 22,80        열린 포트: 22,80,4444   새 포트 4444 발견!
사용자: opsclaw         사용자: opsclaw,hacker  새 사용자 hacker!
/etc/passwd hash: a1b2  /etc/passwd hash: c3d4  파일 변조 감지!
```

---

## 4. Stimulate 모드

보안 탐지 시스템이 제대로 작동하는지 **의도적으로 보안 이벤트를 생성**하여 검증한다.

### 4.1 Stimulate 시나리오

| 시나리오 | 생성 이벤트 | 예상 탐지 |
|---------|-----------|----------|
| SSH 브루트포스 | 잘못된 비밀번호로 반복 시도 | Wazuh rule 5710 |
| 파일 변조 | 테스트 파일 수정 | Wazuh FIM 알림 |
| 포트 스캔 | nmap 스캔 | Suricata alert |
| 웹 공격 | SQL Injection 시도 | WAF 차단 |

### 4.2 Stimulate 실행 예시

```bash
# 안전한 stimulation: 존재하지 않는 사용자로 SSH 시도
curl -s -X POST "http://localhost:8000/projects/$PID/dispatch" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "command": "ssh -o BatchMode=yes -o ConnectTimeout=3 testuser@localhost echo test 2>&1 || true",
    "subagent_url": "http://localhost:8002"
  }'

# 이후 Wazuh에서 알림이 발생하는지 확인
```

### 4.3 LLM으로 Stimulate 계획 수립

```bash
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "보안 테스트 전문가입니다. SIEM 탐지 능력을 검증하기 위한 안전한 테스트 시나리오를 설계합니다. 실제 피해를 주지 않는 안전한 방법만 사용합니다."},
      {"role": "user", "content": "Wazuh SIEM의 탐지 능력을 검증하기 위한 안전한 stimulation 시나리오 5가지를 설계하세요.\n\n각 시나리오에:\n1. 생성할 이벤트\n2. 실행 명령어\n3. 예상 탐지 룰\n4. 확인 방법\n을 포함하세요."}
    ],
    "temperature": 0.4
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

---

## 5. 실습

### 실습 1: Explore 실행

```bash
# 프로젝트 생성
PID=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"name":"daemon-lab","request_text":"Agent Daemon 실습","master_mode":"external"}' \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")

curl -s -X POST "http://localhost:8000/projects/$PID/plan" -H "X-API-Key: opsclaw-api-key-2026" > /dev/null
curl -s -X POST "http://localhost:8000/projects/$PID/execute" -H "X-API-Key: opsclaw-api-key-2026" > /dev/null

# Explore: 기준선 수집
curl -s -X POST "http://localhost:8000/projects/$PID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "tasks": [
      {"order":1, "instruction_prompt":"ss -tlnp | grep LISTEN", "risk_level":"low"},
      {"order":2, "instruction_prompt":"who 2>/dev/null; last -5", "risk_level":"low"},
      {"order":3, "instruction_prompt":"ps aux --sort=-%mem | head -10", "risk_level":"low"}
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

### 실습 2: Daemon 점검 시뮬레이션

```bash
# 30초 간격으로 2번 점검하여 변화 비교
for i in 1 2; do
  echo "=== 점검 $i ==="
  curl -s -X POST "http://localhost:8000/projects/$PID/dispatch" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: opsclaw-api-key-2026" \
    -d '{"command":"ss -tlnp | grep LISTEN | md5sum","subagent_url":"http://localhost:8002"}' \
    | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('result','')[:100])"
  sleep 5
done
```

### 실습 3: Stimulate + 탐지 확인

```bash
# SSH 인증 실패 이벤트 생성
curl -s -X POST "http://localhost:8000/projects/$PID/dispatch" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "command": "for i in 1 2 3; do ssh -o BatchMode=yes -o ConnectTimeout=1 -o StrictHostKeyChecking=no fakeuser@localhost 2>&1; done || true",
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool

# 결과를 LLM으로 분석
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "user", "content": "SSH 인증 실패 이벤트를 3회 생성했습니다. Wazuh SIEM에서 이를 탐지했다면 어떤 룰이 발동되었을까요? 예상 룰 ID와 설명을 알려주세요."}
    ],
    "temperature": 0.3
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

---

## 6. Daemon의 보안적 가치

```
전통적 보안 관제                 Agent Daemon
──────────────                  ────────────
사람이 대시보드 모니터링          LLM이 자동 분석
정해진 룰로만 탐지               패턴 추론 가능
느린 대응 (시간~일)              빠른 대응 (분)
피로도 누적                     24/7 일관된 관제
```

---

## 핵심 정리

1. Explore는 시스템 환경을 탐색하여 보안 기준선을 수립한다
2. Daemon은 주기적으로 상태를 점검하여 변화와 이상을 탐지한다
3. Stimulate는 보안 이벤트를 생성하여 탐지 시스템을 검증한다
4. 세 모드를 조합하면 자율 보안 관제 사이클이 완성된다
5. LLM이 결과를 분석하므로 미리 정의되지 않은 이상도 탐지 가능하다

---

## 다음 주 예고
- Week 13: 분산 지식 - local_knowledge, knowledge transfer
