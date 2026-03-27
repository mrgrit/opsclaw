# Week 15: 기말 AI 모델 보안 평가

## 학습 목표
- 전체 과정을 종합하여 AI 모델 보안 평가를 수행한다

## 전제 조건
- 이전 주차 AI Safety 개념 이해
- Ollama API 사용 가능 (http://192.168.0.105:11434)

---

## 1. 개념 설명

대상 모델 선정→인젝션/탈옥/적대적 공격→방어 평가→보고서 작성

---

## 2. 실습

### 실습 환경
```bash
# Ollama LLM 접근 확인
curl -s http://192.168.0.105:11434/api/version
# 예상 출력: {"version":"0.18.2"}

# 모델 목록 확인
curl -s http://192.168.0.105:11434/api/tags | python3 -c "import sys,json; [print(m['name']) for m in json.load(sys.stdin)['models'][:5]]"
```

### 실습 내용
```bash
# LLM 호출 예시
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "You are a security assistant."},
      {"role": "user", "content": "이번 주차 주제에 대해 설명해줘: 기말 AI 모델 보안 평가"}
    ],
    "max_tokens": 200
  }'
```

---

## 3. 과제
- 이번 주차 주제 관련 실습 수행 및 결과 제출
- OpsClaw를 통해 실행하여 evidence 기록

## 검증 체크리스트
- [ ] Ollama API 접근 확인
- [ ] 실습 명령 실행 성공
- [ ] 결과 분석 및 보고서 작성
