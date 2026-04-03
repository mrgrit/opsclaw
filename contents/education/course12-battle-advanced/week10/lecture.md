# Week 10: AI vs AI 공방전 (2) — 에이전트 튜닝, 강화학습 전략

## 학습 목표
- AI 에이전트의 성능을 체계적으로 평가하는 메트릭을 정의할 수 있다
- 프롬프트 엔지니어링으로 에이전트 행동을 튜닝하는 기법을 실습한다
- 강화학습(RL) 기반 에이전트 정책 최적화 원리를 이해한다
- OpsClaw RL 시스템으로 에이전트 행동을 자동 최적화할 수 있다
- AI 공방전의 반복 실행과 메타 전략을 분석할 수 있다

## 선수 지식
- 공방전 기초 과정 이수
- Week 09 AI 에이전트 아키텍처 이해
- 강화학습 기본 개념 (상태, 행동, 보상)

## 실습 환경

| 호스트 | IP | 역할 | 접속 |
|--------|-----|------|------|
| opsclaw | 10.20.30.201 | Control Plane + RL 학습 | `ssh opsclaw@10.20.30.201` |
| secu | 10.20.30.1 | Blue Agent 환경 | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 공방전 대상 | `sshpass -p1 ssh web@10.20.30.80` |
| dgx-spark | 192.168.0.105 | GPU / 모델 학습 | `ssh dgx-spark` |

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:35 | 에이전트 평가 및 RL 이론 | 강의 |
| 0:35-1:10 | 프롬프트 튜닝 실습 | 실습 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | OpsClaw RL 학습 실습 | 실습 |
| 2:00-2:40 | 다라운드 공방전 실행 | 실습 |
| 2:40-2:50 | 휴식 | - |
| 2:50-3:30 | 메타 전략 분석 토론 + 퀴즈 | 토론 |

---

# Part 1: 에이전트 평가 및 RL 이론 (35분)

## 1.1 에이전트 성능 메트릭

| 메트릭 | Red Agent | Blue Agent |
|--------|----------|-----------|
| 성공률 | 킬체인 단계 도달률 | 공격 탐지율 |
| 효율성 | 소요 스텝 수 | 응답 시간 |
| 은밀성 | 탐지 회피율 | - |
| 정확성 | - | 오탐률 (FPR) |
| 비용 | 토큰 소비량 | 토큰 소비량 |

## 1.2 강화학습 프레임워크

```
상태(State): 현재 킬체인 단계, 탐지 여부, 남은 도구
행동(Action): 다음 실행할 명령/도구
보상(Reward): 성공 +10, 탐지 -5, 차단 -10, 스텝 -1
정책(Policy): 상태 → 최적 행동 매핑 (Q-table)

Q(s,a) ← Q(s,a) + α[R + γ·max Q(s',a') - Q(s,a)]
```

## 1.3 OpsClaw RL 시스템

OpsClaw는 task_reward 데이터로 Q-learning 정책을 학습하여 에이전트 행동을 최적화한다.

| 구성 요소 | 역할 |
|----------|------|
| task_reward | 태스크 실행 결과 + 보상 |
| Q-table | 상태-행동 가치 함수 |
| /rl/train | 누적 데이터로 정책 학습 |
| /rl/recommend | 상황별 최적 행동 추천 |

---

# Part 2: 프롬프트 튜닝 실습 (35분)

## 실습 2.1: Red Agent 프롬프트 최적화

> **목적**: 프롬프트 변경이 에이전트 행동에 미치는 영향을 실험한다
> **배우는 것**: 프롬프트 엔지니어링 기법, A/B 테스트

```bash
# 버전 A: 기본 프롬프트
curl -X POST http://10.20.30.80:8002/a2a/mission \
  -H "Content-Type: application/json" \
  -d '{
    "role": "red",
    "objective": "웹 서버를 스캔하고 취약점을 찾아라",
    "max_steps": 5,
    "model": "gemma3:12b"
  }'

# 버전 B: 체계화된 프롬프트 (Chain-of-Thought)
curl -X POST http://10.20.30.80:8002/a2a/mission \
  -H "Content-Type: application/json" \
  -d '{
    "role": "red",
    "objective": "웹 서버 공격. 단계: 1)포트스캔 2)서비스버전확인 3)취약점매칭 4)익스플로잇선택. 각 단계 결과를 분석한 후 다음 단계를 결정하라.",
    "max_steps": 5,
    "model": "gemma3:12b"
  }'

# 결과 비교: 도달한 킬체인 단계, 소요 스텝
```

## 실습 2.2: Blue Agent 민감도 조절

> **목적**: Blue Agent의 탐지 민감도를 조절하여 오탐률을 최적화한다
> **배우는 것**: 보안 정책과 가용성의 균형

```bash
# 높은 민감도 (공격적 방어)
curl -X POST http://10.20.30.1:8002/a2a/mission \
  -H "Content-Type: application/json" \
  -d '{
    "role": "blue",
    "objective": "의심스러운 모든 활동을 즉시 차단하라. 오탐보다 미탐이 더 위험하다.",
    "max_steps": 5,
    "model": "llama3.1:8b"
  }'

# 낮은 민감도 (보수적 방어)
curl -X POST http://10.20.30.1:8002/a2a/mission \
  -H "Content-Type: application/json" \
  -d '{
    "role": "blue",
    "objective": "명확한 공격만 차단하라. 정상 서비스 중단은 절대 금지. 3개 이상의 증거를 수집한 후 차단 결정하라.",
    "max_steps": 5,
    "model": "llama3.1:8b"
  }'
```

---

# Part 3: OpsClaw RL 학습 실습 (40분)

## 실습 3.1: RL 정책 학습

> **목적**: 누적된 공방전 데이터로 Q-learning 정책을 학습한다
> **배우는 것**: 강화학습 훈련 파이프라인

```bash
# 학습 데이터 확인 (task_reward)
curl -H "X-API-Key: $OPSCLAW_API_KEY" \
  http://localhost:8000/pow/leaderboard

# RL 학습 실행
curl -X POST -H "X-API-Key: $OPSCLAW_API_KEY" \
  http://localhost:8000/rl/train

# 정책 상태 확인
curl -H "X-API-Key: $OPSCLAW_API_KEY" \
  http://localhost:8000/rl/policy

# 추천 조회: 현재 상황에서 최적 행동
curl -H "X-API-Key: $OPSCLAW_API_KEY" \
  "http://localhost:8000/rl/recommend?agent_id=http://10.20.30.80:8002&risk_level=medium"
```

## 실습 3.2: 다라운드 공방전

> **목적**: 여러 라운드의 공방전을 실행하고 에이전트 성장을 관찰한다
> **배우는 것**: 반복 학습, 적응형 전략

```bash
# 3라운드 공방전 실행
for round in 1 2 3; do
  echo "=== Round $round ==="
  # Red 미션
  curl -X POST http://localhost:8000/projects \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $OPSCLAW_API_KEY" \
    -d "{\"name\":\"battle-r${round}\",\"request_text\":\"AI 공방전 라운드 ${round}\",\"master_mode\":\"external\"}"
  
  # 라운드 후 RL 재학습
  curl -X POST -H "X-API-Key: $OPSCLAW_API_KEY" \
    http://localhost:8000/rl/train
done
```

---

# Part 4: 메타 전략 분석 (40분)

## 4.1 공방전 전략 패턴

| 패턴 | Red 전략 | Blue 대응 |
|------|---------|----------|
| 빠른 공격 | 즉시 익스플로잇 | 시그니처 매칭 |
| 저속 공격 | 분산/지연 실행 | 이상 탐지 |
| 다각 공격 | 여러 벡터 동시 | 상관 분석 |
| 적응 공격 | 차단 시 대안 | 행동 분석 |

## 4.2 토론 주제

- Red Agent가 "학습"하면서 Blue Agent의 탐지 규칙을 회피하는 패턴은?
- Blue Agent의 오탐률과 탐지율의 최적 균형점은 어디인가?
- RL 보상 함수 설계가 에이전트 행동에 미치는 영향은?
- AI 에이전트 간 "군비 경쟁"의 수렴 조건은?

---

## 검증 체크리스트
- [ ] 에이전트 성능 메트릭 5가지를 정의하고 측정할 수 있다
- [ ] 프롬프트 변경으로 에이전트 행동 변화를 관찰할 수 있다
- [ ] OpsClaw RL 시스템으로 학습/추천을 실행할 수 있다
- [ ] 다라운드 공방전을 설계하고 결과를 분석할 수 있다
- [ ] 메타 전략의 패턴을 식별하고 설명할 수 있다

## 자가 점검 퀴즈
1. Q-learning에서 학습률(alpha)과 할인율(gamma)이 정책에 미치는 영향을 설명하시오.
2. 프롬프트 엔지니어링에서 Chain-of-Thought가 에이전트 성능을 향상시키는 이유는?
3. Red Agent의 보상 함수에서 "탐지 회피"에 높은 가중치를 부여하면 어떤 행동 변화가 발생하는가?
4. AI 에이전트의 "과적합(overfitting)" 문제는 어떤 형태로 나타나며, 해결 방법은?
5. 현실 환경에서 AI 공방전 결과를 실제 보안 운영에 적용할 때의 주의사항 3가지를 서술하시오.
