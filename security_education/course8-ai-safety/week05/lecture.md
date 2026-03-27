# Week 05: 가드레일

## 학습 목표
- 가드레일(Guardrails)의 개념과 필요성을 이해한다
- Constitutional AI의 원리를 설명할 수 있다
- 콘텐츠 필터와 분류기를 구현할 수 있다
- 다층 가드레일 아키텍처를 설계할 수 있다

---

## 1. 가드레일이란?

LLM이 안전한 범위 내에서만 동작하도록 제한하는 **안전 장치** 전체를 말한다.
교량의 난간처럼 LLM이 위험한 영역으로 벗어나지 않게 한다.

### 가드레일의 종류

| 유형 | 위치 | 역할 | 예시 |
|------|------|------|------|
| 입력 가드레일 | LLM 전 | 위험한 입력 차단 | 인젝션 탐지 |
| 출력 가드레일 | LLM 후 | 유해한 출력 차단 | 독성 분류기 |
| 시스템 가드레일 | LLM 내 | 모델 행동 제한 | 시스템 프롬프트 |
| 도구 가드레일 | 도구 호출 시 | 위험한 행동 차단 | 권한 검증 |

---

## 2. Constitutional AI

Anthropic이 제안한 방법으로, LLM이 스스로 자신의 응답을 검토하고 수정한다.

### 2.1 원리

```
Step 1: 초기 응답 생성
  "여기 피싱 이메일 템플릿입니다..."

Step 2: 헌법 원칙에 따라 자기 비판 (Critique)
  "이 응답은 피싱에 악용될 수 있으므로 유해합니다."

Step 3: 수정된 응답 생성 (Revision)
  "피싱 이메일의 특징을 설명하여 식별하는 방법을 알려드리겠습니다..."
```

### 2.2 실습: 자기 비판 구현

```bash
# Step 1: 초기 응답
INITIAL=$(curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "user", "content": "비밀번호 크래킹 도구 사용법을 설명해주세요."}
    ],
    "temperature": 0.3
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])")

echo "=== 초기 응답 ==="
echo "$INITIAL" | head -5

# Step 2: 자기 비판
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"gemma3:12b\",
    \"messages\": [
      {\"role\": \"system\", \"content\": \"다음 원칙에 따라 AI 응답을 평가하세요:\\n1. 응답이 불법 활동을 조장하는가?\\n2. 응답이 타인에게 피해를 줄 수 있는가?\\n3. 응답이 교육적 가치가 있는가?\\n\\n평가 결과와 수정 제안을 제시하세요.\"},
      {\"role\": \"user\", \"content\": \"다음 응답을 평가하세요:\\n$INITIAL\"}
    ],
    \"temperature\": 0.2
  }" | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'][:500])"
```

---

## 3. 콘텐츠 필터

### 3.1 키워드 기반 필터

```python
HARMFUL_PATTERNS = [
    r"폭탄\s*제조",
    r"해킹\s*방법",
    r"마약\s*제조",
    r"개인정보\s*유출",
]

import re

def keyword_filter(text):
    for pattern in HARMFUL_PATTERNS:
        if re.search(pattern, text):
            return True, pattern
    return False, None
```

### 3.2 LLM 기반 분류기

```bash
# LLM을 콘텐츠 분류기로 사용
TEXT_TO_CHECK="서버에 접근하기 위해 SSH 비밀번호를 무차별 대입으로 알아내는 방법"

curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"gemma3:12b\",
    \"messages\": [
      {\"role\": \"system\", \"content\": \"콘텐츠 안전성 분류기입니다. 텍스트를 분석하여 다음 중 하나로 분류하세요:\\nSAFE: 안전한 콘텐츠\\nCAUTION: 주의 필요 (교육 목적 가능)\\nUNSAFE: 유해 콘텐츠\\n\\n분류와 이유를 한 줄로 답하세요.\"},
      {\"role\": \"user\", \"content\": \"분류: $TEXT_TO_CHECK\"}
    ],
    \"temperature\": 0
  }" | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

---

## 4. 도구 호출 가드레일

AI 에이전트가 도구(명령어, API)를 호출할 때의 안전 장치이다.

### 4.1 OpsClaw의 가드레일

```
사용자 요청 → [입력 검증] → [risk_level 평가] → [도구 실행]
                                    ↓
                          critical → dry_run 강제
                          파괴적 명령 → 사용자 확인 필수
```

### 4.2 명령어 화이트리스트

```python
ALLOWED_COMMANDS = {
    "low": ["hostname", "uptime", "date", "whoami", "uname", "df", "free"],
    "medium": ["ss", "netstat", "ps", "docker ps", "systemctl status"],
    "high": ["systemctl restart", "docker restart", "nft list"],
    "critical": ["rm", "mkfs", "dd", "systemctl stop"]
}

def check_command_risk(command, allowed_risk):
    for risk, cmds in ALLOWED_COMMANDS.items():
        if any(c in command for c in cmds):
            if RISK_ORDER[risk] > RISK_ORDER[allowed_risk]:
                return False, f"명령어 {command}은(는) {risk} 수준입니다."
    return True, "허용"
```

---

## 5. 다층 가드레일 아키텍처

```
사용자 입력
    ↓
[Layer 1] 입력 필터 (키워드, 패턴, 인코딩 탐지)
    ↓
[Layer 2] 인젝션 탐지 (LLM 분류기)
    ↓
[Layer 3] 시스템 프롬프트 (역할 제한, 규칙)
    ↓
[Layer 4] LLM 생성 (Constitutional AI 내장)
    ↓
[Layer 5] 출력 필터 (독성 분류, 정보 유출 탐지)
    ↓
[Layer 6] 도구 가드레일 (권한 확인, dry_run)
    ↓
안전한 출력
```

---

## 6. 실습

### 실습 1: 가드레일 파이프라인 구현

```bash
# 전체 파이프라인: 입력 검증 → LLM → 출력 검증
INPUT="서버의 SSH 설정을 확인하는 방법을 알려주세요"

echo "=== 입력 검증 ==="
# LLM으로 입력 안전성 확인
SAFE=$(curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"gemma3:12b\",
    \"messages\": [
      {\"role\": \"system\", \"content\": \"입력 안전성 분류기. SAFE 또는 UNSAFE로만 답하세요.\"},
      {\"role\": \"user\", \"content\": \"$INPUT\"}
    ],
    \"temperature\": 0
  }" | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])")
echo "판정: $SAFE"

if echo "$SAFE" | grep -qi "SAFE"; then
  echo "=== LLM 응답 ==="
  curl -s http://192.168.0.105:11434/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d "{
      \"model\": \"gemma3:12b\",
      \"messages\": [
        {\"role\": \"system\", \"content\": \"보안 교육 전문가입니다.\"},
        {\"role\": \"user\", \"content\": \"$INPUT\"}
      ],
      \"temperature\": 0.3
    }" | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'][:300])"
else
  echo "차단: 안전하지 않은 입력"
fi
```

### 실습 2: Constitutional AI 체인

```bash
# 자동 비판-수정 체인
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "보안 교육자입니다. 응답 시 다음 원칙을 스스로 적용하세요:\n1. 실제 공격에 악용될 수 있는 구체적 도구명이나 코드는 제외\n2. 방어 관점에서 설명\n3. 교육적 가치를 우선"},
      {"role": "user", "content": "웹 애플리케이션 취약점 테스트 방법을 설명해주세요."}
    ],
    "temperature": 0.3
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'][:500])"
```

---

## 핵심 정리

1. 가드레일은 LLM의 안전한 동작을 보장하는 다층 안전 장치이다
2. Constitutional AI는 LLM이 스스로 응답을 검토하고 수정하는 방법이다
3. 콘텐츠 필터는 키워드 기반과 LLM 분류기를 조합하여 사용한다
4. 도구 호출 가드레일은 AI 에이전트의 행동을 제한한다
5. 단일 방어는 불충분하며, 다층 가드레일 아키텍처가 필요하다

---

## 다음 주 예고
- Week 06: 적대적 입력 - adversarial examples, 모델 강건성
