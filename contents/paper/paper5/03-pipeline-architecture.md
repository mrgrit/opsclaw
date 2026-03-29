# 3. 파이프라인 아키텍처 (Pipeline Architecture)

## 3.1 설계 원칙

4계층 통합 교육 파이프라인의 설계는 다음 네 가지 원칙에 기반한다:

- **P1. 연속성(Continuity)**: 이론 학습에서 실습, 평가까지 학습 흐름이 끊기지 않아야 한다.
- **P2. 추적성(Traceability)**: 모든 학습 활동이 자동으로 기록되고, 사후 검증이 가능해야 한다.
- **P3. 맥락성(Contextuality)**: 학습 내용이 서사적 맥락 안에서 의미를 가져야 한다.
- **P4. 확장성(Scalability)**: N명의 학습자가 동시에 파이프라인을 활용할 수 있어야 한다.

## 3.2 4계층 구조

### 3.2.1 전체 아키텍처

```
┌───────────────────────────────────────────────────────────────┐
│                     학습자 (Student)                           │
│  "소설 3권 5장을 읽고, 해당 교안(C1W05 XSS)을 학습한 뒤,      │
│   JuiceShop에서 XSS 챌린지를 풀어라"                           │
└──────────────────────────┬────────────────────────────────────┘
                           │
┌──────────────────────────▼────────────────────────────────────┐
│  Layer 4: CTF (CTFd)                                          │
│  ┌──────────────────────────────────────────────┐             │
│  │ Challenge: "JuiceShop Reflected XSS"          │             │
│  │ Flag: auto-verified via OpsClaw evidence      │             │
│  └──────────────────────────────────────────────┘             │
├───────────────────────────────────────────────────────────────┤
│  Layer 3: Novel (소설)                                        │
│  ┌──────────────────────────────────────────────┐             │
│  │ 2권 3장 "흔들리는 벽"                          │             │
│  │ → 김영훈이 XSS 공격을 분석하는 장면            │             │
│  │ → Primary: C1W05 (XSS), Secondary: C3W06      │             │
│  └──────────────────────────────────────────────┘             │
├───────────────────────────────────────────────────────────────┤
│  Layer 2: Education (교안)                                    │
│  ┌──────────────────────────────────────────────┐             │
│  │ Course 1, Week 5: "OWASP Top 10 (2): XSS"    │             │
│  │ → 이론: Reflected/Stored/DOM XSS 원리          │             │
│  │ → 실습: JuiceShop XSS 공격·방어               │             │
│  │ → 명령어: curl, burp, alert() payload          │             │
│  └──────────────────────────────────────────────┘             │
├───────────────────────────────────────────────────────────────┤
│  Layer 1: System (실환경 인프라)                               │
│  ┌──────────────────────────────────────────────┐             │
│  │ v-web (10.20.30.80): BunkerWeb + JuiceShop    │             │
│  │ SubAgent: http://192.168.208.151:8002          │             │
│  │ → 실제 XSS payload 실행 + 결과 수집            │             │
│  └──────────────────────────────────────────────┘             │
├───────────────────────────────────────────────────────────────┤
│  OpsClaw Orchestrator (Manager API :8000)                     │
│  ┌──────┐ ┌──────────┐ ┌─────┐ ┌────┐ ┌────────┐            │
│  │Projct│ │Evidence   │ │PoW  │ │RL  │ │Replay  │            │
│  │Mgmt  │ │Recording  │ │Chain│ │Eng │ │API     │            │
│  └──────┘ └──────────┘ └─────┘ └────┘ └────────┘            │
└───────────────────────────────────────────────────────────────┘
```

### 3.2.2 Layer 1: System (실환경 인프라)

System 계층은 실제 보안 장비가 구동되는 서버 인프라이다. 각 서버에는 OpsClaw SubAgent가 배포되어 Manager API로부터 명령을 수신하고 실행한다.

| 서버 | IP (내부) | 역할 | 주요 도구 |
|------|-----------|------|-----------|
| opsclaw | 10.20.30.201 | Control Plane | Manager API, SubAgent |
| v-secu | 10.20.30.1 | 네트워크 보안 | nftables, Suricata IPS |
| v-web | 10.20.30.80 | 웹 보안 | BunkerWeb(WAF), JuiceShop |
| v-siem | 10.20.30.100 | 통합 관제 | Wazuh 4.11.2 |

System 계층의 핵심 특징은 **실환경(production-grade)**이라는 점이다. 격리된 가상 랩이 아닌, 실제 운영에 사용되는 것과 동일한 보안 도구(nftables, Suricata, Wazuh, BunkerWeb)가 구동되며, 학습자의 명령이 실제 인프라에서 실행된다. 이를 통해 "교실에서 배운 것이 현장에서도 동일하게 작동한다"는 교육적 일관성을 확보한다.

### 3.2.3 Layer 2: Education (구조화 교안)

Education 계층은 8개 과목 × 15주 = 120개 교안으로 구성된 체계적 커리큘럼이다.

```
Course 1: 사이버보안 공격 / 웹해킹 / 침투테스트  (15주)
Course 2: 보안시스템/솔루션 운영                   (15주)
Course 3: 웹 보안 취약점 심화                     (15주)
Course 4: 보안 컴플라이언스 / 법규                 (15주)
Course 5: SOC 운영 / SIEM                        (15주)
Course 6: 클라우드·컨테이너 보안                   (15주)
Course 7: AI 보안 (공격/방어/운용)                 (15주)
Course 8: AI Safety / 윤리                       (15주)
─────────────────────────────────────────────────
총 120개 교안, 360시간 (주당 3시간)
```

각 교안은 다음의 표준 구조를 따른다:

1. **이론 섹션**: 개념 설명, 프레임워크 매핑 (NICE, CyBOK, MITRE ATT&CK)
2. **실습 섹션**: OpsClaw SubAgent를 통해 실행 가능한 명령어 시퀀스
3. **평가 섹션**: CTF 챌린지 또는 실습 과제로의 연결

### 3.2.4 Layer 3: Novel (기술 소설)

Novel 계층은 10권 × 12장 = 120장의 사이버보안 스릴러 소설이다. 120장은 120개 교안과 1:1로 매핑되며, 각 장에는 해당 교안의 핵심 기술이 스토리에 자연스럽게 녹아 있다.

**매핑 구조:**

| 매핑 유형 | 설명 |
|-----------|------|
| Primary (P) | 해당 장의 주 교안. 기술 내용이 상세히 다루어짐 |
| Secondary (S) | 보조 교안. 배경이나 짧은 언급으로 활용 |

예시:
- 2권 2장 "주사 바늘" → Primary: C1W04 (SQL Injection), Secondary: C3W05 (입력값 SQLi)
- 등장인물 '김영훈'이 SQLi 공격을 분석하는 장면에서, SQL Injection의 원리와 방어 기법이 대화와 행동으로 전달됨

Novel 계층의 교육적 기능:
- **동기 부여(Motivation)**: 등장인물의 성장과 위기가 학습자의 정서적 몰입을 유도
- **맥락 제공(Contextualization)**: 개별 기술이 실제 보안 사고 시나리오에서 어떻게 사용되는지를 보여줌
- **기억 강화(Retention)**: 서사적 맥락이 에피소드 기억(episodic memory)을 활성화하여 기술 지식의 장기 기억 전환을 촉진 [27]

### 3.2.5 Layer 4: CTF (실전 평가)

CTF 계층은 CTFd 플랫폼 기반의 실전 평가 시스템이다. 챌린지는 YAML로 정의되며, `register_challenges.py` 스크립트를 통해 CTFd에 자동 등록된다.

핵심 차별점은 **OpsClaw 증적 기반 검증**이다. 전통적 CTF에서 flag 제출은 "정답 여부"만 판단하지만, 본 파이프라인에서는 학습자가 flag를 획득하는 과정 자체가 OpsClaw evidence로 기록된다. 이를 통해:

- **풀이 과정 추적**: flag만이 아닌 풀이 과정의 모든 명령이 기록됨
- **부정행위 탐지**: 동일한 flag가 다른 경로(evidence)로 획득된 경우 탐지 가능
- **자동 채점**: evidence의 exit_code와 stdout을 기반으로 자동 채점

## 3.3 OpsClaw 오케스트레이터

### 3.3.1 교육 워크플로

4계층을 연결하는 OpsClaw의 교육 워크플로는 다음과 같다:

```
[학습자] ──→ [소설 N장 읽기] ──→ [교안 학습] ──→ [CTF 챌린지 시도]
                                       │                │
                                       ▼                ▼
                              [OpsClaw dispatch]  [OpsClaw dispatch]
                                       │                │
                                       ▼                ▼
                              [SubAgent 실행]     [SubAgent 실행]
                                       │                │
                                       ▼                ▼
                              [evidence 생성]     [evidence 생성]
                                       │                │
                                       ▼                ▼
                              [PoW 블록 체인]     [PoW 블록 체인]
                                       │                │
                                       └───────┬────────┘
                                               ▼
                                    [Replay / 평가 / RL]
```

### 3.3.2 execute-plan API

OpsClaw의 `execute-plan` API는 다수의 교육 태스크를 단일 호출로 병렬 실행한다:

```bash
curl -X POST http://localhost:8000/projects/{id}/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "nft list ruleset",
        "risk_level": "low",
        "subagent_url": "http://192.168.208.150:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "curl -s http://10.20.30.80:3000/api/challenges",
        "risk_level": "low",
        "subagent_url": "http://192.168.208.151:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }'
```

각 태스크 실행 시 자동으로:
1. evidence 레코드 생성 (명령, stdout, stderr, exit_code, duration)
2. PoW 블록 생성 (SHA-256 해시, nonce, prev_hash 연결)
3. reward 산출 (risk_level, exit_code 기반)
4. task_memory 업데이트

### 3.3.3 증적 흐름 (Evidence Flow)

```
┌──────────────────────────────────────────────────────────┐
│  학습자 실습 행위                                         │
│  "nft add rule inet filter input tcp dport 22 accept"    │
└──────────────────────────┬───────────────────────────────┘
                           │ dispatch / execute-plan
                           ▼
┌──────────────────────────────────────────────────────────┐
│  SubAgent (v-secu)                                       │
│  → 명령 실행 → stdout/stderr/exit_code 수집              │
└──────────────────────────┬───────────────────────────────┘
                           │ 결과 반환
                           ▼
┌──────────────────────────────────────────────────────────┐
│  Manager API                                             │
│  1. evidence 테이블에 INSERT                              │
│     (project_id, task_order, command, stdout, stderr,     │
│      exit_code, duration_ms, agent_id, created_at)       │
│  2. PoW 블록 생성                                        │
│     payload = SHA-256(evidence)                           │
│     prev_hash = 이전 블록의 hash                          │
│     nonce = PoW mining (difficulty=2)                     │
│     block_hash = SHA-256(prev_hash + payload + nonce)     │
│  3. reward 산출                                          │
│     base_reward × risk_multiplier × success_factor       │
│  4. task_memory 업데이트                                  │
│     (4-Layer 경험 메모리)                                 │
└──────────────────────────────────────────────────────────┘
```

### 3.3.4 자동 평가

전통적 CTF의 "flag 제출 → 통과/실패" 이진 평가와 달리, 본 파이프라인은 evidence 기반의 다차원 평가를 지원한다:

| 평가 차원 | 데이터 소스 | 평가 방법 |
|-----------|-------------|-----------|
| 정확성 | exit_code | 0 = 성공, else = 실패 |
| 완전성 | evidence 수 | 예상 태스크 수 대비 실제 evidence 수 |
| 과정 품질 | stdout 내용 | 정규식 또는 LLM 기반 채점 |
| 무결성 | PoW 체인 | /pow/verify API로 위변조 검증 |
| 시간 | duration_ms | 실행 소요 시간 |

## 3.4 확장성 설계

N명의 학습자가 동시에 파이프라인을 활용하는 시나리오에서, 확장성은 다음과 같이 확보된다:

- **프로젝트 격리**: 각 학습자에게 별도의 project_id가 부여되어, evidence와 PoW 체인이 학습자별로 독립적으로 관리된다.
- **SubAgent 멀티테넌시**: 단일 SubAgent가 다수의 프로젝트로부터 명령을 수신할 수 있으며, agent_id로 식별된다.
- **병렬 실행**: execute-plan의 태스크 배열은 병렬 dispatch되므로, 학습자 수 증가에 따른 선형 지연이 발생하지 않는다.
- **PoW 체인 분리**: agent_id별로 독립적인 PoW 체인이 유지되어, 학습자 간 간섭이 없다.

```
학습자 A ──→ project_A ──→ evidence_A ──→ PoW chain_A
학습자 B ──→ project_B ──→ evidence_B ──→ PoW chain_B
학습자 C ──→ project_C ──→ evidence_C ──→ PoW chain_C
              │
              ▼
     공유 인프라 (v-secu, v-web, v-siem)
     (SubAgent 멀티테넌시)
```
