# 4. 구현 (Implementation)

## 4.1 인프라 구성

### 4.1.1 서버 토폴로지

파이프라인의 물리적 인프라는 4대의 서버로 구성되며, 내부 네트워크(10.20.30.0/24)로 연결된다.

```
┌─────────────────────────────────────────────────────────┐
│                    외부 네트워크                          │
│               192.168.208.0/24                          │
├────────┬───────────┬───────────┬────────────────────────┤
│ opsclaw│  v-secu   │  v-web    │  v-siem                │
│ .142   │  .150     │  .151     │  .152                  │
├────────┴───────────┴───────────┴────────────────────────┤
│                   내부 네트워크                           │
│               10.20.30.0/24                             │
├────────┬───────────┬───────────┬────────────────────────┤
│ .201   │  .1       │  .80      │  .100                  │
│ Manager│  nftables │  BunkerWeb│  Wazuh                 │
│ API    │  Suricata │  JuiceShop│  4.11.2                │
│ :8000  │  IPS      │  WAF      │  SIEM                  │
│        │           │           │                        │
│ Sub    │  Sub      │  Sub      │  Sub                   │
│ Agent  │  Agent    │  Agent    │  Agent                 │
│ :8002  │  :8002    │  :8002    │  :8002                 │
└────────┴───────────┴───────────┴────────────────────────┘
```

### 4.1.2 서버별 보안 도구

**v-secu (네트워크 보안)**:
- nftables: Linux 커널 방화벽. 테이블/체인/룰 기반 패킷 필터링
- Suricata IPS: 네트워크 침입 방지 시스템. NFQUEUE 모드로 인라인 차단
- 교육 활용: Course 1(공격), Course 2(방어) 실습 대상

**v-web (웹 보안)**:
- BunkerWeb: ModSecurity 기반 WAF(Web Application Firewall)
- OWASP JuiceShop: 의도적 취약 웹 애플리케이션 (OWASP Top 10 학습용)
- 교육 활용: Course 1(웹해킹), Course 3(웹취약점 심화) 실습 대상

**v-siem (통합 관제)**:
- Wazuh 4.11.2: 오픈소스 SIEM/XDR 플랫폼
- 에이전트: 모든 서버에 Wazuh Agent 설치, 중앙 집중 로그 수집
- 교육 활용: Course 5(SOC/SIEM), Course 7(AI 보안) 실습 대상

### 4.1.3 SubAgent 배포

각 서버의 SubAgent는 OpsClaw의 `apps/subagent-runtime/` 코드베이스를 기반으로 배포된다. 배포 스크립트(`scripts/deploy_subagent.sh`)를 통해 원격 서버에 자동 배포되며, 각 SubAgent는 Manager API로부터 명령을 수신하여 로컬에서 실행한다.

```bash
# SubAgent 배포 (전체 서버)
./scripts/deploy_subagent.sh

# 특정 서버만 배포
./scripts/deploy_subagent.sh secu
```

SubAgent의 핵심 엔드포인트:
- `POST /execute`: 단일 명령 실행
- `POST /a2a/invoke_llm`: LLM 호출 (Ollama 연동)
- `POST /a2a/analyze`: 로그/데이터 분석

## 4.2 커리큘럼 구현

### 4.2.1 8과목 체계

120개 교안은 NICE Framework과 CyBOK의 지식 영역을 커버하도록 설계되었다:

| 과목 | 주제 | NICE 범주 | CyBOK 영역 | 교안 수 |
|------|------|-----------|------------|---------|
| C1 | 사이버보안 공격/웹해킹/침투테스트 | Collect and Operate | Attack | 15 |
| C2 | 보안시스템/솔루션 운영 | Operate and Maintain | Security Ops | 15 |
| C3 | 웹 보안 취약점 심화 | Analyze | Web Security | 15 |
| C4 | 보안 컴플라이언스/법규 | Oversee and Govern | Law & Regulation | 15 |
| C5 | SOC 운영/SIEM | Protect and Defend | Security Ops | 15 |
| C6 | 클라우드·컨테이너 보안 | Securely Provision | Cloud Security | 15 |
| C7 | AI 보안 (공격/방어/운용) | Analyze | AI Security | 15 |
| C8 | AI Safety/윤리 | Oversee and Govern | AI Safety | 15 |

### 4.2.2 교안 표준 구조

각 교안은 다음의 표준 구조를 따르며, Markdown 형식으로 작성된다:

```markdown
# Course X, Week Y: 제목

## 학습 목표
- 목표 1
- 목표 2

## 이론
### 개념 설명
...
### 프레임워크 매핑
- MITRE ATT&CK: T1234
- NICE: PR.AC-1
- CyBOK: Web Security > Input Validation

## 실습
### 환경 준비
```bash
# OpsClaw dispatch로 실행 가능한 명령
curl -X POST http://localhost:8000/projects/{id}/dispatch \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{"command":"nft list ruleset","subagent_url":"http://192.168.208.150:8002"}'
```

### 실습 단계
1. 단계 1: ...
2. 단계 2: ...

## CTF 챌린지
- 챌린지명: ...
- 난이도: ...
- Flag 형식: opsclaw{...}

## 소설 연결
- 해당 장: N권 M장 "제목"
- 장면: 등장인물이 해당 기술을 활용하는 장면 설명
```

### 4.2.3 난이도 계층

120개 교안은 3단계 난이도로 분류된다:

| 난이도 | 과목 | 주차 | 특성 |
|--------|------|------|------|
| 초급(Beginner) | C1~C4 | 1~5주 | 기초 개념, 단일 도구 실습 |
| 중급(Intermediate) | C1~C8 | 6~10주 | 복합 시나리오, 다중 도구 연동 |
| 고급(Advanced) | C5~C8 | 11~15주 | 실전 시나리오, 자율 분석·대응 |

## 4.3 소설 통합

### 4.3.1 매핑 체계

10권 × 12장 = 120장의 소설은 120개 교안과 1:1 매핑된다. 매핑은 Primary(P)와 Secondary(S) 두 수준으로 이루어진다:

- **Primary**: 해당 장의 주 교안. 등장인물의 핵심 행동이 교안의 기술 내용을 상세히 반영함
- **Secondary**: 보조 교안. 대화나 배경 설명에서 간접적으로 언급됨

### 4.3.2 기술 내용의 서사적 변환 예시

**교안**: Course 2, Week 2 — nftables 방화벽 기초

**소설 (1권 4장 "벽돌 쌓기")**:

> 도윤은 터미널 앞에 앉아 야간 방화벽 점검을 시작했다. 추팀장이 내려준 매뉴얼의 첫 줄에는 이렇게 적혀 있었다.
>
> ```
> nft list ruleset
> ```
>
> "전체 룰셋을 먼저 확인해. 뭐가 있는지도 모르면서 룰을 추가하면 안 돼."
> 추팀장의 말이 귓가에 맴돌았다. 화면에 inet filter 테이블이 펼쳐졌다.
> input 체인, forward 체인, output 체인. 도윤은 각 체인의 의미를 하나씩 되새겼다.

이 장면에서 학습자는:
1. `nft list ruleset` 명령의 용도를 이해함
2. nftables의 테이블/체인 구조를 파악함
3. 방화벽 운영의 기본 원칙("현재 상태 확인 후 변경")을 자연스럽게 습득함

### 4.3.3 소설의 구조적 기능

| 소설 요소 | 교육 기능 | 예시 |
|-----------|-----------|------|
| 등장인물 역할 | 보안 직무 모델링 | SOC 분석관, 침투 테스터, 컴플라이언스 담당 |
| 사건 전개 | 보안 사고 시나리오 | APT 공격, 내부자 위협, 데이터 유출 |
| 기술 대화 | 명령어·개념 전달 | "nft add rule..." 형태의 자연어 설명 |
| 갈등·해결 | 문제 해결 과정 모델링 | 공격 탐지 → 분석 → 차단 → 보고 |
| 반전(twist) | 비판적 사고 촉진 | OpsClaw 증적으로 내부 비리 발견 |

## 4.4 CTF 통합

### 4.4.1 챌린지 정의

CTF 챌린지는 YAML 형식으로 정의되며, 교안과의 매핑 정보를 포함한다:

```yaml
# contents/ctf/challenges/c2w02-nftables-basic.yaml
name: "nftables 기본 룰셋 점검"
category: "Network Security"
difficulty: easy
points: 100
description: |
  v-secu 서버의 nftables 룰셋을 확인하고,
  SSH(22)가 허용되어 있는지 점검하라.
flag: "opsclaw{nft_input_ssh_accept}"
lecture_mapping: "C2W02"
novel_mapping: "Vol01Ch04"
hint: "nft list ruleset 명령으로 시작하라"
```

### 4.4.2 자동 등록

`register_challenges.py` 스크립트가 YAML 정의를 파싱하여 CTFd API를 통해 챌린지를 자동 등록한다:

```bash
python3 contents/ctf/scripts/register_challenges.py \
  --ctfd-url http://localhost:8080 \
  --token $CTFD_API_TOKEN \
  --challenges-dir contents/ctf/challenges/
```

### 4.4.3 OpsClaw 증적 연동

CTF flag 획득 과정이 OpsClaw evidence로 기록되는 흐름:

```
1. 학습자가 CTF 챌린지 확인
2. OpsClaw dispatch로 실습 명령 실행
   → POST /projects/{id}/dispatch
   → {"command": "nft list ruleset", "subagent_url": "http://192.168.208.150:8002"}
3. SubAgent 실행 → stdout에 ruleset 출력
4. Manager: evidence 생성 + PoW 블록 생성
5. 학습자가 stdout에서 flag 확인
6. CTFd에 flag 제출
7. 교수자: /projects/{id}/replay로 풀이 과정 전체 확인
```

## 4.5 OpsClaw API 활용

### 4.5.1 프로젝트 생성

교육 세션은 OpsClaw 프로젝트로 관리된다:

```bash
curl -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "student-kim-c2w02",
    "request_text": "nftables 기초 실습 (Course 2, Week 2)",
    "master_mode": "external"
  }'
# → {"id": "prj_abc123...", "stage": "created"}
```

### 4.5.2 Stage 전환 및 실행

```bash
# Plan 단계로 전환
curl -X POST http://localhost:8000/projects/prj_abc123/plan \
  -H "X-API-Key: $OPSCLAW_API_KEY"

# Execute 단계로 전환
curl -X POST http://localhost:8000/projects/prj_abc123/execute \
  -H "X-API-Key: $OPSCLAW_API_KEY"

# 다중 태스크 병렬 실행
curl -X POST http://localhost:8000/projects/prj_abc123/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {"order":1, "instruction_prompt":"nft list ruleset",
       "risk_level":"low", "subagent_url":"http://192.168.208.150:8002"},
      {"order":2, "instruction_prompt":"nft list chain inet filter input",
       "risk_level":"low", "subagent_url":"http://192.168.208.150:8002"},
      {"order":3, "instruction_prompt":"ss -tlnp | grep 22",
       "risk_level":"low", "subagent_url":"http://192.168.208.150:8002"}
    ],
    "subagent_url": "http://localhost:8002"
  }'
```

### 4.5.3 증적 확인 및 검증

```bash
# Evidence 요약
curl -H "X-API-Key: $OPSCLAW_API_KEY" \
  http://localhost:8000/projects/prj_abc123/evidence/summary

# PoW 체인 무결성 검증
curl "http://localhost:8000/pow/verify?agent_id=http://192.168.208.150:8002" \
  -H "X-API-Key: $OPSCLAW_API_KEY"
# → {"valid": true, "blocks": 3, "orphans": 0, "tampered": []}

# 실행 Replay
curl http://localhost:8000/projects/prj_abc123/replay \
  -H "X-API-Key: $OPSCLAW_API_KEY"
# → 시간순 전체 실행 이력
```

### 4.5.4 완료 보고서

교육 세션 종료 시 완료 보고서를 생성하여 학습 기록을 정리한다:

```bash
curl -X POST http://localhost:8000/projects/prj_abc123/completion-report \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "summary": "nftables 기초 실습 완료",
    "outcome": "success",
    "work_details": [
      "nft list ruleset로 현재 룰셋 확인",
      "input 체인에서 SSH 허용 룰 확인",
      "CTF flag 획득: opsclaw{nft_input_ssh_accept}"
    ]
  }'
```
