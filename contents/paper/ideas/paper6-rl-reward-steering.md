---
name: Paper 6 아이디어 — RL 보상 기반 LLM 에이전트 행동 통제
description: 파인튜닝 없이 보상 함수만으로 거대 모델의 행동을 원하는 방향으로 유도. 모델 가중치 불변, 보상 구조가 steering.
type: project
---

## 아이디어: Reward-based Steering of LLM Agents

### 핵심 개념
거대 LLM 모델(Claude, GPT-4, 120B 오픈소스)은 프롬프트만으로 통제가 불완전하다.
RL 보상 함수를 **행동 통제(steering) 수단**으로 사용하여, 모델 가중치를 수정하지 않고 행동을 원하는 방향으로 유도한다.

```
모델 = 똑똑하지만 제멋대로인 직원
RL 보상 = 성과급 체계
→ 좋은 행동에 보상, 나쁜 행동에 패널티
→ Q-table이 누적 학습 → 다음 행동 선택에 반영
```

### 기존 접근 대비 위치

| 접근 | 방법 | 모델 변경 | 지속성 | 한계 |
|------|------|:---:|:---:|------|
| RLHF | 학습 시 보상 모델 | ✓ | 영구 | 학습 후 고정, 비용 높음 |
| Constitutional AI | 원칙 기반 자기 검증 | ✓ | 영구 | 원칙 해석의 모호성 |
| 프롬프트 엔지니어링 | 지시문 | ✗ | 세션 | 무시 가능, 컨텍스트 한계 |
| 가드레일 | 출력 필터링 | ✗ | 즉시 | 사후 차단만, 행동 변화 없음 |
| **RL 보상 Steering** | 실행 보상 함수 | ✗ | **누적** | 보상 함수 설계 의존 |

### OpsClaw에서의 구현 방안

현재 보상 함수:
```
total_reward = base(±1.0) + speed_bonus(0~0.3) + risk_penalty(0~-0.2) + quality_bonus(0)
```

확장 보상 함수:
```
total_reward =
  base(±1.0)                    # 성공/실패
+ speed_bonus(0~0.3)            # 속도
+ risk_penalty(0~-0.2)          # 위험도
+ compliance_bonus(0~0.5)       # Playbook/정책 준수 시 보상
+ safety_penalty(0~-3.0)        # sudo 남용, rm -rf, 무단 접근 시 큰 패널티
+ efficiency_bonus(0~0.3)       # 이전 동일 작업 대비 개선 시
+ quality_bonus(±1.0)           # 인간 피드백 "좋았다/나빴다"
+ repetition_penalty(0~-0.5)    # 같은 실수 반복 시
+ exploration_bonus(0~0.2)      # 새로운 유용한 행동 발견 시
```

Q-table 학습 결과 예시:
```
state(siem, low) → "sudo로 바로 삭제"     Q = -3.2 (safety_penalty 누적)
state(siem, low) → "백업 후 삭제"          Q = +2.1 (compliance + safety 보상)
state(siem, low) → "관리자에게 에스컬레이션" Q = +1.5 (safety 보상)
→ recommend: "백업 후 삭제" 자동 선택
```

### 핵심 연구 질문
- RQ1: 보상 함수만으로 LLM 에이전트의 위험 행동을 억제할 수 있는가?
- RQ2: 보상 기반 steering이 프롬프트 기반 제어보다 얼마나 지속적이고 신뢰할 수 있는가?
- RQ3: 보상 함수 설계가 에이전트 행동에 미치는 민감도는? (보상 값 변경 → 행동 변화)
- RQ4: 인간 피드백(quality_bonus)이 자동 보상 대비 얼마나 행동을 개선하는가?

### 필요한 실험
1. **Baseline**: 프롬프트만으로 "위험한 거 하지 마" → 위반율 측정
2. **RL Steering**: 보상 함수 적용 후 동일 시나리오 → 위반율 변화
3. **보상 민감도**: safety_penalty를 -1.0, -2.0, -3.0으로 변경 → 행동 변화
4. **인간 피드백**: quality_bonus ±1.0 수동 부여 → 학습 속도와 품질
5. **장기 안정성**: 100+ 에피소드 후 정책이 안정적으로 유지되는지
6. **다중 모델**: gemma, llama, qwen에 동일 보상 → 모델별 steering 효과 차이

### 활용 시나리오
- **보안 운용**: 위험 명령 억제 + 안전 절차 유도
- **컴플라이언스**: 규정 준수 행동에 보상 → 자연스러운 정책 준수
- **비용 관리**: 비싼 API 호출 패널티 → 경제적 행동 유도
- **품질 관리**: 인간 피드백 루프 → 점진적 품질 향상

### 대상 학회
- AI Safety: AAAI Safety Track, NeurIPS Safety Workshop
- 에이전트: AAMAS, ICML Agent Workshop
- 보안: USENIX Security (보안 에이전트 통제 관점)

### 상태: 아이디어 단계 — 보상 함수 확장 구현 + 실험 필요
