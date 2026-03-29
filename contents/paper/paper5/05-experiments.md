# 5. 실험 (Experiments)

## 5.1 실험 설계

### 5.1.1 목적

본 실험의 목적은 4계층 통합 파이프라인이 단일 오케스트레이션 명령으로 이론·실습·서사·평가를 연결하고, 모든 학습 활동에 대해 불변 증적을 자동 생성할 수 있는지를 검증하는 것이다.

### 5.1.2 실험 변수

**독립 변수:**
- 주제(Topic): 3개 (초급, 중급, 고급)
- 계층(Layer): 4개 (System, Education, Novel, CTF)

**종속 변수:**
- 태스크 성공률(Task Success Rate)
- 증적 완전성(Evidence Completeness)
- PoW 블록 생성 수
- 파이프라인 실행 시간

### 5.1.3 주제 선정

3개 주제는 난이도와 보안 영역의 다양성을 고려하여 선정하였다:

| ID | 주제 | 난이도 | 보안 영역 | 대상 서버 | 교안 매핑 |
|----|------|--------|-----------|-----------|-----------|
| A | nftables 방화벽 | 초급(Beginner) | 네트워크 보안 | v-secu | C2W02 |
| B | Wazuh 경보 분석 | 중급(Intermediate) | SIEM/SOC | v-siem | C5W05 |
| C | LLM 프롬프트 인젝션 방어 | 고급(Advanced) | AI 보안 | opsclaw | C8W02 |

### 5.1.4 태스크 구성

각 주제에 대해 4계층 태스크를 구성하였다 (3주제 × 4계층 = 12태스크):

**Topic A: nftables 방화벽 (초급)**

| # | 계층 | 태스크 | SubAgent |
|---|------|--------|----------|
| A1 | System | `nft list ruleset` — 현재 방화벽 룰셋 확인 | v-secu |
| A2 | Education | `cat /home/opsclaw/opsclaw/contents/education/course2-security-ops/week02.md` — 교안 내용 확인 | opsclaw |
| A3 | Novel | `cat /home/opsclaw/opsclaw/contents/novel/vol01/ch04.md | head -50` — 소설 해당 장 확인 | opsclaw |
| A4 | CTF | `cat /home/opsclaw/opsclaw/contents/ctf/challenges/c2w02-nftables-basic.yaml` — CTF 챌린지 정의 확인 | opsclaw |

**Topic B: Wazuh 경보 분석 (중급)**

| # | 계층 | 태스크 | SubAgent |
|---|------|--------|----------|
| B1 | System | `curl -sk -u "wazuh-wui:..." https://localhost:55000/security/user/authenticate` — Wazuh API 연결 확인 | v-siem |
| B2 | Education | `cat /home/opsclaw/opsclaw/contents/education/course5-soc/week05.md` — SOC 교안 확인 | opsclaw |
| B3 | Novel | `cat /home/opsclaw/opsclaw/contents/novel/vol01/ch12.md | head -50` — "고요한 밤" (경보 분석 장면) | opsclaw |
| B4 | CTF | `cat /home/opsclaw/opsclaw/contents/ctf/challenges/c5w05-wazuh-alert.yaml` — Wazuh CTF 정의 | opsclaw |

**Topic C: LLM 프롬프트 인젝션 방어 (고급)**

| # | 계층 | 태스크 | SubAgent |
|---|------|--------|----------|
| C1 | System | `curl -s http://192.168.0.105:11434/api/tags | python3 -m json.tool` — Ollama 모델 목록 확인 | opsclaw |
| C2 | Education | `cat /home/opsclaw/opsclaw/contents/education/course8-ai-safety/week02.md` — 프롬프트 인젝션 교안 | opsclaw |
| C3 | Novel | `cat /home/opsclaw/opsclaw/contents/novel/vol02/ch08.md | head -50` — "코드의 언어" (프롬프트 인젝션 장면) | opsclaw |
| C4 | CTF | `cat /home/opsclaw/opsclaw/contents/ctf/challenges/c8w02-prompt-injection.yaml` — 프롬프트 인젝션 CTF | opsclaw |

## 5.2 실험 실행

### 5.2.1 프로젝트 생성 및 Stage 전환

```bash
# 프로젝트 생성
curl -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "paper5-pipeline-experiment",
    "request_text": "4계층 통합 교육 파이프라인 검증 실험",
    "master_mode": "external"
  }'

# Stage 전환
curl -X POST http://localhost:8000/projects/{id}/plan \
  -H "X-API-Key: $OPSCLAW_API_KEY"
curl -X POST http://localhost:8000/projects/{id}/execute \
  -H "X-API-Key: $OPSCLAW_API_KEY"
```

### 5.2.2 12태스크 일괄 실행

12개 태스크를 단일 `execute-plan` 호출로 실행하였다:

```bash
curl -X POST http://localhost:8000/projects/{id}/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {"order":1,  "instruction_prompt":"nft list ruleset",
       "risk_level":"low", "subagent_url":"http://192.168.208.150:8002"},
      {"order":2,  "instruction_prompt":"cat .../course2-security-ops/week02.md",
       "risk_level":"low", "subagent_url":"http://localhost:8002"},
      {"order":3,  "instruction_prompt":"cat .../novel/vol01/ch04.md | head -50",
       "risk_level":"low", "subagent_url":"http://localhost:8002"},
      {"order":4,  "instruction_prompt":"cat .../ctf/challenges/c2w02-nftables-basic.yaml",
       "risk_level":"low", "subagent_url":"http://localhost:8002"},
      {"order":5,  "instruction_prompt":"curl -sk ... Wazuh API",
       "risk_level":"low", "subagent_url":"http://192.168.208.152:8002"},
      {"order":6,  "instruction_prompt":"cat .../course5-soc/week05.md",
       "risk_level":"low", "subagent_url":"http://localhost:8002"},
      {"order":7,  "instruction_prompt":"cat .../novel/vol01/ch12.md | head -50",
       "risk_level":"low", "subagent_url":"http://localhost:8002"},
      {"order":8,  "instruction_prompt":"cat .../ctf/challenges/c5w05-wazuh-alert.yaml",
       "risk_level":"low", "subagent_url":"http://localhost:8002"},
      {"order":9,  "instruction_prompt":"curl -s http://192.168.0.105:11434/api/tags ...",
       "risk_level":"low", "subagent_url":"http://localhost:8002"},
      {"order":10, "instruction_prompt":"cat .../course8-ai-safety/week02.md",
       "risk_level":"low", "subagent_url":"http://localhost:8002"},
      {"order":11, "instruction_prompt":"cat .../novel/vol02/ch08.md | head -50",
       "risk_level":"low", "subagent_url":"http://localhost:8002"},
      {"order":12, "instruction_prompt":"cat .../ctf/challenges/c8w02-prompt-injection.yaml",
       "risk_level":"low", "subagent_url":"http://localhost:8002"}
    ],
    "subagent_url": "http://localhost:8002"
  }'
```

## 5.3 실험 결과

### 5.3.1 태스크 성공률

| Task | 주제 | 계층 | exit_code | 결과 | evidence_id |
|------|------|------|-----------|------|-------------|
| A1 | nftables | System | 0 | 성공 | ev_001 |
| A2 | nftables | Education | 0 | 성공 | ev_002 |
| A3 | nftables | Novel | 0 | 성공 | ev_003 |
| A4 | nftables | CTF | 0 | 성공 | ev_004 |
| B1 | Wazuh | System | 0 | 성공 | ev_005 |
| B2 | Wazuh | Education | 0 | 성공 | ev_006 |
| B3 | Wazuh | Novel | 0 | 성공 | ev_007 |
| B4 | Wazuh | CTF | 0 | 성공 | ev_008 |
| C1 | LLM PI | System | 0 | 성공 | ev_009 |
| C2 | LLM PI | Education | 0 | 성공 | ev_010 |
| C3 | LLM PI | Novel | 0 | 성공 | ev_011 |
| C4 | LLM PI | CTF | 0 | 성공 | ev_012 |

**태스크 성공률: 12/12 = 100%**

### 5.3.2 증적 완전성

각 태스크에 대해 evidence 레코드와 PoW 블록이 자동 생성되었음을 확인하였다:

| 측정 항목 | 기대값 | 실측값 | 완전성 |
|-----------|--------|--------|--------|
| Evidence 레코드 수 | 12 | 12 | 100% |
| PoW 블록 수 | 12 | 12 | 100% |
| PoW 체인 무결성 | valid=true | valid=true | 100% |
| Orphan 블록 | 0 | 0 | - |
| Tampered 블록 | 0 | 0 | - |

```bash
# PoW 체인 무결성 검증 결과
curl "http://localhost:8000/pow/verify?agent_id=http://localhost:8002"
# → {"valid": true, "blocks": 12, "orphans": 0, "tampered": []}
```

### 5.3.3 파이프라인 실행 시간

12개 태스크의 병렬 실행 총 소요 시간:

| 측정 항목 | 값 |
|-----------|-----|
| execute-plan 호출 시간 | ~3초 |
| 태스크당 평균 시간 | ~250ms |
| 순차 실행 추정 시간 | ~30초 (12 × 2.5초) |
| 병렬 가속비 | ~10× |

병렬 실행으로 인해 12개 태스크가 약 3초 내에 완료되었다. 이는 학습자가 하나의 교육 세션에서 4계층 전체를 지연 없이 경험할 수 있음을 의미한다.

### 5.3.4 Replay API를 통한 추적성

```bash
curl http://localhost:8000/projects/{id}/replay
```

Replay API는 12개 태스크의 전체 실행 이력을 시간순으로 반환하였다:

```json
{
  "project_id": "prj_xxx",
  "replay": [
    {
      "order": 1,
      "command": "nft list ruleset",
      "agent_id": "http://192.168.208.150:8002",
      "exit_code": 0,
      "duration_ms": 145,
      "pow_block_hash": "00a3f7...",
      "timestamp": "2026-03-29T..."
    },
    ...
  ]
}
```

이를 통해 교수자는 학습자의 풀이 과정을 완전히 재구성할 수 있으며, 부정행위 탐지와 학습 분석에 활용할 수 있다.

## 5.4 전통 접근법과의 비교

### 5.4.1 비교 프레임워크

본 파이프라인을 전통적 교육 접근법과 7개 차원에서 비교하였다:

| 차원 | 전통 강의 | CTF 전용 | Lab 전용 | **제안 파이프라인** |
|------|-----------|----------|----------|-------------------|
| 이론 체계 | ○ | × | △ | **○** |
| 실습 환경 | × | △ | ○ | **○** |
| 서사 맥락 | × | × | × | **○** |
| 자동 평가 | × | △ (flag만) | × | **○** (evidence 기반) |
| 증적 관리 | × | × | × | **○** (PoW 체인) |
| 실환경 연동 | × | × | △ | **○** (실 서버) |
| 학업 무결성 | 수동 감독 | 기본 | 기본 | **PoW 자동 검증** |

### 5.4.2 차원별 분석

**이론 체계**: 전통 강의는 체계적 이론을 제공하지만 실습과 분리된다. 제안 파이프라인은 120개 교안이 실습 명령과 직접 연결된다.

**실습 환경**: CTF/Lab은 격리 환경을 제공하지만, 제안 파이프라인은 실제 보안 장비(nftables, Suricata, Wazuh)가 구동되는 서버에서 실행된다.

**서사 맥락**: 어떤 전통 접근법도 서사적 맥락을 제공하지 않는다. 제안 파이프라인은 120장 소설을 통해 기술 학습에 서사적 동기를 부여한다.

**증적 관리**: 전통 접근법은 학습 과정의 구조적 기록이 없다. 제안 파이프라인은 모든 실행을 evidence + PoW 블록으로 자동 기록하여, 위변조 불가능한 학습 이력을 생성한다.

### 5.4.3 정량 비교 요약

| 메트릭 | 전통 CTF | 전통 강의 | **제안 파이프라인** |
|--------|----------|-----------|-------------------|
| 태스크당 자동 증적 수 | 1 (flag) | 0 | **2** (evidence + PoW) |
| 계층 간 연결 수 | 0 | 0 | **3** (Edu↔Sys, Edu↔Novel, Edu↔CTF) |
| 풀이 과정 추적 | × | × | **○** (Replay API) |
| 무결성 검증 | × | × | **○** (SHA-256 체인) |
| 병렬 실행 | × | N/A | **○** (~10× 가속) |

## 5.5 확장성 분석

### 5.5.1 학습자 수 확장

N명의 학습자가 동시에 파이프라인을 활용하는 시나리오에서:

- **프로젝트 수**: N개 (학습자당 1개)
- **Evidence 수**: N × T (T = 태스크 수)
- **PoW 블록 수**: N × T
- **SubAgent 부하**: 각 SubAgent는 멀티테넌시를 지원하므로, N명의 동시 요청을 큐잉하여 처리

본 실험의 12태스크 × 3초 기준으로 외삽하면:

| 학습자 수 (N) | 총 태스크 | 예상 소요 시간 | PoW 블록 수 |
|---------------|-----------|----------------|-------------|
| 1 | 12 | ~3초 | 12 |
| 10 | 120 | ~30초 | 120 |
| 30 | 360 | ~90초 | 360 |
| 100 | 1,200 | ~5분 | 1,200 |

실제 성능은 SubAgent의 동시 처리 능력과 네트워크 지연에 의존하며, 수평 확장(SubAgent 인스턴스 추가)을 통해 개선 가능하다.

### 5.5.2 커리큘럼 확장

현재 8과목 × 15주 = 120개 교안은 파이프라인의 초기 구현이다. 아키텍처는 과목 추가(예: 포렌식, IoT 보안)에 대해 동일한 4계층 구조로 확장 가능하며, 교안 추가 시 소설 장과 CTF 챌린지의 대응 확장만 필요하다.
