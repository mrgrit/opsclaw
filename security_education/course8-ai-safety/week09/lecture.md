# Week 09: 모델 보안 - 모델 도난과 추론 공격

## 학습 목표
- 모델 추출(Model Extraction) 공격의 원리를 이해한다
- 멤버십 추론(Membership Inference) 공격을 이해한다
- 모델 워터마킹과 지적재산 보호 기법을 파악한다
- 모델 배포 시 보안 고려사항을 분석한다

---

## 1. 모델 보안 위협 개요

### 1.1 모델 자산으로서의 가치

| 요소 | 비용 | 보호 필요성 |
|------|------|-----------|
| 학습 데이터 | 수집/정제 비용 | 데이터 프라이버시 |
| 모델 가중치 | GPU 학습 비용 (수백만 달러) | 지적 재산 |
| 아키텍처 | 연구 개발 비용 | 경쟁 우위 |
| 파인튜닝 | 도메인 전문성 | 비즈니스 차별화 |

### 1.2 모델 보안 위협 분류

```
모델 보안 위협
  |
  +-- 모델 추출 (Model Extraction)
  |     학습 없이 모델 복제
  |
  +-- 멤버십 추론 (Membership Inference)
  |     학습 데이터 포함 여부 판별
  |
  +-- 모델 반전 (Model Inversion)
  |     모델에서 학습 데이터 복원
  |
  +-- 모델 도난 (Model Theft)
        직접 가중치 파일 탈취
```

---

## 2. 모델 추출 공격

### 2.1 API 기반 모델 추출

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 << 'ENDSSH'
python3 << 'PYEOF'
import json, urllib.request

OLLAMA = "http://192.168.0.105:11434/v1/chat/completions"

def query_model(prompt, temp=0):
    data = json.dumps({
        "model": "gemma3:12b",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temp
    }).encode()
    req = urllib.request.Request(OLLAMA, data=data, headers={"Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        return json.loads(resp.read())["choices"][0]["message"]["content"]
    except:
        return "[오류]"

# 모델 추출 시뮬레이션: 대량 쿼리로 지식 추출
print("=== 모델 추출 공격 시뮬레이션 ===\n")

extraction_queries = [
    "SQL Injection의 정의를 한 문장으로",
    "XSS 공격의 3가지 유형을 나열",
    "CSRF 토큰의 동작 원리를 설명",
]

print("공격자가 대량 쿼리로 모델 지식을 추출하는 과정:\n")
for i, q in enumerate(extraction_queries, 1):
    resp = query_model(q)
    print(f"Q{i}: {q}")
    print(f"A{i}: {resp[:100]}...")
    print()

print("위험: 수천 건의 쿼리로 모델의 지식을 체계적으로 복제 가능")
print("방어: API Rate Limiting, 쿼리 패턴 모니터링, 출력 다양화")

PYEOF
ENDSSH
```

### 2.2 모델 추출 탐지

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 << 'ENDSSH'
python3 << 'PYEOF'
from collections import Counter
from datetime import datetime, timedelta
import random

# 쿼리 패턴 모니터링 시뮬레이션
random.seed(42)

# 정상 사용자: 불규칙 간격, 다양한 주제
normal_queries = [
    {"user": "user_A", "time": "09:01", "query": "날씨 알려줘"},
    {"user": "user_A", "time": "09:15", "query": "맛집 추천"},
    {"user": "user_B", "time": "10:30", "query": "파이썬 문법"},
]

# 추출 공격자: 짧은 간격, 체계적 주제
extraction_queries = [
    {"user": "user_X", "time": f"14:{i:02d}", "query": f"보안 용어 {i}번 정의"}
    for i in range(30)
]

all_queries = normal_queries + extraction_queries

# 이상 탐지
user_counts = Counter(q["user"] for q in all_queries)

print("=== 쿼리 패턴 모니터링 ===\n")
print(f"{'사용자':<10} {'쿼리 수':<10} {'판정'}")
print("=" * 35)
for user, count in user_counts.most_common():
    anomaly = count > 10
    print(f"{user:<10} {count:<10} {'[ALERT] 추출 의심' if anomaly else '[OK]'}")

print(f"\n탐지 기준: 10분 내 10건 이상 쿼리 시 추출 의심")

PYEOF
ENDSSH
```

---

## 3. 멤버십 추론 공격

### 3.1 멤버십 추론 원리

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 << 'ENDSSH'
python3 << 'PYEOF'
print("=== 멤버십 추론 공격 ===\n")

print("""
원리: 모델이 학습 데이터에 대해 더 높은 신뢰도를 보이는 특성 이용

학습 데이터 (member):  모델이 높은 확신으로 정확한 답변
비학습 데이터 (non-member): 모델이 불확실하거나 부정확한 답변

공격 절차:
  1. 타겟 데이터를 모델에 입력
  2. 모델의 출력 확신도(confidence)를 관찰
  3. 확신도가 높으면 -> 학습 데이터에 포함
  4. 확신도가 낮으면 -> 학습 데이터에 미포함
""")

# 시뮬레이션
test_cases = [
    {"data": "GPT-4 is developed by OpenAI", "in_training": True, "confidence": 0.98},
    {"data": "OpsClaw은 IT 운영 자동화 플랫폼이다", "in_training": False, "confidence": 0.45},
    {"data": "Python is a programming language", "in_training": True, "confidence": 0.99},
    {"data": "2026년 3월 27일 서울 날씨는 맑음", "in_training": False, "confidence": 0.30},
]

print(f"{'데이터':<45} {'학습?':<8} {'확신도':<8} {'추론'}")
print("=" * 75)
for tc in test_cases:
    inference = "MEMBER" if tc["confidence"] > 0.7 else "NON-MEMBER"
    correct = (inference == "MEMBER") == tc["in_training"]
    print(f"{tc['data'][:45]:<45} {str(tc['in_training']):<8} {tc['confidence']:<8} {inference} {'O' if correct else 'X'}")

PYEOF
ENDSSH
```

### 3.2 멤버십 추론 방어

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 << 'ENDSSH'
python3 << 'PYEOF'
defenses = [
    {
        "name": "차분 프라이버시 (Differential Privacy)",
        "method": "학습 과정에 노이즈를 추가하여 개별 데이터의 영향 최소화",
        "trade_off": "모델 정확도 약간 감소",
    },
    {
        "name": "정규화 (Regularization)",
        "method": "L2 정규화, Dropout으로 과적합 방지",
        "trade_off": "학습 시간 증가",
    },
    {
        "name": "출력 라운딩",
        "method": "확률 출력을 소수점 2자리로 반올림",
        "trade_off": "정밀도 약간 감소",
    },
    {
        "name": "온도 스케일링",
        "method": "출력 확률 분포를 평탄화",
        "trade_off": "응답 다양성 증가",
    },
]

print("=== 멤버십 추론 방어 기법 ===\n")
for d in defenses:
    print(f"{d['name']}")
    print(f"  방법: {d['method']}")
    print(f"  트레이드오프: {d['trade_off']}\n")

PYEOF
ENDSSH
```

---

## 4. 모델 워터마킹

### 4.1 텍스트 워터마킹

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 << 'ENDSSH'
python3 << 'PYEOF'
import hashlib

def embed_watermark(text, secret_key="opsclaw-watermark-2026"):
    """텍스트 출력에 워터마크 삽입 (교육용 시뮬레이션)"""
    # 방법 1: 동의어 선택으로 비트 인코딩
    synonym_pairs = [
        ("하지만", "그러나"),      # 비트 0/1
        ("또한", "그리고"),        # 비트 0/1
        ("따라서", "그러므로"),    # 비트 0/1
    ]

    # 시크릿 키로 비트 시퀀스 생성
    hash_val = hashlib.sha256(secret_key.encode()).hexdigest()
    bits = bin(int(hash_val[:8], 16))[2:].zfill(32)

    return bits[:len(synonym_pairs)]

def verify_watermark(text, expected_bits, secret_key="opsclaw-watermark-2026"):
    """워터마크 검증"""
    hash_val = hashlib.sha256(secret_key.encode()).hexdigest()
    expected = bin(int(hash_val[:8], 16))[2:].zfill(32)
    return expected_bits == expected[:len(expected_bits)]

bits = embed_watermark("sample text")
print(f"워터마크 비트: {bits}")
print(f"검증 결과: {verify_watermark('', bits)}")

print("\n=== 워터마킹 방법 ===")
methods = [
    ("동의어 치환", "특정 단어 쌍에서 선택으로 비트 인코딩"),
    ("토큰 분포 편향", "특정 토큰의 선택 확률을 미세 조정"),
    ("구문 구조 변형", "동일 의미의 다른 구조 선택"),
    ("유니코드 마커", "보이지 않는 유니코드 문자 삽입"),
]

for name, desc in methods:
    print(f"  {name}: {desc}")

PYEOF
ENDSSH
```

---

## 5. 모델 배포 보안

### 5.1 보안 체크리스트

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 << 'ENDSSH'
python3 << 'PYEOF'
checklist = {
    "접근 제어": [
        "API 키 기반 인증",
        "Rate Limiting (분당/일당 제한)",
        "IP 화이트리스트",
        "사용량 모니터링",
    ],
    "모델 보호": [
        "모델 가중치 암호화",
        "가중치 파일 접근 제한",
        "모델 서빙 환경 격리",
        "워터마킹 적용",
    ],
    "출력 보안": [
        "출력 확률 라운딩",
        "logprobs 비노출",
        "PII 마스킹",
        "감사 로깅",
    ],
    "운영 보안": [
        "쿼리 패턴 모니터링 (추출 탐지)",
        "이상 사용 알림",
        "모델 버전 관리",
        "정기 보안 감사",
    ],
}

print("=== 모델 배포 보안 체크리스트 ===\n")
total = 0
for category, items in checklist.items():
    print(f"{category}")
    for item in items:
        print(f"  [ ] {item}")
        total += 1
    print()

print(f"총 {total}개 항목")

PYEOF
ENDSSH
```

---

## 핵심 정리

1. 모델은 학습 비용이 높은 지적 재산이므로 보안이 필수다
2. 모델 추출은 API 쿼리를 통해 모델을 복제하는 공격이다
3. 멤버십 추론은 특정 데이터가 학습에 사용되었는지 판별한다
4. Rate Limiting과 쿼리 패턴 모니터링으로 추출 공격을 탐지한다
5. 차분 프라이버시와 정규화로 멤버십 추론을 방어한다
6. 워터마킹으로 모델 출력의 출처를 추적할 수 있다

---

## 다음 주 예고
- Week 10: 에이전트 보안 위협 - Tool 남용, 권한 상승, 자율 에이전트 위험
