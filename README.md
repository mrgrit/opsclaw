# OpsClaw

## 1. 한 줄 정의

**OpsClaw는 사용자가 자연어로 목표만 말하면, 시스템이 필요한 사실을 스스로 확인(Probe)하고, 증거 기반으로 계획·실행·검증·재계획을 반복하며, Tool / Skill / Experience를 누적해 점점 더 잘 일하는 범용 IT 오케스트레이션 에이전트 플랫폼이다.**

OpsClaw는 특정 제품 설치기나 보안 전용 자동화 스크립트가 아니다. Suricata 설치, 서비스 장애 복구, 시스템 운영 자동화, 파일 정리, 보안 점검, 방화벽 정책 변경, 로그 파이프라인 추적, 리포트 생성, 이메일 처리 같은 여러 업무를 하나의 공통 실행 루프로 다루는 것을 목표로 한다.

---

## 2. OpsClaw가 **아닌 것**

OpsClaw를 정확히 이해하려면 먼저 “무엇이 아닌가”를 분명히 해야 한다.

### 2.1 특정 제품 설치 프로그램이 아니다
- Suricata 설치만 잘하는 프로그램이 아니다.
- 방화벽 룰만 적용하는 도구도 아니다.
- 장애 분석만 하는 진단기만도 아니다.

### 2.2 고정 플레이북 실행기에서 멈추지 않는다
- 미리 만들어진 Playbook만 실행하는 시스템으로 끝나지 않는다.
- Playbook은 여전히 중요하지만, 최종 지향점은 자연어 목표 → Probe → Evidence → Decision → Execution → Validation → Replan의 범용 루프다.

### 2.3 단순 챗봇이 아니다
- “대화형 답변”이 목적이 아니다.
- 실제 시스템 확인, 실제 명령 실행, 실제 증빙 수집, 실제 상태 저장이 목적이다.

### 2.4 완전 즉흥형 LLM 실행기만도 아니다
- 아무 제어 없이 LLM이 즉석에서 명령을 만들어 실행하는 구조는 재현성·안전성·감사 측면에서 위험하다.
- 그래서 OpsClaw는 Tool / Skill / Evidence / Audit / Policy / Approval을 갖는 하이브리드 구조를 지향한다.

---

## 3. 왜 OpsClaw가 필요한가

운영 자동화가 실제 현장에서 실패하는 이유는 대체로 비슷하다.

- 자동화는 되지만 **왜 그렇게 했는지 설명이 안 된다**.
- 실행은 되지만 **감사·증빙이 남지 않는다**.
- 한 번 잘 되더라도 **재현성이 없다**.
- 운영 환경의 작은 차이 때문에 **Playbook 하드코딩이 쉽게 깨진다**.
- 도구가 없으면 사람이 직접 검색·설치·학습해야 해서 **자동화가 멈춘다**.
- 위험한 조치는 무작정 자동화하면 안 되는데, 기존 시스템은 **승인/정책/롤백 모델이 약하다**.

OpsClaw는 이 문제를 다음 방식으로 해결하려 한다.

1. **자연어 목표 수신**
2. **Unknown/모호성 식별**
3. **Probe 설계 및 실행**
4. **Evidence 기반 의사결정**
5. **Tool/Skill 실행**
6. **Validate / Fix / Retry / Replan**
7. **State / Audit / Evidence 축적**
8. **Experience 축적을 통한 장기적 자동화 향상**

---

## 4. 핵심 컨셉

## 4.1 Goal-driven orchestration
사용자는 “무엇을 하고 싶은지”만 말한다.

예:
- “웹이 갑자기 느려졌어. 원인 찾아서 복구해.”
- “신규 서버 5대 기본 셋업해.”
- “로그 파이프라인이 어디서 끊겼는지 찾아.”
- “이번 주 장애/변경/승인 내역을 보고서로 만들어.”
- “이메일 읽고 요약하고, 중요하지 않은 건 초안 답장 만들어.”

OpsClaw는 이 목표를 실행 가능한 흐름으로 바꾼다.

## 4.2 Guess가 아니라 Probe
LLM은 추측하면 안 된다.

- 알 수 있는 것은 시스템에 직접 물어본다.
- 모호하면 추가 probe를 만든다.
- 그래도 판단 불가면 human에게 질문한다.

즉 OpsClaw의 기본 철학은:

**“추측보다 확인, 확인보다 증거, 증거보다 안전”**

## 4.3 Human은 최소 개입
사람은 아무 것도 모르는 존재가 아니라, **시스템이 알 수 없는 것**과 **위험한 결정**을 담당한다.

### 시스템이 직접 확인할 것
- OS / distro / pkg manager
- 서비스 상태 / 포트 / 프로세스
- 파일 존재 여부 / 로그 / 설정 위치
- 네트워크 인터페이스 / 주소 / 라우팅
- 도구 설치 여부 / 실행 가능 여부

### 사람에게 물을 것
- 이 변경을 승인할지
- 어떤 후보가 실제 운영 의미상 맞는지
- 삭제/발송/차단 같은 위험 행동을 허용할지
- 조직/사용자 선호, 비즈니스 의도, 예외 규칙

---

## 5. 핵심 기술 스택

## 5.1 A2A (Agent-to-Agent / Manager ↔ SubAgent 분산 실행)
OpsClaw는 Manager가 직접 모든 시스템에 들어가 실행하지 않는다.

- **Manager API**가 계획, 오케스트레이션, 상태관리, 감사, 증빙을 담당한다.
- **SubAgent**는 각 실행 타깃에서 실제 명령/도구/API 호출을 수행한다.
- Manager는 A2A 방식으로 SubAgent에 실행을 위임하고 결과를 수집한다.

이 구조의 장점:
- 폐쇄망/분리망 대응
- 분산 타깃 실행
- 로컬/원격 혼합 운용
- 실행 권한과 계획 권한 분리

## 5.2 LangGraph / 상태기계 기반 워크플로우
OpsClaw는 단순 순차 스크립트보다 **상태기계 기반 워크플로우**를 지향한다.

대표 흐름:
- Intake
- Plan
- Probe
- Decide
- Execute
- Collect
- Validate
- Fix / Retry / Stop

LangGraph 철학이 중요한 이유:
- 실패/재시도/분기/중지조건을 구조화할 수 있음
- 상태 저장과 재현성이 좋아짐
- 자동화가 “대화”가 아니라 “절차”가 됨

## 5.3 FastAPI 기반 Manager / SubAgent
- `api/` : Manager API
- `subagent/` : 실행 노드 API
- `web/` : 콘솔 UI

FastAPI를 쓰는 이유:
- 경량 API 구현
- OpenAPI 기반 라우트 명세
- 다른 시스템과의 연동 용이

## 5.4 Docker / Docker Compose
기본 배포는 compose 기반이다.

현재 구성 개요:
- `api` : Manager
- `web` : 웹 콘솔
- `db` : 상태 저장 보조 DB
- `subagent` : 실행 노드 (환경에 따라 별도 원격 호스트 운영 가능)

## 5.5 LLM Registry / Multi-provider routing
현재 구조는 복수 LLM provider를 등록/선택할 수 있게 설계돼 있다.

예:
- `ollama`
- `openai`
- `anthropic`
- `yncai` (학교 게이트웨이)

역할별 바인딩:
- `master_conn_id`
- `manager_conn_id`
- `subagent_default_conn_id`

즉 OpsClaw는 “모델 1개 하드코딩”이 아니라 **역할 기반 모델 라우팅** 구조를 가진다.

## 5.6 MasterGate
외부 또는 상위 모델에 질의하기 전에:
- 개인정보
- 비밀정보
- 내부 자산 정보
를 점검/마스킹/차단하는 **데이터 거버넌스 레이어**다.

이건 보안 기능이라기보다, **조직 데이터를 안전하게 다루기 위한 운영 레이어**로 보는 게 맞다.

## 5.7 State / Audit / Evidence
OpsClaw는 결과만 중요한 게 아니라 **과정 전체를 남기는 시스템**이다.

- **State**: 현재 프로젝트, plan, inputs, runs, workflow 상태
- **Audit**: 언제 어떤 probe/결정/실행/승인이 있었는지
- **Evidence**: stdout/stderr, 로그, 아티팩트, ZIP 패키지

이 3가지는 나중에 Experience의 원천 데이터가 된다.

---

## 6. 시스템 구성

```text
User / Operator
    ↓
Web Console / API Request
    ↓
Manager API (FastAPI)
    ├─ Planner v0
    ├─ Probe Loop
    ├─ Input Resolver / Fact Resolver
    ├─ Playbook Runner / Workflow Engine
    ├─ Audit / State / Evidence 관리
    ├─ LLM Registry / Master Clients / MasterGate
    └─ Experience Layer (future)
            ↓ A2A
        SubAgent(s)
            ├─ shell / http / file / tool execution
            ├─ evidence collection
            └─ target-local observation
```

---

## 7. 전체 실행 흐름

## 7.1 현재 기준 핵심 흐름
1. Project 생성
2. 자연어 요청 저장
3. Planner가 target / playbook 후보 점수 계산
4. `run_auto` 실행
5. Playbook/Target 결정
6. `input_resolver`가 필요한 fact/missing input 계산
7. 자동으로 풀 수 있는 fact는 probe해서 resolve
8. 안 되면 choices/question 생성
9. 입력이 준비되면 playbook 실행
10. validate / fix / retry / result 저장
11. state / audit / evidence 축적

## 7.2 최종 비전 기준 흐름
1. Goal 이해
2. Unknowns 추출
3. Observation Domain에 probe 할당
4. Evidence 수집
5. Decision 생성
6. Skill 또는 Tool Lifecycle 실행
7. Validate
8. Replan
9. Experience update
10. 다음번에는 덜 묻고 더 정확하게 수행

---

## 8. 현재 코드베이스 기준 구현 현황

## 8.1 M1 ~ M2
- Core workflow 뼈대
- Evidence pack
- Audit / State 저장
- Web UI 기초
- MasterGate / Master provider 연동 기초

## 8.2 M3-4.x
- Planner v0
- Playbook Store
- Workflow / Playbook Runner 강화
- `run_auto` 기초 흐름 정착
- missing input / choices 반환 구조 도입

## 8.3 M3-5.1 완료
- LLM Connection Registry
- Role Binding
- `yncai` provider 연동
- `/llm/*` 라우트 정착

## 8.4 M3-5.2 완료(PhaseA)
- `run_auto`에서 missing/choices 처리 정착
- playbook `inputs.discover.commands` 기반 후보 수집
- 최소 human 질문 구조 정착
- remote subagent host-network 운영 가이드 정리
- state / audit / evidence 흐름 안정화

## 8.5 M3-5.3 현재 진행 중
M3-5.3은 “NIC 자동 찾기 기능 추가”가 아니라, **범용 fact/probe 구조를 도입해 Playbook 중심 구조에서 Goal/Probe 중심 구조로 옮겨가는 단계**다.

현재까지 반영된 핵심:
- `resolution_types.py` 도입
- `input_resolver.py`를 generic fact resolution coordinator 방향으로 확장
- `run_auto()`가 rationale / approvals / evidence_map 메타를 plan에 보존할 구조 도입
- playbook이 범용 fact(`target_os`, `pkg_manager`)를 요구하도록 확장 가능
- `sys_fact_resolver.py`를 통해 사실상 `sys.probe v0`의 축소판 구현
  - `target_os` 자동 판별
  - `pkg_manager` 자동 판별
  - `input_rationales` / `evidence_map` 저장

### 현재 상태를 한 문장으로 요약하면
**OpsClaw는 이제 Playbook 실행기에서 벗어나, 최소한 시스템 기본 사실을 스스로 확인하고 그 근거까지 남기는 단계로 진입했다.**

---

## 9. 현재 핵심 모듈 설명

## 9.1 Planner v0
자연어 요청과 등록된 target / playbook을 비교해 점수를 매기고, 가장 유력한 조합을 고른다.

현재는 완전한 IR 플래너가 아니라 **후보 정렬 + ambiguity 처리용 추천기** 성격이 강하다.

## 9.2 Playbook Store / Playbook Runner
- YAML playbook 로드
- jobs/steps 실행
- validate 반영
- 결과 저장

중요한 점은 YAML이 점점 “하드코딩 작업 언어”가 아니라, **입력/출력/정책/증빙 계약** 쪽으로 이동하고 있다는 점이다.

## 9.3 Input Resolver
현재 `input_resolver`는 단순 “값 채우기 함수”에서 벗어나고 있다.

방향:
- 어떤 fact가 필요한지 파악
- 일부 fact는 전용 resolver로 자동 해결
- 나머지는 discover.commands 또는 질문으로 fallback

## 9.4 Probe Loop
장기적으로 OpsClaw의 본체가 될 부분이다.

목표:
- unknowns가 나오면 probe 생성
- evidence 수집
- evidence 기반 결정
- 그래도 모호하면 human 최소 질문

## 9.5 Sys Probe (현재 축소판 구현)
현재는 `sys_fact_resolver.py`가 다음 사실을 자동으로 확인한다.

- `target_os`
- `pkg_manager`

향후 확장:
- `service_manager`
- `hostname`
- `kernel`
- `python_available`
- `docker_available`
- `has_sudo`

---

## 10. Tool / Skill / Experience 아키텍처

## 10.1 Tool
실행 수단 그 자체다.

예:
- shell.run
- http.request
- file.collect
- archive.pack
- browser automation
- OSS CLI
- 이메일 API

Tool은 “손과 발”이다.

## 10.2 Skill
입력/출력 계약, 정책, 검증, 증빙을 포함하는 재사용 단위다.

예:
- `sys.probe`
- `net.probe`
- `svc.probe`
- `fs.probe`
- `pkg.install`
- `fw.apply_ruleset`
- `mail.read`
- `mail.reply_draft`
- `mail.delete`
- `tool.discover`
- `tool.acquire`
- `tool.understand`
- `tool.run`
- `tool.wrap`

Skill은 “검증된 실행 패키지”다.

## 10.3 Experience
Experience는 다음을 저장한다.

- 사용자/조직 선호
- human-confirmed 결정
- 반복된 성공/실패 패턴
- 환경별 관찰된 규칙
- 장기적으로 재사용 가능한 운영 기억

예:
- 특정 타깃의 inline in/out pair
- 외부 발신 자동 답장 금지
- 운영 DB 직접 변경 금지
- 이 서비스는 health endpoint가 `/healthz`
- 특정 장애 유형에서 DB pool 고갈이 자주 원인

### Experience의 역할
- 미래 질문 수를 줄인다.
- 반복 판단의 정확도를 올린다.
- 사용자/조직별 맞춤 자동화를 가능하게 한다.

---

## 11. 향후 아키텍처 방향

## 11.1 Observation Domains
M3-5.3 이후 OpsClaw는 개별 resolver가 아니라 **Observation Domain** 중심으로 가야 한다.

### `sys.probe`
- target_os
- pkg_manager
- service_manager
- hostname
- kernel

### `svc.probe`
- service active
- process found
- listening ports
- health check
- recent logs summary

### `net.probe`
- interfaces
- addresses
- routes
- default route
- DNS / reachability
- candidate in/out

### `fs.probe`
- file exists
- size
- perms
- modified time
- config candidate paths

이 구조가 있어야 Suricata 설치, 서비스 장애 복구, 파일 정리, 로그 분석, 네트워크 구조 파악을 **같은 아키텍처 안에서** 다룰 수 있다.

## 11.2 Tool Lifecycle Engine
도구가 없으면 알아서:
1. 검색
2. 다운로드/clone
3. 문서 읽기
4. 사용법 추출
5. 샘플 probe
6. 실제 실행
7. wrapper/API화
8. 증빙 저장

이게 있어야 OpsClaw가 특정 번들에 갇히지 않고 확장된다.

## 11.3 IR (Intermediate Representation)
장기적으로는 YAML / 자연어 / LLM 출력 / Tool 실행을 모두 하나의 IR(JSON)로 통일해야 한다.

핵심 필드 예:
- `goal`
- `constraints`
- `policy`
- `unknowns`
- `probes`
- `evidence`
- `decisions`
- `plan`
- `validate`
- `errors`
- `fixes`
- `replans`
- `iterations`

## 11.4 Experience Layer
초기엔 DB 기반 정형 저장으로 시작하고,
중기엔 DB + embedding/RAG hybrid로 확장하는 게 현실적이다.

## 11.5 RL / Bandit Layer
RL/밴딧은 지금 당장 구현하지 않지만, 장기 계획에는 항상 포함한다.

적용 포인트:
- planner 후보 정렬
- probe 순서 선택
- human 질문 최소화
- experience weighting
- skill sequence ranking

중요 원칙:
- RL이 위험한 실제 action을 직접 지배하면 안 된다.
- RL은 질문/후보/전략 최적화 레이어로 붙는다.
- 고위험 action은 계속 정책/승인/롤백 스킬 아래 통제된다.

---

## 12. 개발 로드맵(요약)

## 단기
- `svc.probe v0`
- `net.probe v0`
- `fs.probe v0`
- `run_auto`와 Observation Domain 연계
- human answer/clarify endpoint

## 중기
- Experience v0
- Tool Lifecycle Engine v0
- wrapper/API화
- 더 많은 reusable Skill 패키지

## 장기
- IR v1
- Experience retrieval + RAG hybrid
- RL/밴딧 정책 레이어
- playbook 없는 자연어 목표를 더 직접적으로 해결하는 완전한 goal-driven orchestrator

---

# 13. User Cases (상세)

아래 사용 케이스들은 “완성된 OpsClaw” 기준 비전과, 현재 진행 중인 구조가 어디로 가는지를 동시에 보여준다.

## 사용 케이스 1) 원인 모르는 서비스 지연/장애 자동 복구

### 사용자 목표
“웹이 갑자기 느려졌어. 원인 찾아서 복구해. 재발 방지까지.”

### 시스템 흐름
- Planner가 웹/API/DB/캐시 경로를 가정한다.
- `svc.probe`, `sys.probe`, `fs.probe`, 필요 시 `net.probe`를 먼저 친다.
- CPU/메모리/디스크/포트/프로세스/로그/에러율/health를 수집한다.
- 병목 후보를 ranking 한다.
- 완화 조치(재시작/스케일/캐시 flush)는 위험도에 따라 승인 요구.
- 적용 후 동일 probe를 다시 실행해 정상화 여부를 검증한다.
- 실패하면 다음 원인 후보로 replan 한다.

### 산출물
- 장애 타임라인
- 근본 원인 후보 / 조치 / 검증 로그
- evidence ZIP

## 사용 케이스 2) 신규 서버 5대 온보딩

### 사용자 목표
“신규 서버 5대 기본 셋업(계정/SSH/보안/모니터링/로그) 해줘. 증빙 남겨.”

### 시스템 흐름
- 대상 그룹 선택
- `sys.probe`로 각 서버 OS/패키지 매니저/서비스 매니저 확인
- SSH 설정, 계정 상태, 기존 agent 존재 여부를 확인
- 공통 DAG 실행: 계정/키/패키지/에이전트/검증
- 실패 노드는 선택적으로 재시도
- 충돌하는 설정은 human에게 질문

### 산출물
- 서버별 성공/실패 표
- 설정 diff
- 최종 heartbeat / 포트 확인 증빙

## 사용 케이스 3) 전체 서버 보안 점검 및 보고서 생성

### 사용자 목표
“전체 서버 취약 설정/열린 포트/취약 패키지 점검해서 보고서 만들어.”

### 시스템 흐름
- target inventory 수집
- `sys.probe`, `svc.probe`, `net.probe`, `fs.probe`로 기본 사실 수집
- 필요 시 OSS 스캐너를 검색·도입·실행
- 결과를 JSON으로 통일해 위험도 분류
- 수정 제안은 PR/패치안 중심으로 제시

### 산출물
- 점검 보고서
- 서버별 리스크 목록
- 스캐너 버전/커밋/실행 명령이 포함된 증빙팩

## 사용 케이스 4) 네트워크 구조 파악과 in/out 인터페이스 결정

### 사용자 목표
“이 서버에서 인라인(in/out) 인터페이스를 정확히 판별해.”

### 시스템 흐름
- `net.probe`로 NIC/ADDR/ROUTE/GW/DNS/Reachability 수집
- default route, 주소, 실트래픽 단서를 조합해 후보 생성
- 여전히 애매하면 사용자가 두 후보 중 선택
- 결론을 Experience로 저장 가능

### 산출물
- 인터페이스 후보와 근거
- 최종 결정값
- 재현 가능한 probe 명령 모음

## 사용 케이스 5) IDS/로그 파이프라인 장애 추적

### 사용자 목표
“Suricata 로그가 SIEM으로 안 올라가. 어디서 끊겼는지 찾아서 복구해.”

### 시스템 흐름
- 파이프라인을 구간별로 모델링
- 각 구간에서 `svc.probe`, `fs.probe`, `net.probe` 수행
- 로그 파일 생성 여부, forwarder queue, collector 포트, SIEM API 상태 확인
- 끊긴 구간 pinpoint 후 수정 조치 제안
- 필요 시 승인 후 서비스 재시작/권한 수정/재전송 트리거

### 산출물
- 장애 구간 pinpoint
- 조치 전후 end-to-end 흐름 검증
- 관련 로그 증빙

## 사용 케이스 6) 방화벽 정책 변경 + 자동 검증 + 롤백

### 사용자 목표
“API 서버는 443만 열고 나머지는 차단. 변경 후 접속 테스트까지.”

### 시스템 흐름
- 현재 규칙/열린 포트/의존 통신 파악
- 영향 분석
- high-risk로 분류하여 승인 요청
- 변경 전 정책 백업
- 적용 후 smoke test
- 실패하면 자동 롤백

### 산출물
- 적용 diff
- 롤백 포인트
- 검증 결과

## 사용 케이스 7) OSS 도구가 없는 문제 해결

### 사용자 목표
“PCAP에서 특정 패턴 트래픽만 추출해 통계 내줘. 도구 없으면 알아서 찾아 써.”

### 시스템 흐름
- 필요 기능 정의
- `tool.discover`로 후보 OSS 탐색
- clone/install
- README/--help 학습
- 샘플 입력으로 probe
- 실제 처리
- 필요 시 wrapper 생성

### 산출물
- 사용한 도구 버전/커밋
- 실행 명령
- JSON 결과 + 요약 보고서

## 사용 케이스 8) DB 백업/복구 리허설

### 사용자 목표
“백업 잘 되는지 확인하고, 복구 리허설까지 수행해서 증빙 남겨.”

### 시스템 흐름
- `fs.probe`로 백업 파일 존재/최근성/크기 확인
- `sys.probe`로 DB 환경 확인
- 격리된 환경 복구
- 샘플 쿼리/테이블 수로 무결성 검증
- 운영 직접 영향 시 승인 요구

### 산출물
- 백업 존재 증빙
- 복구 로그
- 무결성 체크 결과

## 사용 케이스 9) IAM/권한 감사 + 최소 권한 정리

### 사용자 목표
“권한 과다 계정 찾고 정리안 만들고, 승인 후 적용.”

### 시스템 흐름
- 사용자/그룹/권한 구조 수집
- 위험 권한 패턴 탐지
- human 승인 후 변경
- 영향도 검증
- rollback 정보 저장

### 산출물
- 변경 전/후 권한 diff
- 승인 로그
- 검증 결과

## 사용 케이스 10) 성능 튜닝

### 사용자 목표
“API p95가 튀어. 원인 찾고 개선해. 개선 전/후 증빙 남겨.”

### 시스템 흐름
- 지표/로그/리소스 동시 수집
- 병목 가설 생성
- 실험 순서 결정
- 필요 시 벤치/프로파일러 도구 자동 도입
- 설정 변경/캐시/리소스 조정
- 전/후 비교

### 산출물
- 가설 목록
- 전후 벤치
- 그래프/로그 증빙

## 사용 케이스 11) 보안 이벤트 대응

### 사용자 목표
“이상 트래픽. 감염 조사하고 필요한 조치 실행. 증빙 남겨.”

### 시스템 흐름
- IOC 기반 파일/프로세스/연결/로그 조사
- 감염 가능성 판단
- 조사/수집은 자동
- 격리/차단/계정 잠금은 승인 후 실행
- 재발 여부 확인

### 산출물
- 탐지→조사→조치→검증 타임라인
- 증거 파일

## 사용 케이스 12) 주간 운영 리포트 생성

### 사용자 목표
“이번 주 장애/변경/조치/승인 내역을 증빙과 함께 보고서로.”

### 시스템 흐름
- audit/state/evidence index 수집
- 중요 이벤트 분류
- 요약과 개선사항 도출
- Markdown/PDF 리포트 생성

### 산출물
- 운영 리포트
- evidence ZIP 링크/첨부

## 사용 케이스 13) 이메일 읽기·요약·분류·답장 초안 생성

### 사용자 목표
“내 이메일을 읽어서 요약하고, 중요하지 않은 건 초안 답장 만들어.”

### 시스템 흐름
- 메일 시스템 종류 확인(Gmail/Outlook/IMAP/브라우저)
- 권한/정책/자동발송 허용 여부 확인
- 최근 메일 목록 수집
- 중요도 분류
- low-risk는 초안 생성
- 실제 발송은 정책/선호에 따라 결정

### 산출물
- 받은 메일 요약
- 중요/비중요 분류 결과
- 초안 답장 목록

## 사용 케이스 14) 이메일 자동 삭제/휴지통 정책 적용

### 사용자 목표
“광고성/의미없는 메일은 자동으로 정리해.”

### 시스템 흐름
- 사용자 선호와 조직 정책 확인
- 삭제 대신 trash 이동이 기본인지 확인
- 샘플 분류 후 human 확인
- 이후 Experience에 저장
- 반복적으로 같은 패턴에 대해 자동 정리 강화

### 산출물
- 정리 대상 목록
- 삭제/휴지통 이동 로그
- 정책/선호 기록

## 사용 케이스 15) 디렉토리 파일 정리

### 사용자 목표
“이 디렉토리 파일 좀 정리해. 오래된 것, 중복, 의미 없는 것 구분해서.”

### 시스템 흐름
- `fs.probe`로 목록, 크기, 수정시간, 확장자, 중복 후보 수집
- 보존 규칙을 사용자에게 최소 질문
- 정리안 제시
- 승인 후 이동/압축/삭제 수행

### 산출물
- 정리 전/후 목록
- 이동/삭제 기록
- archive 파일

## 사용 케이스 16) 웹방화벽(WAF) 룰 생성 및 적용

### 사용자 목표
“이 애플리케이션 공격 패턴을 막는 WAF 룰 만들어서 적용해.”

### 시스템 흐름
- 로그/공격 패턴 수집
- 룰 초안 생성
- dry-run / detect-only 테스트
- false positive 검토
- 승인 후 차단 모드 적용

### 산출물
- 룰 diff
- 테스트 결과
- 적용/롤백 로그

## 사용 케이스 17) 서드파티 서비스 연동 장애 분석

### 사용자 목표
“외부 API 호출이 자꾸 실패해. 네트워크인지 인증인지 찾아.”

### 시스템 흐름
- DNS/route/reachability 확인
- 자격증명/토큰 만료 확인
- http probe / 로그 / 응답 코드 비교
- 원인 분류(네트워크, TLS, auth, rate limit)
- 수정 또는 human 확인

### 산출물
- 실패 원인 분류
- 재현 명령
- 수정 후 검증

## 사용 케이스 18) 배포 후 헬스체크 및 회귀 탐지

### 사용자 목표
“새 버전 배포했는데 문제 없는지 확인해.”

### 시스템 흐름
- 서비스 포트/프로세스/health endpoint 확인
- 최근 오류 로그와 latency 비교
- 이전 baseline과 비교
- 이상 시 rollback 제안

### 산출물
- 배포 검증 리포트
- 회귀 여부
- rollback 여부

## 사용 케이스 19) 규정 준수/설정 표준화 점검

### 사용자 목표
“우리 운영 표준에 맞게 SSH, sudoers, 로그, 패키지 상태 점검해.”

### 시스템 흐름
- 표준 정책 로드
- `sys.probe`, `fs.probe`, `svc.probe`로 현상 수집
- 차이(diff) 계산
- 자동 수정 가능한 것과 승인 필요한 것 분리

### 산출물
- 표준 위반 항목 목록
- 수정안
- 검증 로그

## 사용 케이스 20) 클라우드/가상화 자원 운영 자동화

### 사용자 목표
“신규 VM 몇 대 올리고 기본 셋업한 뒤 heartbeat까지 확인해.”

### 시스템 흐름
- 자원 생성 API/CLI 호출
- 호스트 접근 가능 여부 확인
- `sys.probe`로 초기 facts 수집
- 온보딩 DAG 실행
- 최종 서비스/에이전트 heartbeat 확인

### 산출물
- 자원 목록
- 셋업 결과
- 최종 가동 상태

## 사용 케이스 21) 구성 파일 위치 탐색 및 자동 수정 제안

### 사용자 목표
“이 서비스 설정 파일이 어디 있는지 찾고, 변경안까지 제안해.”

### 시스템 흐름
- `fs.probe`로 일반 경로 후보 탐색
- 프로세스 실행 인자/서비스 파일 조사
- 구성 파일 결정
- 수정안 diff 생성
- 적용은 승인 후

### 산출물
- 후보 경로 목록
- 최종 설정 파일
- 변경 diff

## 사용 케이스 22) 감사 대응용 증빙 패키지 자동 생성

### 사용자 목표
“이 작업에 대한 감사 대응 증빙을 제출 가능한 형태로 묶어줘.”

### 시스템 흐름
- 관련 project state / audit / evidence 수집
- 명령, 결과, 승인, diff, 로그를 정리
- ZIP + Markdown/PDF 보고서 생성

### 산출물
- 제출용 evidence pack
- 실행 요약 보고서
- 감사 타임라인

---

## 14. 마무리

OpsClaw는 아직 완성형이 아니다. 하지만 방향은 분명하다.

- Playbook 중심 실행기에서 출발해
- Probe/Evidence 기반 의사결정 구조를 만들고
- Tool / Skill / Experience로 확장하며
- 장기적으로는 RL/밴딧으로 질문/후보/전략 선택을 최적화하는

**범용 IT 업무 오케스트레이션 에이전트**로 가고 있다.

핵심은 “LLM이 똑똑해서 다 한다”가 아니다.
핵심은 **LLM이 Tool과 Skill을 활용해 필요한 사실을 확인하고, 인간은 정말 필요한 결정만 하며, 그 과정 전체가 evidence와 experience로 축적되는 시스템**이라는 점이다.
