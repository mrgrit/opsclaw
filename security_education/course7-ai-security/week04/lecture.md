# Week 04: LLM 기반 로그 분석

## 학습 목표
- Wazuh SIEM 알림의 구조를 이해한다
- LLM을 활용하여 보안 로그를 자동 분석할 수 있다
- 분석 결과를 구조화된 인시던트 보고서로 변환할 수 있다
- 대량 알림에서 중요 이벤트를 우선순위로 분류할 수 있다

---

## 1. 보안 로그 분석의 과제

SOC(Security Operations Center)에서 분석가는 하루 수천~수만 건의 알림을 처리한다.
대부분은 오탐(False Positive)이지만, 소수의 진짜 위협을 놓치면 사고로 이어진다.

### LLM이 도울 수 있는 영역

| 작업 | 수동 분석 | LLM 보조 |
|------|----------|---------|
| 알림 분류 | 1건당 5분 | 1건당 10초 |
| 패턴 인식 | 분석가 경험 의존 | 다양한 패턴 인식 |
| 보고서 작성 | 30분~1시간 | 2~3분 |
| 맥락 파악 | 여러 도구 참조 | 프롬프트로 맥락 제공 |

---

## 2. Wazuh 알림 구조

### 2.1 알림 JSON 구조

```json
{
  "timestamp": "2026-03-27T10:30:00.000+0900",
  "rule": {
    "id": "5710",
    "level": 10,
    "description": "sshd: Attempt to login using a denied user.",
    "groups": ["syslog", "sshd", "authentication_failed"]
  },
  "agent": {
    "id": "002",
    "name": "web",
    "ip": "10.20.30.80"
  },
  "data": {
    "srcip": "203.0.113.50",
    "srcport": "54321",
    "dstuser": "root"
  },
  "full_log": "Mar 27 10:30:00 web sshd[1234]: Failed password for root from 203.0.113.50 port 54321 ssh2"
}
```

### 2.2 Wazuh Rule Level

| Level | 의미 | 예시 |
|-------|------|------|
| 0-3 | 정보 | 성공 로그인 |
| 4-7 | 경고 | 실패한 인증 |
| 8-11 | 높은 경고 | 반복 실패, 정책 위반 |
| 12-15 | 심각 | 공격 탐지, 무결성 위반 |

---

## 3. LLM으로 알림 분석

### 3.1 단일 알림 분석

```bash
ALERT='{
  "rule": {"id": "5710", "level": 10, "description": "sshd: Attempt to login using a denied user."},
  "agent": {"name": "web", "ip": "10.20.30.80"},
  "data": {"srcip": "203.0.113.50", "dstuser": "root"},
  "full_log": "Mar 27 10:30:00 web sshd[1234]: Failed password for root from 203.0.113.50 port 54321 ssh2"
}'

curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"gemma3:12b\",
    \"messages\": [
      {\"role\": \"system\", \"content\": \"SOC Tier-2 분석가입니다. Wazuh 알림을 분석하고 다음 형식으로 응답하세요:\\n- 요약: (한 줄)\\n- 위협수준: CRITICAL/HIGH/MEDIUM/LOW\\n- MITRE ATT&CK: (해당 기법)\\n- 대응: (즉시 수행할 조치)\"},
      {\"role\": \"user\", \"content\": \"다음 Wazuh 알림을 분석하세요:\\n$ALERT\"}
    ],
    \"temperature\": 0.2
  }" | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

### 3.2 복수 알림 상관 분석

```bash
ALERTS='[
  {"time": "10:30:00", "rule": "5710", "src": "203.0.113.50", "msg": "SSH 로그인 실패 (root)"},
  {"time": "10:30:05", "rule": "5710", "src": "203.0.113.50", "msg": "SSH 로그인 실패 (admin)"},
  {"time": "10:31:00", "rule": "5715", "src": "203.0.113.50", "msg": "SSH 브루트포스 탐지"},
  {"time": "10:35:00", "rule": "5501", "src": "203.0.113.50", "msg": "SSH 로그인 성공 (deploy)"},
  {"time": "10:36:00", "rule": "550",  "src": "10.20.30.80",  "msg": "사용자 추가: hacker"}
]'

curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"gemma3:12b\",
    \"messages\": [
      {\"role\": \"system\", \"content\": \"SOC 분석가입니다. 여러 알림을 시간순으로 상관 분석하여 공격 시나리오를 추론하세요.\"},
      {\"role\": \"user\", \"content\": \"다음 Wazuh 알림들을 상관 분석하세요. 공격 킬체인을 추론하세요:\\n$ALERTS\"}
    ],
    \"temperature\": 0.3
  }" | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

---

## 4. 알림 우선순위 분류

### 4.1 배치 분류 프롬프트

```bash
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "SOC 분석가입니다. 알림을 우선순위별로 분류하세요.\n분류: CRITICAL(즉시 대응), HIGH(1시간 내), MEDIUM(24시간 내), LOW(정기 검토)\n\nJSON 배열로 응답: [{\"id\": N, \"priority\": \"...\", \"reason\": \"...\"}]"},
      {"role": "user", "content": "분류할 알림 목록:\n1. SSH root 로그인 성공 (외부 IP)\n2. 파일 무결성 변경 (/etc/passwd)\n3. 디스크 사용량 90%\n4. nginx 404 에러 증가\n5. sudo 권한 실행 (웹 서버에서 wget)"}
    ],
    "temperature": 0
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

---

## 5. 자동화 스크립트

### 5.1 Python으로 Wazuh 알림 자동 분석

```python
#!/usr/bin/env python3
"""wazuh_llm_analyzer.py - Wazuh 알림을 LLM으로 분석"""
import requests
import json

OLLAMA_URL = "http://192.168.0.105:11434/v1/chat/completions"
MODEL = "gemma3:12b"

SYSTEM_PROMPT = """SOC Tier-2 분석가입니다. Wazuh 알림을 분석하고
정확히 다음 JSON 형식으로만 응답하세요:
{"severity": "CRITICAL|HIGH|MEDIUM|LOW", "summary": "한줄요약",
 "attack_type": "공격유형", "action": "대응조치"}"""

def analyze_alert(alert_json):
    response = requests.post(OLLAMA_URL, json={
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"알림: {json.dumps(alert_json, ensure_ascii=False)}"}
        ],
        "temperature": 0
    })
    return response.json()["choices"][0]["message"]["content"]

# 사용 예시
sample_alert = {
    "rule": {"id": "5710", "level": 10,
             "description": "sshd: Attempt to login using a denied user."},
    "agent": {"name": "web"},
    "data": {"srcip": "203.0.113.50", "dstuser": "root"}
}

result = analyze_alert(sample_alert)
print(result)
```

---

## 6. 실습

### 실습 1: 실제 Wazuh 알림 분석

```bash
# siem 서버에서 최근 알림 가져오기 (OpsClaw 활용)
curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "name": "wazuh-log-analysis",
    "request_text": "Wazuh 최근 알림 수집 및 분석",
    "master_mode": "external"
  }'

# 프로젝트 ID 확인 후 dispatch로 알림 수집
# curl -X POST http://localhost:8000/projects/{id}/dispatch ...
```

### 실습 2: 공격 시나리오별 프롬프트 설계

```bash
# 시나리오: 웹 서버에서 의심스러운 활동 탐지
SCENARIO="다음은 웹 서버(10.20.30.80)에서 30분간 수집된 로그입니다:
10:00 - 정상 웹 트래픽
10:05 - /admin 페이지 접근 시도 (403)
10:06 - SQL Injection 시도 (?id=1' OR '1'='1)
10:08 - /admin 접근 성공 (200)
10:10 - 파일 업로드 (webshell.php)
10:15 - webshell.php에서 시스템 명령 실행
10:20 - /etc/passwd 읽기 시도
10:25 - 리버스 셸 연결 시도"

curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"gemma3:12b\",
    \"messages\": [
      {\"role\": \"system\", \"content\": \"인시던트 대응 전문가입니다. 공격 킬체인을 분석하고 각 단계의 MITRE ATT&CK 기법을 매핑하세요.\"},
      {\"role\": \"user\", \"content\": \"$SCENARIO\"}
    ],
    \"temperature\": 0.3
  }" | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

### 실습 3: 분석 결과를 인시던트 보고서로 변환

```bash
# 이전 분석 결과를 CISO용 보고서로 변환
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "CISO에게 보고할 인시던트 보고서를 작성합니다. 비기술적 경영진도 이해할 수 있되, 기술 세부사항도 포함하세요."},
      {"role": "user", "content": "다음 분석 결과를 인시던트 보고서로 변환하세요:\n- 공격: SQL Injection → 웹셸 업로드 → 시스템 침입\n- 대상: web 서버 (10.20.30.80)\n- 공격자 IP: 203.0.113.50\n- 시간: 2026-03-27 10:00~10:25\n- 피해: 관리자 페이지 접근, 시스템 명령 실행 시도\n\n보고서 형식: 1.개요 2.타임라인 3.영향분석 4.대응현황 5.재발방지"}
    ],
    "temperature": 0.4
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

---

## 7. LLM 로그 분석의 한계

1. **환각**: 존재하지 않는 위협을 만들어낼 수 있다
2. **최신 위협**: 학습 데이터 이후의 새로운 공격 패턴을 모를 수 있다
3. **정밀도**: 자동 분류의 정확도를 지속적으로 검증해야 한다
4. **민감 데이터**: 실제 IP, 비밀번호 등을 외부 LLM에 전송하면 안 된다

해결 방법: 로컬 LLM(Ollama) 사용 + 사람 검증 + 지속적 피드백

---

## 핵심 정리

1. LLM은 대량의 보안 알림을 빠르게 분류하고 분석하는 도구이다
2. 시간순 상관 분석으로 공격 킬체인을 추론할 수 있다
3. 구조화된 프롬프트로 일관된 분석 결과를 얻는다
4. 자동화 스크립트로 Wazuh 알림을 실시간 분석할 수 있다
5. LLM 분석 결과는 반드시 사람이 검증해야 한다

---

## 다음 주 예고
- Week 05: 탐지 룰 자동 생성 - 공격 패턴에서 SIGMA/Wazuh 룰 자동 생성
