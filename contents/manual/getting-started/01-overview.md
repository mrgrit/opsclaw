# OpsClaw 개요

> **문서 버전**: 1.0 | **최종 수정**: 2026-03-30

---

## OpsClaw란 무엇인가

OpsClaw는 IT 운영과 보안 자동화를 위한 **Control-Plane 플랫폼**이다.
여러 서버에 분산된 운영 작업(서버 점검, 패키지 관리, 보안 감사, 사고 대응 등)을
하나의 통합 API를 통해 계획, 실행, 기록, 분석하는 것이 핵심 목적이다.

OpsClaw의 핵심 특징:

- **자연어 → 자동 실행**: "v-secu 방화벽 점검해줘"라고 입력하면, LLM이 작업 계획을 수립하고 원격 서버에서 실행한다
- **증거 기반 운영**: 모든 실행 결과는 Evidence(증거)로 기록되며, PoW(Proof-of-Work) 블록체인으로 무결성을 보장한다
- **강화학습 최적화**: 과거 작업 결과를 Q-learning으로 학습하여 최적 위험도(risk_level)를 자동 추천한다
- **이중 모드**: 내장 LLM(Native)과 외부 AI(Claude Code) 두 가지 모드를 지원한다
- **분산 실행**: 방화벽, 웹 서버, SIEM 등 역할별 서버에 SubAgent를 배포하여 원격 명령을 실행한다

---

## 핵심 개념

### Project (프로젝트)

작업의 기본 단위. 하나의 요청(request)이 하나의 프로젝트가 된다.

- 생성 → 계획(plan) → 실행(execute) → 완료보고(completion-report) → 종료(close)의 라이프사이클을 가진다
- 프로젝트 ID 형식: `prj_` + UUID (예: `prj_a1b2c3d4e5f6`)
- 모든 Evidence, PoW, Replay가 프로젝트 단위로 관리된다

### Evidence (증거)

실행 결과의 기록물. 명령의 stdout, stderr, exit_code, 실행 시간이 자동으로 저장된다.

- `execute-plan` 또는 `dispatch`를 통해 명령이 실행될 때마다 자동 생성
- 프로젝트별로 조회 가능: `GET /projects/{id}/evidence`
- 성공률, 실행 시간 등의 요약 통계 제공: `GET /projects/{id}/evidence/summary`

### Proof-of-Work (PoW)

Evidence의 무결성을 보장하는 블록체인 메커니즘.

- 각 Evidence에 대해 SHA-256 해시를 계산하고, 난이도(difficulty) 조건을 만족하는 nonce를 채굴한다
- 이전 블록의 해시를 참조하여 체인을 형성한다 (linked-list 구조)
- 위변조 시 체인 검증(`/pow/verify`)에서 즉시 감지된다
- `execute-plan` 실행 시 자동으로 PoW 블록이 생성된다 (별도 호출 불필요)

### SubAgent (서브에이전트)

실제 명령을 실행하는 원격 에이전트. 각 서버에 하나씩 배포된다.

- 포트 8002에서 실행된다
- Manager API를 통해서만 호출된다 (직접 호출 금지)
- Tool(단일 명령)과 Skill(Tool 조합 절차)을 실행할 수 있다
- `/health` 엔드포인트로 상태를 확인한다

### Playbook (플레이북)

반복 가능한 작업 절차를 정의하는 템플릿.

- Step 단위로 구성된다 (Tool 또는 Skill 호출)
- 버전 관리를 지원한다
- 프로젝트에 연결하여 실행할 수 있다
- 예시: "서버 온보딩", "TLS 인증서 갱신", "보안 점검"

### Reward (보상) & RL (강화학습)

작업 성과에 따른 보상과 학습 메커니즘.

- 성공한 태스크에 보상이 자동 지급된다
- 누적 보상으로 에이전트 랭킹이 산출된다 (`/pow/leaderboard`)
- Q-learning으로 risk_level 최적화 정책을 학습한다 (`/rl/train`)

---

## 시스템 아키텍처

```
                          ┌──────────────────────────────────┐
                          │         사용자 / 운영자           │
                          └──────────┬───────────────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
              ┌─────▼─────┐   ┌─────▼─────┐   ┌─────▼─────┐
              │  OpsClaw   │   │  Claude   │   │  Web UI   │
              │    CLI     │   │   Code    │   │ (React)   │
              └─────┬──────┘   └─────┬──────┘   └─────┬─────┘
                    │                │                │
         ┌──────────────────────────────────────────────────┐
         │                                                  │
   ┌─────▼──────┐                                    ┌──────▼──────┐
   │  Master    │◄──── Mode A (Native)               │  Manager    │
   │  Service   │      LLM 계획 수립                  │    API      │
   │  :8001     │                                    │   :8000     │
   └────────────┘                                    └──────┬──────┘
                                                            │
                            Mode B (External)               │
                            Claude Code가 직접 호출 ────────►│
                                                            │
                  ┌─────────────────┬───────────────────────┤
                  │                 │                       │
           ┌──────▼──────┐  ┌──────▼──────┐  ┌────────────▼──────┐
           │  SubAgent   │  │  SubAgent   │  │    SubAgent       │
           │  opsclaw    │  │  secu       │  │    web / siem     │
           │  :8002      │  │  :8002      │  │    :8002          │
           └─────────────┘  └─────────────┘  └───────────────────┘
                  │                 │                       │
           ┌─────▼─────┐   ┌──────▼──────┐  ┌────────────▼──────┐
           │ localhost  │   │  nftables   │  │  Apache / Wazuh   │
           │ PostgreSQL │   │  Suricata   │  │  JuiceShop        │
           └───────────┘   └─────────────┘  └───────────────────┘
```

### 3계층 구조 상세

| 계층 | 구성 요소 | 역할 | 직접 접근 |
|------|-----------|------|-----------|
| **1층: Master** | Master Service(:8001) 또는 Claude Code | 자연어 분석, 작업 계획 수립, 결과 해석 | 사용자가 직접 호출 |
| **2층: Manager** | Manager API(:8000) | 상태 관리, 인증, Evidence 기록, PoW, SubAgent dispatch | Master 또는 CLI가 호출 |
| **3층: SubAgent** | SubAgent Runtime(:8002) | 실제 shell 명령 실행, 파일 조작, 서비스 제어 | Manager만 호출 가능 |

---

## 두 가지 실행 모드

### Mode A: Native (내장 LLM)

```
사용자 → CLI(opsclaw run) → Master(:8001) → Ollama LLM → 작업계획
                                                            ↓
                              Manager(:8000) ← tasks 배열 전달
                                   ↓
                              SubAgent(:8002) → 명령 실행
                                   ↓
                              Evidence + PoW 자동 기록
```

- OpsClaw 내장 LLM(Ollama)이 사용자 요청을 분석하고 작업 계획(tasks 배열)을 자동 생성
- CLI 한 줄로 전체 워크플로우가 자동 진행
- 소규모 LLM(8B~120B)을 사용하므로 복잡한 판단에는 한계가 있음
- **적합한 경우**: 표준화된 반복 작업, 단순 상태 점검, Playbook 기반 실행

### Mode B: Claude Code (외부 AI)

```
사용자 → Claude Code → curl로 Manager API 직접 호출
                              ↓
                        Manager(:8000) → SubAgent(:8002) → 명령 실행
                              ↓
                        Evidence + PoW 자동 기록
                              ↓
                  Claude Code가 결과를 분석하고 다음 단계 결정
```

- Claude Code가 Manager API를 직접 호출하며 전체 워크플로우를 주도
- 대형 LLM(Claude)의 추론 능력을 활용하여 복잡한 판단 가능
- 실행 결과를 분석하고 동적으로 다음 작업을 결정
- **적합한 경우**: 복잡한 사고 대응, 다단계 보안 감사, 동적 판단이 필요한 작업

---

## 등록된 Tool과 Skill

### Tool (단일 명령 단위)

| Tool | 설명 | 주요 파라미터 |
|------|------|--------------|
| `run_command` | 임의의 shell 명령 실행 | `command` |
| `fetch_log` | 로그 파일 조회 | `log_path`, `lines` |
| `query_metric` | CPU/메모리/디스크/네트워크 현황 수집 | (없음) |
| `read_file` | 파일 내용 읽기 | `path` |
| `write_file` | 파일 쓰기 | `path`, `content` |
| `restart_service` | systemctl 서비스 재시작 | `service` |

### Skill (Tool 조합 절차)

| Skill | 설명 |
|-------|------|
| `probe_linux_host` | hostname, uptime, 커널, 디스크, 메모리, 프로세스, 포트 종합 수집 |
| `check_tls_cert` | TLS 인증서 유효기간 및 발급자 확인 |
| `collect_web_latency_facts` | HTTP 응답 시간 3회 측정 |
| `monitor_disk_growth` | 디렉토리 디스크 사용량 추세 분석 |
| `summarize_incident_timeline` | 시스템 오류 로그 타임라인 요약 |
| `analyze_wazuh_alert_burst` | Wazuh 보안 알림 급증 원인 분석 |

---

## 인프라 구성

### 물리 서버 (운영 환경)

| 서버 | IP | 역할 | SubAgent URL |
|------|----|------|--------------|
| **opsclaw** | 192.168.208.142 | Control Plane — Manager, Master, SubAgent, PostgreSQL | http://localhost:8002 |
| **secu** | 192.168.208.150 | 네트워크 보안 — nftables 방화벽, Suricata IPS | http://192.168.208.150:8002 |
| **web** | 192.168.208.151 | 웹 서비스 — BunkerWeb WAF, JuiceShop 취약 앱 | http://192.168.208.151:8002 |
| **siem** | 192.168.208.152 | 보안 모니터링 — Wazuh 4.11.2 SIEM | http://192.168.208.152:8002 |
| **dgx-spark** | 192.168.0.105 | GPU 연산 — Ollama LLM 추론 엔진 | http://192.168.0.105:8002 |

### 가상 서버 (교육/실습 환경)

| 서버 | IP | 역할 | CLI 별명 |
|------|----|------|----------|
| **v-secu** | 192.168.0.108 | 가상 방화벽/IPS | `v-secu` |
| **v-web** | 192.168.0.110 | 가상 웹 서버 | `v-web` |
| **v-siem** | 192.168.0.109 | 가상 SIEM | `v-siem` |

---

## 이 매뉴얼의 대상 독자

### SOC 분석가 (Security Operations Center)

- Wazuh 알림 분석 자동화
- 보안 사고 타임라인 자동 수집
- 방화벽/IDS 규칙 점검

### 보안 엔지니어

- 서버 보안 감사 자동화 (TLS, 패치, 계정 관리)
- 침투 테스트 자동화 (Purple Team)
- PoW 기반 작업 무결성 검증

### DevOps 엔지니어

- 서버 온보딩 자동화
- 패키지 관리, 서비스 재시작
- 모니터링/알림 설정

### 정보보안 전공 학생

- 8개 교육과정(네트워크, 시스템, 웹, 클라우드 보안 등)
- CTFd 실습 문제
- 실제 인프라에서의 보안 운영 실습

---

## 주요 기술 스택

| 구성 요소 | 기술 | 버전 |
|-----------|------|------|
| 백엔드 프레임워크 | FastAPI + Uvicorn | Python 3.11 |
| 데이터베이스 | PostgreSQL | 15 (Docker) |
| 워크플로우 엔진 | LangGraph | 상태 머신 기반 |
| LLM 추론 | Ollama | gpt-oss:120b, qwen3:8b, gemma3:12b |
| 외부 AI | Claude Code | Anthropic Claude |
| 컨테이너 | Docker / Docker Compose | 최신 |
| 보안 도구 | nftables, Suricata, Wazuh, BunkerWeb | 각 최신 |

---

## 다음 단계

- **설치**: [02-installation.md](02-installation.md) 에서 환경 구축 방법을 확인한다
- **빠른 시작**: [03-quickstart.md](03-quickstart.md) 에서 5분 안에 첫 프로젝트를 실행한다
- **Native 모드**: [../native-mode/01-overview.md](../native-mode/01-overview.md)
- **Claude Code 모드**: [../claude-code-mode/01-overview.md](../claude-code-mode/01-overview.md)
