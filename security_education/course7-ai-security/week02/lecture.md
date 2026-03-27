# Week 02: LLM 기초 + Ollama

## 학습 목표
- 대규모 언어 모델(LLM)의 기본 원리를 이해한다
- Ollama를 사용하여 로컬 LLM을 실행할 수 있다
- 프롬프트, temperature 등 주요 파라미터를 조절할 수 있다
- API를 통해 LLM을 프로그래밍 방식으로 활용할 수 있다

---

## 1. LLM이란?

Large Language Model(대규모 언어 모델)은 방대한 텍스트 데이터로 학습된 AI 모델이다.
텍스트를 입력받아 다음에 올 가능성이 높은 텍스트를 생성한다.

### 핵심 개념

| 용어 | 설명 | 예시 |
|------|------|------|
| **토큰** | 텍스트의 최소 단위 | "안녕하세요" → 여러 토큰 |
| **파라미터** | 모델의 학습된 가중치 수 | 7B, 12B, 70B |
| **컨텍스트 윈도우** | 한 번에 처리할 수 있는 토큰 수 | 4K, 8K, 128K |
| **추론(Inference)** | 학습된 모델로 답변 생성 | 질문 → 답변 |

### 주요 오픈소스 LLM

| 모델 | 제작사 | 크기 | 특징 |
|------|--------|------|------|
| Llama 3.1 | Meta | 8B/70B/405B | 범용, 고성능 |
| Gemma 3 | Google | 4B/12B/27B | 효율적, 다국어 |
| Mistral | Mistral AI | 7B/8x7B | 유럽 기반, 빠름 |
| Qwen 2.5 | Alibaba | 7B/14B/72B | 다국어, 코딩 |

---

## 2. Ollama 소개

Ollama는 로컬에서 LLM을 쉽게 실행하는 도구이다.
Docker처럼 모델을 pull하고 run하는 방식이다.

### 2.1 기본 사용법

```bash
# 모델 다운로드
ollama pull gemma3:12b

# 대화형 실행
ollama run gemma3:12b

# 실행 중인 모델 확인
ollama list

# 모델 정보 확인
ollama show gemma3:12b
```

### 2.2 실습 환경

우리 실습에서는 dgx-spark 서버(192.168.0.105)의 GPU에서 Ollama가 실행된다.

```
dgx-spark (192.168.0.105)
├── GPU: NVIDIA DGX Spark
├── Ollama 서버: http://192.168.0.105:11434
├── 모델: gemma3:12b, llama3.1:8b
└── OpenAI 호환 API: /v1/chat/completions
```

---

## 3. Ollama API 사용

### 3.1 기본 대화 (Chat Completion)

```bash
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "당신은 친절한 보안 전문가입니다."},
      {"role": "user", "content": "방화벽이란 무엇인가요?"}
    ]
  }' | python3 -m json.tool
```

### 3.2 메시지 역할

| 역할 | 설명 | 예시 |
|------|------|------|
| **system** | AI의 행동 지침 | "보안 전문가로서 답변하세요" |
| **user** | 사용자 질문 | "SQL 인젝션을 설명해주세요" |
| **assistant** | AI의 이전 답변 | 대화 이력 유지용 |

### 3.3 주요 파라미터

```bash
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "user", "content": "리눅스 보안 팁 3가지"}
    ],
    "temperature": 0.3,
    "max_tokens": 500,
    "top_p": 0.9
  }' | python3 -m json.tool
```

| 파라미터 | 범위 | 효과 |
|---------|------|------|
| **temperature** | 0.0~2.0 | 낮으면 정확, 높으면 창의적 |
| **max_tokens** | 1~N | 최대 출력 토큰 수 |
| **top_p** | 0.0~1.0 | 상위 확률 토큰만 샘플링 |

### 3.4 Temperature 비교 실험

```bash
# temperature=0 (결정론적, 항상 같은 답)
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [{"role": "user", "content": "1+1=?"}],
    "temperature": 0
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"

# temperature=1.5 (매우 창의적, 매번 다른 답)
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [{"role": "user", "content": "보안을 한 마디로 표현하면?"}],
    "temperature": 1.5
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

---

## 4. Python에서 LLM 활용

### 4.1 requests로 직접 호출

```python
import requests
import json

def ask_llm(question, model="gemma3:12b", temperature=0.7):
    response = requests.post(
        "http://192.168.0.105:11434/v1/chat/completions",
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": "보안 전문가로서 답변하세요."},
                {"role": "user", "content": question}
            ],
            "temperature": temperature
        }
    )
    return response.json()["choices"][0]["message"]["content"]

# 사용
answer = ask_llm("SSH 보안 강화 방법을 알려주세요")
print(answer)
```

### 4.2 openai 라이브러리 사용 (호환 API)

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://192.168.0.105:11434/v1",
    api_key="unused"  # Ollama는 키 불필요
)

response = client.chat.completions.create(
    model="gemma3:12b",
    messages=[
        {"role": "system", "content": "보안 전문가입니다."},
        {"role": "user", "content": "XSS 공격이란?"}
    ],
    temperature=0.3
)

print(response.choices[0].message.content)
```

---

## 5. 실습

### 실습 1: 첫 LLM 대화

```bash
# 기본 질문
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "user", "content": "사이버보안 초보자에게 가장 중요한 3가지 습관은 무엇인가요?"}
    ],
    "temperature": 0.5
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

### 실습 2: System 프롬프트 실험

```bash
# 같은 질문, 다른 system 프롬프트
for role in "대학생" "10년차 해커" "CISO"; do
  echo "=== $role 관점 ==="
  curl -s http://192.168.0.105:11434/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d "{
      \"model\": \"gemma3:12b\",
      \"messages\": [
        {\"role\": \"system\", \"content\": \"당신은 ${role}입니다.\"},
        {\"role\": \"user\", \"content\": \"비밀번호 관리에 대해 한 문장으로 조언해주세요.\"}
      ],
      \"temperature\": 0.7,
      \"max_tokens\": 100
    }" | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
  echo ""
done
```

### 실습 3: 모델 비교

```bash
# gemma3:12b vs llama3.1:8b
for model in "gemma3:12b" "llama3.1:8b"; do
  echo "=== $model ==="
  curl -s http://192.168.0.105:11434/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d "{
      \"model\": \"$model\",
      \"messages\": [
        {\"role\": \"user\", \"content\": \"리눅스에서 열린 포트를 확인하는 명령어는?\"}
      ],
      \"temperature\": 0
    }" | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
  echo ""
done
```

---

## 6. LLM 사용 시 주의사항

1. **환각(Hallucination)**: LLM은 사실이 아닌 내용을 자신 있게 말할 수 있다
2. **보안 정보**: LLM의 보안 조언을 무조건 신뢰하지 말고 검증하라
3. **민감 데이터**: 외부 API에 비밀번호나 내부 정보를 보내지 말라
4. **최신 정보**: LLM의 학습 데이터에는 시간 제한이 있다

---

## 핵심 정리

1. LLM은 텍스트를 이해하고 생성하는 AI 모델이다
2. Ollama로 로컬 환경에서 안전하게 LLM을 실행할 수 있다
3. system/user/assistant 역할로 대화를 구성한다
4. temperature로 답변의 정확성/창의성을 조절한다
5. API를 통해 프로그래밍 방식으로 LLM을 활용한다

---

## 다음 주 예고
- Week 03: 프롬프트 엔지니어링 for 보안 - 로그 분석, 취약점 설명 프롬프트
