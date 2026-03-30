# 4. 비교 프레임워크 (Comparison Framework)

본 장에서는 두 패러다임을 10개 차원에서 체계적으로 비교한다.

## 표 2. 10차원 비교 프레임워크

| # | 차원 | Client Harness (Claude Code) | Server Harness (OpsClaw) | 핵심 차이 |
|---|------|-----|------|------|
| D1 | **도구 (Tools)** | 30+ 내장, 런타임 발견, MCP 확장 | 6개 등록, PostgreSQL 관리 | 범위 vs 통제 |
| D2 | **스킬 (Skills)** | 프롬프트 기반 워크플로, LLM이 해석 | 도구 체인 템플릿, 파라미터 바인딩 | 유연성 vs 결정론 |
| D3 | **훅 (Hooks)** | 25+ 라이프사이클 이벤트, 4가지 타입 | 웹훅 알림, 서버 이벤트 | 로컬 자동화 vs 알림 |
| D4 | **메모리** | CLAUDE.md + auto-memory, 머신 로컬 | 4-Layer DB, 서버 중앙 | 개인 vs 공유 |
| D5 | **서브에이전트** | 대화형 전문가, 다수/세션, 격리 컨텍스트 | 상태 없는 실행기, 1개/서버 | 자율성 vs 단순성 |
| D6 | **태스크 추적** | 인메모리 (세션 스코프), 의존성 | PostgreSQL (영구), 프로젝트 라이프사이클 | 휘발 vs 영구 |
| D7 | **권한 관리** | 도구 수준 패턴 매칭 (deny/allow/ask) | 태스크 수준 리스크 (low~critical) | 세밀 vs 거버넌스 |
| D8 | **스케줄링** | /loop(세션), Cloud(영구), Cron | scheduler-worker 데몬 (영구) | 세션 의존 vs 독립 |
| D9 | **피드백 루프** | 훅(결정론) + auto-memory(학습) | PoW + Reward + RL(Q-learning) | 정성적 vs 정량적 |
| D10 | **실행 모델** | 에이전틱 루프 (LLM → Tool → LLM → ...) | 3계층 위임 (Master → Manager → SubAgent) | 대화형 vs 선언적 |

---

## D1: 도구 (Tools)

**Claude Code:** 파일 읽기/쓰기, 코드 검색, 셸 실행, 웹 접근, 에이전트 위임 등 **30개 이상**의 도구를 내장한다. MCP(Model Context Protocol) 서버를 통해 외부 도구(GitHub, Jira, Slack 등)도 연결할 수 있다. 도구는 런타임에 자동 발견된다.

**OpsClaw:** `run_command`, `fetch_log`, `query_metric`, `read_file`, `write_file`, `restart_service`의 **6개 핵심 도구**를 등록한다. 도구는 PostgreSQL에 사전 등록되며, 각 도구에 risk_level이 지정된다.

**분석:** Claude Code는 **넓은 도구 범위**로 다양한 작업을 자율적으로 수행한다. OpsClaw는 **좁지만 통제된 도구 셋**으로 인프라 운영에 특화되며, 도구 사용의 리스크를 명시적으로 관리한다.

## D2: 스킬 (Skills) / 플레이북 (Playbooks)

**Claude Code Skill:** 프롬프트 텍스트를 LLM에 주입하여 워크플로를 유도한다. LLM이 프롬프트를 해석하여 어떤 도구를 어떤 순서로 호출할지 자율 결정한다. 따라서 **동일 스킬을 호출해도 매번 다른 실행 경로**가 나올 수 있다.

**OpsClaw Playbook:** 각 단계(step)의 도구, 파라미터가 명시적으로 바인딩된다. `resolve_step_script()`가 파라미터를 결정론적으로 생성하여, **동일 플레이북은 항상 동일한 명령**을 생성한다.

**분석:** Claude Code 스킬은 **유연하지만 비결정론적**, OpsClaw 플레이북은 **경직되지만 100% 재현 가능**. 새로운 상황에 대한 적응은 스킬이 유리하고, 반복 운영의 일관성은 플레이북이 유리하다.

## D3: 훅 (Hooks)

**Claude Code:** SessionStart, PreToolUse, PostToolUse, FileChanged 등 25+ 이벤트에 command/prompt/agent/http 훅을 설정할 수 있다. 훅은 LLM이 아닌 **하네스가 결정론적으로 실행**한다. 예: Bash 실행 후 자동 린팅, 파일 변경 시 자동 테스트.

**OpsClaw:** 웹훅 알림(Slack, Email)과 서버 이벤트(evidence 기록, PoW 생성)를 지원하지만, 클라이언트 사이드 자동화는 없다.

**분석:** Claude Code 훅은 **개발자 워크플로 자동화**에 강력하다. OpsClaw는 서버 사이드 **감사·알림**에 초점을 맞추며, 로컬 자동화는 Master(Claude Code)가 담당한다.

## D4: 메모리

**Claude Code:** CLAUDE.md(영구 지시, Git 커밋)와 auto-memory(자동 학습, 머신 로컬)의 2계층. 세션 간 유지되지만 **특정 머신에 종속**되며, 팀 공유는 CLAUDE.md의 Git 커밋에 의존한다.

**OpsClaw:** Evidence → Task Memory → Experience → Retrieval의 4계층. 모든 메모리가 PostgreSQL에 **중앙 저장**되어, 어떤 세션·어떤 SubAgent에서든 API로 조회 가능하다. 고보상 태스크는 자동으로 경험(Experience)으로 승급된다.

**분석:** Claude Code 메모리는 **개인 개발자에 최적화**, OpsClaw 메모리는 **팀/조직 단위 지식 공유에 최적화**.

## D5~D10: 나머지 차원

(이하 각 차원도 동일한 구조로 상세 비교 — 지면 관계상 핵심 차이만 요약)

| 차원 | Client 강점 | Server 강점 |
|------|-----------|-----------|
| D5 서브에이전트 | 다양한 전문가 에이전트를 동적 생성 | 서버별 고정 배치로 안정성 확보 |
| D6 태스크 추적 | 세션 내 빠른 추적, 의존성 체인 | 영구 저장, 감사 추적, replay |
| D7 권한 | 도구별 세밀한 allow/deny 패턴 | critical→dry_run 자동 강제 |
| D8 스케줄링 | 세션 기반 빠른 설정, 클라우드 옵션 | 독립 데몬, 서버 재시작에도 유지 |
| D9 피드백 | 훅으로 즉각적 자동 반응 | RL 보상으로 장기적 정책 최적화 |
| D10 실행 모델 | 대화형 (사용자와 실시간 조율) | 선언적 (API 호출로 일괄 실행) |
