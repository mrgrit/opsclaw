# 6. 논의 (Discussion)

## 6.1 각 패러다임의 최적 적용 영역

실험 결과를 종합하면, 각 패러다임의 최적 적용 영역이 명확히 구분된다.

**클라이언트 하네스가 유리한 경우:**
- **개발 작업**: 코드 작성, 리팩터링, 디버깅 — 파일 I/O와 코드 검색이 핵심
- **탐색적 작업**: 새로운 시스템을 분석하거나 아직 절차가 정해지지 않은 작업
- **1회성 작업**: 반복할 필요가 없는 단발성 명령 실행
- **개인 생산성**: 개발자 1인이 빠르게 작업을 완료하는 것이 목표

**서버 하네스가 유리한 경우:**
- **반복 운영**: 매일/매주 수행하는 보안 점검, 인프라 모니터링
- **감사 필요**: 누가 언제 무엇을 실행했는지 증명해야 하는 환경
- **팀 협업**: Red/Blue/Purple Team 운용처럼 여러 역할이 결과를 공유
- **학습/개선**: 반복 실행에서 축적된 데이터로 정책을 자동 최적화

**판단 기준 1문장:** "이 작업의 결과를 나중에 **증명하거나 재현**해야 하는가?" → Yes이면 서버 하네스, No이면 클라이언트 하네스.

## 6.2 하이브리드 아키텍처: "Claude Code as Master + OpsClaw as Control Plane"

본 연구의 모든 실험은 사실 **하이브리드 모드**로 수행되었다:

```
Claude Code (클라이언트 하네스)
  ↕ REST API 호출
OpsClaw Manager API (서버 하네스)
  ↕ 태스크 위임
SubAgent (실행 노드)
```

이 하이브리드에서:
- **Claude Code**가 자연어 요청을 분석하고, 작업 계획을 수립하고, OpsClaw API를 호출한다 (Master 역할)
- **OpsClaw Manager**가 프로젝트 라이프사이클을 관리하고, 증적을 기록하고, PoW와 보상을 생성한다 (Control Plane 역할)
- **SubAgent**가 대상 서버에서 실제 명령을 실행한다 (Executor 역할)

**하이브리드의 이점:**

| 측면 | 클라이언트만 | 서버만 | 하이브리드 |
|------|-----------|--------|---------|
| 유연성 | ✓ | | ✓ (Claude Code) |
| 증적 | | ✓ | ✓ (OpsClaw) |
| 재현성 | | ✓ | ✓ (Playbook) |
| 학습 | △ (auto-memory) | ✓ (RL) | ✓ (양쪽 모두) |
| 속도 | ✓ | | △ (오버헤드 있지만 관리 가능) |

하이브리드에서 유일한 단점은 **오버헤드**(클라이언트→서버 API 호출 비용)이지만, 이는 증적·추적·학습의 가치로 상쇄된다.

## 6.3 향후 통합 방향

### 방향 1: Claude Code 훅 → OpsClaw 자동 연동

Claude Code의 PostToolUse 훅에 OpsClaw evidence 생성을 연결하면, Claude Code의 모든 Bash 실행이 자동으로 OpsClaw에 기록된다:

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "http",
        "url": "http://localhost:8000/projects/{id}/evidence",
        "method": "POST"
      }]
    }]
  }
}
```

### 방향 2: OpsClaw Playbook → Claude Code Skill 변환

OpsClaw Playbook의 선언적 태스크 배열을 Claude Code Skill 프롬프트로 자동 변환하면, Playbook의 재현성과 Skill의 유연성을 결합할 수 있다.

### 방향 3: Claude Code auto-memory ↔ OpsClaw Experience 동기화

Claude Code의 auto-memory에 축적된 학습을 OpsClaw Experience로 동기화하고, 역으로 OpsClaw의 고보상 경험을 CLAUDE.md에 주입하면, 개인 학습과 팀 학습이 통합된다.

## 6.4 한계점

**(1) 단일 비교 대상.** 클라이언트 하네스로 Claude Code만, 서버 하네스로 OpsClaw만 비교하였다. Cursor, Devin, CALDERA 등 다른 시스템과의 비교가 필요하다.

**(2) 정성적 비교 포함.** 메모리/학습 비교(실험 3)는 정성적 분석에 의존하며, 정량적 측정이 어렵다. auto-memory의 효과를 수치화하는 방법론이 필요하다.

**(3) 동일 LLM 사용.** 양쪽 모두 Claude를 사용하므로, LLM 자체의 차이가 아닌 하네스의 차이만 비교한다. 다른 LLM(GPT-4, Llama)에서의 결과는 다를 수 있다.

**(4) 실험 규모.** 5개 태스크 벤치마크는 소규모이다. 대규모(50+ 태스크) 장기 운영에서의 비교가 필요하다.
