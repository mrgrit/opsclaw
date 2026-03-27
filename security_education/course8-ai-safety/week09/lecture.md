# Week 09: 모델 보안

## 학습 목표
- 모델 추출(Model Extraction) 공격을 이해한다
- 멤버십 추론(Membership Inference) 공격을 파악한다
- 모델 워터마킹 기법과 용도를 익힌다
- 모델 자산 보호 전략을 설계할 수 있다

---

## 1. AI 모델의 가치와 위협

AI 모델은 학습 데이터, 컴퓨팅 리소스, 전문 지식이 결합된 **고가치 지적 재산**이다.

| 위협 | 공격자 목표 | 영향 |
|------|-----------|------|
| 모델 추출 | 모델 복제 | IP 도난, 경쟁 우위 상실 |
| 멤버십 추론 | 학습 데이터 유추 | 개인정보 유출 |
| 모델 역전 | 학습 데이터 복원 | 민감 데이터 노출 |
| 모델 도용 | 무단 사용 | 비용 전가, 오용 |

---

## 2. 모델 추출 (Model Extraction)

### 2.1 개념

API로 제공되는 모델에 대량 쿼리를 보내 모델의 행동을 복제한다.

```
공격자 → 수천~수만 건 쿼리 → 대상 모델 API
                                    ↓
                              입력-출력 쌍 수집
                                    ↓
                              복제 모델 학습 (지식 증류)
```

### 2.2 공격 방법

```python
# 대상 모델에 체계적으로 쿼리
import requests

queries = [
    "보안이란 무엇인가?",
    "방화벽의 종류를 설명하라",
    # ... 수천 개의 체계적 질문
]

training_data = []
for q in queries:
    response = requests.post(TARGET_API, json={"prompt": q})
    training_data.append({
        "input": q,
        "output": response.json()["text"]
    })

# 수집된 데이터로 복제 모델 학습
# model.train(training_data)
```

### 2.3 방어

| 방어 | 방법 |
|------|------|
| Rate Limiting | 시간당 쿼리 수 제한 |
| 쿼리 패턴 탐지 | 비정상적 쿼리 패턴 감지 |
| 출력 제한 | 확률값/로짓 비공개 |
| 워터마킹 | 출력에 추적 가능한 패턴 삽입 |

---

## 3. 멤버십 추론 (Membership Inference)

### 3.1 개념

특정 데이터가 모델의 학습에 사용되었는지 여부를 알아내는 공격이다.

```
질문: "이 개인정보가 GPT의 학습 데이터에 포함되어 있는가?"
답변: 모델의 응답 확신도로 추론 가능
```

### 3.2 원리

```
학습 데이터:   모델이 높은 확신도로 답변 (과적합)
비학습 데이터: 모델이 낮은 확신도로 답변

→ 확신도 차이로 학습 데이터 여부 추론
```

### 3.3 개인정보 위험

```
의료 데이터로 학습된 모델:
  "환자 홍길동의 진단 결과는?" → 높은 확신도로 답변
  → 홍길동의 의료 기록이 학습 데이터에 포함되었음을 추론
  → 개인 의료 정보 유출
```

### 3.4 실습: 멤버십 추론 개념

```bash
# 모델이 특정 정보를 "기억"하는지 확인
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "user", "content": "OpenAI의 CEO는 누구인가요?"}
    ],
    "temperature": 0
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'][:200])"

# 존재하지 않는 정보
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "user", "content": "2026년 3월에 설립된 한국 스타트업 SecureClaw의 CEO는 누구인가요?"}
    ],
    "temperature": 0
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'][:200])"

# 첫 번째는 확신 있게, 두 번째는 불확실하게 답변
# → 확신도 차이가 멤버십 추론의 단서
```

---

## 4. 모델 워터마킹

### 4.1 개념

모델의 출력에 추적 가능한 패턴을 삽입하여 소유권을 증명하거나 무단 사용을 탐지한다.

### 4.2 텍스트 워터마킹

```
방법 1: 특정 동의어 선호
  정상: "좋은" / "훌륭한" / "우수한" (랜덤 선택)
  워터마크: "훌륭한"을 70% 확률로 선택 (통계적으로 탐지 가능)

방법 2: 토큰 색상 분할
  토큰을 "빨강/초록" 그룹으로 분할
  워터마크된 모델은 "초록" 토큰을 더 자주 선택
  통계 테스트로 워터마크 존재 확인
```

### 4.3 워터마킹의 용도

| 용도 | 설명 |
|------|------|
| 소유권 증명 | 복제된 모델의 원본 확인 |
| AI 생성 탐지 | AI가 작성한 텍스트 식별 |
| 무단 사용 추적 | API 출력의 무단 재배포 탐지 |
| 규정 준수 | AI 생성 콘텐츠 표시 규정 |

---

## 5. 모델 보호 전략

### 5.1 API 수준 보호

```python
# Rate Limiting + 이상 탐지
from collections import defaultdict
import time

request_log = defaultdict(list)

def check_rate_limit(api_key, max_rpm=60):
    now = time.time()
    recent = [t for t in request_log[api_key] if now - t < 60]
    request_log[api_key] = recent

    if len(recent) >= max_rpm:
        return False  # 제한 초과

    # 이상 패턴 탐지: 체계적 쿼리
    if len(recent) > 30 and is_systematic(recent):
        alert("모델 추출 의심: " + api_key)
        return False

    request_log[api_key].append(now)
    return True
```

### 5.2 OpsClaw의 모델 보호

```bash
# OpsClaw API 인증 = 모델 보호의 기본
# 인증 없이는 API 접근 불가
curl -s http://localhost:8000/projects
# → 401 Unauthorized

# API 키로 접근 (인가된 사용자만)
curl -s -H "X-API-Key: opsclaw-api-key-2026" http://localhost:8000/projects
# → 200 OK
```

---

## 6. 실습

### 실습 1: LLM으로 모델 보안 위협 분석

```bash
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "AI 보안 전문가입니다."},
      {"role": "user", "content": "기업이 자체 파인튜닝한 LLM을 API로 서비스할 때 발생 가능한 보안 위협 5가지와 각각의 방어 방법을 설명해주세요."}
    ],
    "temperature": 0.4
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

### 실습 2: Rate Limiting 개념 체험

```bash
# 빠른 연속 요청으로 Rate Limiting 이해
for i in $(seq 1 5); do
  echo "요청 $i:"
  curl -s -o /dev/null -w "HTTP %{http_code}" \
    -H "X-API-Key: opsclaw-api-key-2026" \
    http://localhost:8000/projects
  echo ""
done
```

---

## 핵심 정리

1. 모델 추출은 API 쿼리로 모델을 복제하는 지적재산 도난이다
2. 멤버십 추론은 학습 데이터 포함 여부를 알아내어 개인정보를 유출한다
3. 워터마킹으로 모델 소유권을 증명하고 무단 사용을 추적한다
4. API Rate Limiting과 이상 탐지가 모델 보호의 기본이다
5. 모델은 고가치 자산이므로 접근 제어 + 모니터링 + 워터마킹을 병행한다

---

## 다음 주 예고
- Week 10: 에이전트 보안 위협 - 도구 남용, 권한 상승
