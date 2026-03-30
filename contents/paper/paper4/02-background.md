# 2. 배경 및 정의 (Background & Definitions)

## 2.1 에이전트 하네스란?

에이전트 하네스(agent harness)는 LLM 에이전트의 실행을 **관리, 제어, 기록**하는 프레임워크이다. "하네스"라는 용어는 말의 고삐(harness)에서 유래하며, 강력한 에이전트의 행동을 원하는 방향으로 이끌고 제어한다는 의미이다.

하네스가 없는 단독 에이전트(standalone agent)는:
- 어떤 도구든 자유롭게 사용 (제어 부재)
- 실행 기록이 세션 로그에만 의존 (기록 부재)
- 과거 경험을 컨텍스트 윈도우 내에서만 참조 (학습 부재)

하네스가 제공하는 가치:

```
┌──────────────────────────────────────────────┐
│                Agent Harness                  │
│                                              │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐    │
│  │ 도구  │  │ 스킬  │  │ 메모리│  │ 권한  │    │
│  │ Tools │  │Skills │  │Memory│  │Perms │    │
│  └──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘    │
│     │         │         │         │          │
│     └─────────┴─────────┴─────────┘          │
│                    │                          │
│              ┌─────┴─────┐                    │
│              │  LLM Agent │                    │
│              │ (Claude,   │                    │
│              │  GPT, etc) │                    │
│              └───────────┘                    │
│                                              │
│  ┌──────┐  ┌──────┐  ┌──────┐               │
│  │ 증적  │  │피드백 │  │스케줄│               │
│  │Evid. │  │Reward│  │Sched │               │
│  └──────┘  └──────┘  └──────┘               │
└──────────────────────────────────────────────┘
```

## 2.2 클라이언트 하네스 vs 서버 하네스

### 클라이언트 하네스 (Client-Side Harness)

사용자의 로컬 머신에서 동작한다. LLM이 파일시스템, 터미널, 브라우저 등에 직접 접근하며, 사용자와 대화하면서 자율적으로 도구를 선택하고 실행한다.

```
┌─ 사용자 머신 ──────────────────────┐
│                                    │
│  ┌──────────────────┐              │
│  │  Claude Code CLI │              │
│  │  ┌────────────┐  │              │
│  │  │ LLM (Claude)│  │              │
│  │  └──────┬─────┘  │              │
│  │         │         │              │
│  │  ┌──────┴──────┐  │              │
│  │  │ Tools:      │  │              │
│  │  │ Read, Write │  │  ┌────────┐ │
│  │  │ Bash, Grep  │──┼──│파일시스템│ │
│  │  │ Agent, Web  │  │  │터미널   │ │
│  │  └─────────────┘  │  └────────┘ │
│  │                    │              │
│  │  ┌─────────────┐  │              │
│  │  │ Memory:     │  │              │
│  │  │ CLAUDE.md   │  │              │
│  │  │ auto-memory │  │              │
│  │  └─────────────┘  │              │
│  └──────────────────┘              │
└────────────────────────────────────┘
```

**특징:**
- LLM이 실행 판단의 주체 (에이전틱 루프)
- 30+ 내장 도구에 직접 접근
- 세션 기반 메모리 + 파일 기반 영구 메모리
- 사용자와 실시간 대화하면서 작업 수행
- 권한은 도구 수준에서 세밀하게 제어

### 서버 하네스 (Server-Side Harness)

서버 사이드 API가 실행을 중재한다. Master(LLM)가 계획을 수립하고, Manager(API)가 상태를 관리하며, SubAgent(런타임)가 대상 서버에서 명령을 실행한다.

```
┌─ Control Plane ────────────────────────┐
│                                        │
│  ┌──────────┐   ┌──────────────────┐   │
│  │  Master  │   │   Manager API    │   │
│  │  (LLM)   │──▶│  - 프로젝트 관리  │   │
│  │          │   │  - 증적 기록      │   │
│  └──────────┘   │  - PoW/Reward    │   │
│                  │  - RL 정책       │   │
│                  └────────┬─────────┘   │
│                           │             │
└───────────────────────────┼─────────────┘
                            │
              ┌─────────────┼────────────┐
              │             │            │
        ┌─────┴──┐   ┌─────┴──┐   ┌─────┴──┐
        │SubAgent│   │SubAgent│   │SubAgent│
        │ secu   │   │  web   │   │  siem  │
        │ :8002  │   │ :8002  │   │ :8002  │
        └────────┘   └────────┘   └────────┘
```

**특징:**
- Master가 계획, Manager가 중재, SubAgent가 실행 (3계층 위임)
- 모든 실행이 DB에 영구 기록 (evidence + PoW)
- 보상(reward)과 강화학습으로 정책 자율 개선
- Playbook으로 결정론적 재현
- 태스크 수준 리스크 거버넌스 (critical → dry_run 강제)

## 2.3 관련 연구

### LLM 에이전트 프레임워크
MetaGPT [5]는 SOP를 다중 에이전트 워크플로에 인코딩하여 역할 기반 협업을 구현한다. CAMEL [6]은 두 에이전트의 역할극을 통한 자율 협업을 제안한다. 이들은 "에이전트 간 협업"에 초점을 맞추며, 하네스의 제어·기록·학습 측면은 다루지 않는다.

### 코딩 에이전트
SWE-bench [7]와 SWE-agent [8]는 GitHub 이슈를 자동으로 해결하는 에이전트를 벤치마킹한다. Devin [9]은 종합 소프트웨어 엔지니어 에이전트를 제안한다. 이들은 코딩 작업에 특화되어 있으며, IT 운영/보안 작업의 하네스와는 범위가 다르다.

### IT 운영 자동화
Ansible [10]과 Terraform [11]은 IaC(Infrastructure as Code) 도구로 결정론적 실행을 보장하지만, LLM 기반 동적 계획이 불가능하다. CALDERA [4]는 ATT&CK 기반 자동화 공격 에뮬레이션을 제공하지만, 방어 자동화와 경험 학습은 지원하지 않는다.

### 본 연구의 위치

**표 1. 기존 연구와의 위치 비교**

| | 클라이언트 | 서버 | 하네스 비교 |
|---|:---:|:---:|:---:|
| MetaGPT, CAMEL | | ✓ (협업) | |
| SWE-bench, Devin | ✓ (코딩) | | |
| Ansible, CALDERA | | ✓ (운영) | |
| Claude Code | ✓ | | |
| OpsClaw | | ✓ | |
| **본 연구** | **✓** | **✓** | **✓** |

---

## References

[5] S. Hong et al., "MetaGPT: Meta Programming for a Multi-Agent Collaborative Framework," *Proc. ICLR*, 2024.

[6] G. Li et al., "CAMEL: Communicative Agents for 'Mind' Exploration of Large Language Model Society," *Proc. NeurIPS*, 2023.

[7] C. E. Jimenez et al., "SWE-bench: Can Language Models Resolve Real-World GitHub Issues?," *Proc. ICLR*, 2024.

[8] J. Yang et al., "SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering," *arXiv:2405.15793*, 2024.

[9] Cognition, "Devin: The First AI Software Engineer," 2024.

[10] Red Hat, "Ansible: Simple IT Automation," https://www.ansible.com, 2024.

[11] HashiCorp, "Terraform: Infrastructure as Code," https://www.terraform.io, 2024.
