# 3. 두 패러다임 (Two Paradigms)

## 3.1 클라이언트 하네스: Claude Code

Claude Code는 Anthropic이 제공하는 CLI 기반 에이전틱 코딩 도구이다. LLM(Claude)이 사용자의 로컬 환경에서 도구를 직접 호출하여 작업을 수행한다.

### 3.1.1 도구 (Tools)

30개 이상의 내장 도구를 제공한다:

| 카테고리 | 도구 | 역할 |
|---------|------|------|
| 파일 I/O | Read, Write, Edit | 파일 읽기/쓰기/수정 |
| 코드 검색 | Grep, Glob | 정규식 검색, 파일 패턴 매칭 |
| 셸 실행 | Bash | OS 명령 실행 |
| 웹 접근 | WebFetch, WebSearch | HTTP 요청, 웹 검색 |
| 에이전트 | Agent | 서브에이전트 위임 |
| 태스크 | TaskCreate, TaskUpdate, TaskList | 작업 추적 |
| 스케줄링 | CronCreate, CronDelete | 반복 실행 |

LLM이 매 턴(turn)마다 어떤 도구를 호출할지 자율적으로 결정한다. 한 턴에 여러 도구를 병렬 호출할 수 있다.

### 3.1.2 스킬 (Skills)

스킬은 재사용 가능한 프롬프트 워크플로이다. YAML 프론트매터로 정의한다:

```yaml
---
name: security-scan
description: 서버 보안 점검
allowed-tools: Bash, Read, Grep
---
대상 서버에 접속하여 다음을 점검하라:
1. 열린 포트 확인 (ss -tlnp)
2. sudo 권한 확인 (sudo -l)
3. 패스워드 정책 (grep PASS_MAX /etc/login.defs)
결과를 보안 보고서로 정리하라.
```

스킬은 `/security-scan`으로 호출하며, LLM이 스킬의 지시를 해석하여 도구를 선택하고 실행한다. **동일 스킬을 호출해도 LLM이 매번 다른 도구 조합/순서를 선택할 수 있다** — 이것이 비결정론의 원인이다.

### 3.1.3 훅 (Hooks)

훅은 LLM의 도구 호출 전후에 자동 실행되는 **결정론적 로직**이다:

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Bash",
      "hooks": [{"type": "command", "command": "echo '[LOG] $(date): Bash executed' >> /tmp/audit.log"}]
    }]
  }
}
```

25개 이상의 이벤트(SessionStart, PreToolUse, PostToolUse, FileChanged 등)에 훅을 걸 수 있으며, 4가지 유형(command, prompt, agent, http)을 지원한다. 훅은 LLM이 아닌 **하네스가 결정론적으로 실행**한다.

### 3.1.4 메모리

두 가지 메모리 메커니즘이 존재한다:

**CLAUDE.md (영구 지시):** 프로젝트 루트에 위치하며, 세션 시작 시 자동 로딩된다. 개발 규칙, 아키텍처 설명, 커밋 규칙 등을 포함한다. Git에 커밋하여 팀 공유가 가능하다.

**auto-memory (자동 학습):** Claude가 대화 중 중요하다고 판단한 정보를 `~/.claude/projects/<project>/memory/`에 저장한다. 사용자 선호, 프로젝트 상태, 피드백 등이 축적된다. 머신 로컬이며 세션 간 유지된다.

### 3.1.5 권한 모델

도구 수준의 세밀한 권한 제어를 제공한다:

```
allow: ["Bash(npm run build)", "Read(/src/**/*.ts)"]
deny: ["Edit(/.env)", "Bash(rm -rf *)"]
```

`deny > ask > allow` 우선순위로 평가되며, 정규식과 글롭 패턴을 지원한다. `auto` 모드에서는 안전 분류기가 자동으로 허용/거부를 판단한다.

---

## 3.2 서버 하네스: OpsClaw

OpsClaw는 IT 운영·보안 자동화를 위한 서버 사이드 오케스트레이션 플랫폼이다. Master→Manager→SubAgent 3계층 위임 아키텍처를 채택한다.

### 3.2.1 도구 (Tools)

6개의 등록 도구를 제공한다:

| 도구 | 역할 | 필수 파라미터 |
|------|------|------------|
| run_command | 셸 명령 실행 | command |
| fetch_log | 로그 파일 조회 | log_path, lines |
| query_metric | 시스템 메트릭 수집 | — |
| read_file | 파일 읽기 | path |
| write_file | 파일 쓰기 | path, content |
| restart_service | 서비스 재시작 | service |

도구는 PostgreSQL `tools` 테이블에 등록되며, 각 도구에 risk_level이 지정된다.

### 3.2.2 스킬과 플레이북 (Skills & Playbooks)

**스킬:** 도구를 조합한 재사용 가능한 능력. `probe_linux_host`는 hostname, uptime, 디스크, 메모리, 프로세스를 종합 수집하는 스킬로, 내부적으로 `run_command`를 여러 번 호출한다.

**플레이북:** 스킬과 도구를 순서화한 절차. 각 단계(step)의 파라미터가 결정론적으로 바인딩되어, **동일 플레이북은 항상 동일한 명령을 생성**한다. 이것이 클라이언트 하네스의 비결정론과의 핵심 차이이다.

### 3.2.3 메모리 (4-Layer)

```
Layer 1: Evidence (원시 기록) — 태스크 실행 즉시 기록
Layer 2: Task Memory (구조화 요약) — 프로젝트 종료 시 집계
Layer 3: Experience (의미적 지식) — 고보상 태스크 자동 승급
Layer 4: Retrieval (검색 인덱스) — RAG 기반 컨텍스트 주입
```

모든 메모리는 PostgreSQL에 영구 저장되며, 어떤 세션에서든 API로 조회 가능하다.

### 3.2.4 피드백 루프 (PoW + RL)

각 태스크 실행 시 자동으로:
1. **PoW 블록** 생성 (SHA-256 해시 체인)
2. **보상(reward)** 산출 (base ± speed_bonus ± risk_penalty)
3. **RL 정책** 학습 (Q-learning + UCB1)

이를 통해 "어떤 위험도의 태스크를 어떤 에이전트에 할당할 때 가장 좋은 결과를 얻는가?"를 자율적으로 학습한다.

---

## 3.3 공통점과 근본적 차이

### 공통점

| 측면 | Claude Code | OpsClaw |
|------|-----------|---------|
| LLM 기반 | Claude (Opus/Sonnet) | Claude (External Master) 또는 Ollama |
| 도구 호출 | 30+ 내장 도구 | 6 등록 도구 + SubAgent |
| 재사용 단위 | Skills (프롬프트) | Skills + Playbooks (선언적) |
| 메모리 | CLAUDE.md + auto-memory | 4-Layer DB |
| 확장 가능 | MCP 서버, 커스텀 스킬 | 새 Tool/Skill/Playbook 등록 |

### 근본적 차이

```
                    클라이언트 하네스          서버 하네스
실행 위치:          사용자 머신               서버 (Control Plane)
실행 주체:          LLM이 자율 결정           Master가 계획, Manager가 중재
메모리 범위:        머신 로컬                 서버 중앙 (팀 공유)
증적:               세션 로그 (휘발)          DB 영구 기록 (PoW 해시 체인)
재현성:             비결정론 (LLM 의존)       결정론 (Playbook)
학습:               auto-memory (정성적)      RL reward (정량적)
권한:               도구 수준 (세밀)          태스크 수준 (리스크 기반)
```

**핵심 차이를 한 문장으로:** 클라이언트 하네스는 **"LLM이 자유롭게 도구를 사용하되, 위험한 행동은 제한"**하고, 서버 하네스는 **"Master가 계획을 수립하고, Manager가 증적과 보상을 관리하며, SubAgent가 실행"**한다.
