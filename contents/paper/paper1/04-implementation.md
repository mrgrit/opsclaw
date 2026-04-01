# 4. 설계 및 구현 (Design & Implementation)

본 장에서는 OpsClaw의 다섯 가지 핵심 모듈—PoW 블록체인, 강화학습 정책 엔진, Playbook 엔진, 4-Layer 경험 메모리, 병렬 Multi-Agent Dispatch—의 설계와 구현을 기술한다. 각 모듈의 알고리즘은 수도코드로 제시하며, 핵심 설계 결정(design decision)의 근거를 논의한다.

## 4.1 PoW 블록체인

### 4.1.1 블록 구조

OpsClaw의 PoW 블록은 태스크 실행 1건에 대응하는 단위 기록이다. 각 블록은 다음 필드로 구성된다:

```
Block = {
  block_id:       UUID,
  agent_id:       String,          // SubAgent URL (서버 식별)
  project_id:     UUID,
  task_order:     Integer,
  task_title:     String,
  evidence_hash:  SHA-256,         // H(stdout ‖ stderr ‖ exit_code)
  prev_hash:      SHA-256,         // 이전 블록의 block_hash
  block_hash:     SHA-256,         // H(prev_hash ‖ evidence_hash ‖ ts_raw ‖ nonce)
  nonce:          Integer,         // PoW 조건을 만족시키는 값
  difficulty:     Integer,         // 선행 제로 비트 수 (기본값: 4)
  ts_raw:         String,          // ISO 8601 UTC 타임스탬프 (원본 문자열)
  created_at:     Timestamp
}
```

그림 3은 블록 간 해시 체인 연결을 도시한다.

```
그림 3. PoW 해시 체인 구조

┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Block #1   │    │  Block #2   │    │  Block #3   │
│             │    │             │    │             │
│ prev_hash:  │    │ prev_hash:  │    │ prev_hash:  │
│  "0000..."  │◄───│  H(B#1)     │◄───│  H(B#2)     │
│             │    │             │    │             │
│ evidence:   │    │ evidence:   │    │ evidence:   │
│  H(stdout₁) │    │  H(stdout₂) │    │  H(stdout₃) │
│             │    │             │    │             │
│ block_hash: │    │ block_hash: │    │ block_hash: │
│  H(B#1)     │    │  H(B#2)     │    │  H(B#3)     │
│  0000xxxx   │    │  0000xxxx   │    │  0000xxxx   │
└─────────────┘    └─────────────┘    └─────────────┘
```

### 4.1.2 마이닝 알고리즘

`_mine_block` 함수는 `block_hash`가 `difficulty`개의 선행 제로(leading zeros)로 시작하는 `nonce`를 탐색한다.

```
Algorithm 1: PoW Block Mining
─────────────────────────────────────────────
Input:  prev_hash, evidence_hash, ts_raw, difficulty
Output: (block_hash, nonce)

1  prefix ← "0" × difficulty
2  for nonce ← 0 to MAX_NONCE do
3      raw ← prev_hash ‖ evidence_hash ‖ ts_raw ‖ str(nonce)
4      h ← SHA-256(raw)
5      if h starts with prefix then
6          return (h, nonce)
7  raise MiningExhausted
```

`difficulty = 4`에서 기대 반복 횟수는 16⁴ = 65,536회이며, 실측 마이닝 시간은 약 0.1초이다. `MAX_NONCE = 10,000,000`으로 안전 상한을 설정하여 무한 루프를 방지한다.

**설계 결정: 합의 프로토콜 배제.** OpsClaw는 단일 조직 내 에이전트 하네스이므로, 비잔틴 합의(Byzantine consensus)가 불필요하다. 경량 해시 체인만으로 위변조 탐지의 목적을 달성하며, 블록체인 네트워크의 운영 비용을 회피한다.

### 4.1.3 체인 검증

`verify_chain` 함수는 에이전트의 전체 블록 체인을 순회하며 무결성을 검증한다.

```
Algorithm 2: Chain Verification
─────────────────────────────────────────────
Input:  agent_id
Output: {valid, blocks, orphans, tampered[]}

1  all_blocks ← SELECT * FROM proof_of_work WHERE agent_id = agent_id
2  chain ← _build_chain(all_blocks)       // linked-list 순회
3  orphans ← |all_blocks| - |chain|
4  tampered ← []
5  for i ← 1 to |chain| do
6      block ← chain[i]
7      // evidence_hash 재계산
8      expected_eh ← SHA-256(block.stdout ‖ block.stderr ‖ block.exit_code)
9      if expected_eh ≠ block.evidence_hash then
10         tampered.append(block.block_id)
11     // block_hash 재계산
12     expected_bh ← SHA-256(block.prev_hash ‖ block.evidence_hash
13                           ‖ block.ts_raw ‖ str(block.nonce))
14     if expected_bh ≠ block.block_hash then
15         tampered.append(block.block_id)
16     // prev_hash 연결 검증
17     if i > 0 and block.prev_hash ≠ chain[i-1].block_hash then
18         tampered.append(block.block_id)
19 return {valid: |tampered| = 0, blocks: |chain|, orphans, tampered}
```

**M27 패치: linked-list 재구성.** 초기 구현에서는 `ORDER BY ts`로 체인 순서를 결정하였으나, 시간대(timezone) 차이로 인한 순서 역전 버그(B-02)가 발견되었다. M27에서 `ts_raw` 필드를 추가하고, `_build_chain` 함수가 `prev_hash` 링크를 따라가는 linked-list 순회로 변경하여, 타임스탬프에 무관한 정확한 체인 재구성을 보장한다. 분기(split)가 발생한 블록은 최장 체인(longest-chain) 규칙으로 주 체인을 결정하고, 나머지를 orphan으로 분류한다.

**동시성 제어.** 동일 `agent_id`에 대한 동시 마이닝을 직렬화하기 위해 PostgreSQL의 `pg_advisory_xact_lock(hash(agent_id))`를 사용한다. 이를 통해 병렬 execute-plan에서도 `prev_hash` 링크의 일관성을 보장한다.

### 4.1.4 보상 산출

각 PoW 블록 생성 시 보상(reward)이 자동 산출되어 `task_reward` 테이블에 기록된다.

```
Algorithm 3: Reward Calculation
─────────────────────────────────────────────
Input:  exit_code, duration_s, risk_level
Output: total_reward

1  if exit_code = 0 then
2      base_score ← +1.0
3      if duration_s < 5 then speed_bonus ← +0.3
4      else if duration_s < 30 then speed_bonus ← +0.15
5      else if duration_s < 60 then speed_bonus ← +0.05
6      else speed_bonus ← 0.0
7      risk_penalty ← 0.0
8  else
9      base_score ← -1.0
10     speed_bonus ← 0.0
11     if risk_level = "high" then risk_penalty ← -0.1
12     else if risk_level = "critical" then risk_penalty ← -0.2
13     else risk_penalty ← 0.0
14 quality_bonus ← 0.0              // 향후 인간 피드백용 예약
15 total_reward ← base_score + speed_bonus + risk_penalty + quality_bonus
16 return total_reward
```

보상 값은 [-1.2, +1.3] 범위이며, 성공적이고 빠른 저위험 태스크가 최고 보상을 받는다. `reward_ledger` 테이블이 에이전트별 누적 보상과 성공/실패 통계를 관리하며, 리더보드(`GET /pow/leaderboard`)를 통해 에이전트 간 성과 비교가 가능하다.

## 4.2 강화학습 정책 엔진

### 4.2.1 상태 공간 및 행동 공간

OpsClaw의 RL 엔진은 테이블 기반 Q-learning을 사용한다.

**상태 공간 S.** 48개 이산 상태로 구성된다:
- `risk_level` ∈ {low, medium, high, critical} → 인덱스 0~3
- `success_rate` ∈ {[0, 0.25), [0.25, 0.5), [0.5, 0.75), [0.75, 1.0]} → 버킷 0~3
- `task_order` ∈ {[1, 3], [4, 7], [8, ∞)} → 버킷 0~2
- `state_idx = risk_idx × 12 + sr_bucket × 3 + order_bucket`

**행동 공간 A.** 4개 이산 행동: {low, medium, high, critical}. 각 행동은 권장 위험도 수준에 대응한다.

**보상 신호 R.** 4.1.4절의 `total_reward` 값이 직접 사용된다.

### 4.2.2 Q-learning 업데이트

에피소드 수집(`collect_episodes`)은 `task_reward` 테이블에서 (state, action, reward) 튜플을 추출한다. 각 에피소드는 종결 상태(terminal)이므로, 단순화된 업데이트 규칙을 적용한다:

```
Algorithm 4: Q-Learning Training
─────────────────────────────────────────────
Input:  episodes[], α (learning rate), policy_path
Output: updated Q-table

1  Q ← load_q_table(policy_path) or zeros(48, 4)
2  visit_counts ← load_visit_counts(policy_path) or zeros(48, 4)
3  for each (s, a, r) in episodes do
4      Q[s][a] ← Q[s][a] + α × (r - Q[s][a])
5      visit_counts[s][a] ← visit_counts[s][a] + 1
6  save_q_table(Q, visit_counts, policy_path)
7  return Q
```

기본 하이퍼파라미터: α = 0.1, γ = 0.95 (향후 다단계 에피소드 확장용 예약). 학습 최소 에피소드 수는 5건이다.

**설계 결정: 테이블 Q-learning 선택.** 상태 공간이 48개로 소규모이므로, 함수 근사(DQN 등)의 복잡성 없이 테이블 기반 Q-learning이 충분하다. 이는 해석 가능성(interpretability), 수렴 속도, 구현 단순성에서 이점이 있다. 상태 공간 확대 시 DQN으로의 전환은 인터페이스 변경 없이 가능하도록 설계하였다.

### 4.2.3 UCB1 탐색 전략

추천 시(`recommend`) 세 가지 탐색 전략을 지원한다.

```
Algorithm 5: UCB1 Exploration
─────────────────────────────────────────────
Input:  state s, Q-table, visit_counts, c (exploration constant)
Output: recommended action a*

1  N ← Σ_a visit_counts[s][a]        // 상태 s의 총 방문 횟수
2  if N = 0 then return random(A)
3  for each action a in A do
4      n_a ← visit_counts[s][a]
5      if n_a = 0 then return a       // 미방문 행동 우선 탐색
6      ucb[a] ← Q[s][a] + c × √(ln(N) / n_a)
7  return argmax_a ucb[a]
```

UCB1(Upper Confidence Bound)은 Q-value가 높은 행동(exploitation)과 방문 횟수가 적은 행동(exploration)을 균형 있게 선택한다. `c = 1.414` (√2)를 기본값으로 사용한다. 미방문 행동이 존재하면 무조건 해당 행동을 추천하여 정책 커버리지를 확대한다.

## 4.3 Playbook 엔진

### 4.3.1 결정론적 실행

Playbook 엔진은 LLM의 비결정론 문제를 해결하기 위해 **파라미터 바인딩 기반 결정론적 빌더(deterministic builder)** 패턴을 채택한다.

```
Algorithm 6: Playbook Step Resolution
─────────────────────────────────────────────
Input:  step (step_type, ref_id, params), registry
Output: executable_command

1  if step.step_type = "tool" then
2      tool ← registry.get_tool(step.ref_id)
3      command ← tool.template.format(**step.params)
4  else if step.step_type = "skill" then
5      skill ← registry.get_skill(step.ref_id)
6      command ← skill.resolve(**step.params)
7  return command
```

각 Playbook step은 `step_type`(tool 또는 skill), `ref_id`(레지스트리 ID), `params`(파라미터 딕셔너리)를 명시적으로 지정한다. `resolve_step_script()` 함수가 파라미터를 결정론적으로 바인딩하여 동일한 실행 가능 명령을 생성한다. 이를 통해 LLM이 생성하는 명령의 비결정론(동일 지시에 대해 다른 명령 생성)을 완전히 제거한다.

### 4.3.2 Playbook 실행 흐름

```
Algorithm 7: Playbook Execution
─────────────────────────────────────────────
Input:  playbook_id, project_id, subagent_url, dry_run
Output: execution_results[]

1  steps ← GET /playbooks/{playbook_id}/steps (ORDER BY step_order)
2  results ← []
3  for each step in steps do
4      command ← resolve_step_script(step)
5      if dry_run then
6          results.append({step, command, status: "dry_run"})
7          continue
8      response ← dispatch_to_subagent(subagent_url, command)
9      evidence ← record_evidence(project_id, command, response)
10     pow_block ← generate_proof(project_id, agent_id, step.order, ...)
11     results.append({step, command, response, evidence, pow_block})
12 return results
```

Playbook의 재실행은 동일한 steps 시퀀스를 동일한 파라미터로 실행하므로, 시스템 상태가 동일하다면 동일한 결과를 산출한다. 실험 G에서 10회 반복 실행 시 의미적 완전 일치(100%)를 달성하였다.

## 4.4 4-Layer 경험 메모리

OpsClaw는 원시 실행 기록부터 의미적 지식까지 4계층으로 구조화된 메모리를 운영한다. 그림 4는 데이터 흐름을 도시한다.

```
그림 4. 4-Layer 경험 메모리 아키텍처

Layer 1: Evidence (원시 기록)
┌──────────────────────────────────────────┐
│ command_text │ stdout │ stderr │ exit_code │
│ started_at   │ finished_at │ agent_role   │
└──────────────┬───────────────────────────┘
               │ build_task_memory()
               ▼
Layer 2: Task Memory (구조화 요약)
┌──────────────────────────────────────────┐
│ project_id │ summary │ metadata           │
│ (evidence_count, asset_ids, final_stage)  │
└──────────────┬───────────────────────────┘
               │ promote_to_experience()
               │ auto_promote_high_reward(threshold=1.1)
               ▼
Layer 3: Experience (의미적 지식)
┌──────────────────────────────────────────┐
│ category │ title │ summary │ outcome      │
│ linked_evidence_ids │ metadata            │
└──────────────┬───────────────────────────┘
               │ index_document()
               ▼
Layer 4: Retrieval (검색 인덱스)
┌──────────────────────────────────────────┐
│ document_type │ title │ body │ tsvector   │
│ PostgreSQL FTS + ILIKE fallback           │
└──────────────────────────────────────────┘
               │ search_documents(query)
               ▼
           RAG Context Injection → Master LLM
```

### 4.4.1 Layer 1: Evidence

태스크 실행 즉시 `evidence` 테이블에 기록된다. 각 레코드는 실행된 명령(`command_text`), 출력(`stdout_ref`, `stderr_ref`), 종료 코드(`exit_code`), 실행 시각(`started_at`, `finished_at`), 실행 주체(`agent_role`)를 포함한다. 출력 데이터는 `inline://stdout/{id}:{content}` 형식의 인라인 참조로 저장된다.

### 4.4.2 Layer 2: Task Memory

`build_task_memory(project_id)` 함수가 프로젝트 종료 시 호출되어, 해당 프로젝트의 모든 evidence, 보고서, 연결 자산, Playbook 정보를 집계하여 구조화 요약을 생성한다. 요약 형식은 "Project: {name} | Request: {text} | Stage: {stage} | Evidence: {count} records"이며, 메타데이터에 `evidence_count`, `asset_ids`, `playbook_id`, `final_stage`, `mode`를 저장한다. 동일 프로젝트에 대해 멱등(idempotent)하게 동작하여 중복 생성을 방지한다.

### 4.4.3 Layer 3: Experience

Task Memory에서 재사용 가치가 높은 항목을 경험(experience)으로 승급한다. 세 가지 승급 경로를 지원한다:

1. **수동 승급** (`promote_to_experience`): 관리자가 명시적으로 카테고리, 제목, 결과를 지정하여 승급
2. **LLM 자동 승급** (`auto_promote_experience`): pi LLM이 Task Memory 요약에서 의미 있는 제목, 카테고리, 교훈을 자동 추출하여 승급
3. **보상 기반 자동 승급** (`auto_promote_high_reward`): 프로젝트의 평균 보상이 임계값(기본 1.1) 이상이면 자동 승급. 이를 통해 고성과 태스크 패턴이 경험 지식으로 축적된다.

### 4.4.4 Layer 4: Retrieval

`retrieval_documents` 테이블에 인덱싱된 문서에 대해 PostgreSQL의 `to_tsvector` / `plainto_tsquery` 기반 전문 검색(FTS)을 제공한다. FTS로 결과가 없을 경우 ILIKE 폴백 검색을 수행한다. 문서 유형(`document_type`) 필터링을 지원하며, report, evidence_summary, experience, playbook, asset 유형이 인덱싱 대상이다. 검색 결과는 RAG 방식으로 Master LLM의 컨텍스트에 주입되어, 과거 유사 경험을 기반으로 한 의사결정을 지원한다.

### 4.4.5 RL 연결

4-Layer 메모리와 RL 정책 엔진은 보상 신호를 통해 연결된다. Layer 1의 evidence에서 파생된 보상이 `collect_episodes()`를 통해 Q-learning 학습 데이터로 공급되고, 학습된 정책이 향후 태스크의 `risk_level` 추천에 활용된다. 동시에 고보상 태스크가 Layer 3 experience로 자동 승급되어, 성공 패턴이 RAG를 통해 미래 계획 수립에 반영된다. 이를 통해 **실행→증적→보상→학습→경험→검색→계획**의 자기 개선 루프가 완성된다.

## 4.5 병렬 Multi-Agent Dispatch

### 4.5.1 태스크별 SubAgent 라우팅

execute-plan의 각 태스크는 개별 `subagent_url`을 지정할 수 있어, 단일 API 호출로 다수의 서버에 동시 작업을 위임할 수 있다.

```
Algorithm 8: Parallel Multi-Agent Dispatch
─────────────────────────────────────────────
Input:  tasks[], global_subagent_url, parallel, dry_run
Output: aggregated_results

1  if parallel and |tasks| > 1 and not dry_run then
2      workers ← min(|tasks|, 5)
3      executor ← ThreadPoolExecutor(max_workers=workers)
4      futures ← {}
5      for each task in tasks do
6          url ← task.subagent_url or global_subagent_url
7          f ← executor.submit(dispatch_single_task, task, url)
8          futures[task.order] ← f
9      results ← [futures[order].result() for order in sorted(futures)]
10 else
11     results ← []
12     for each task in tasks (ordered) do
13         url ← task.subagent_url or global_subagent_url
14         result ← dispatch_single_task(task, url)
15         results.append(result)
16 return aggregate(results)
```

### 4.5.2 위험도 자동 에스컬레이션

보안을 위해 `sudo` 키워드가 포함된 명령의 위험도를 자동 상향한다:

```
if regex("\bsudo\b", task.instruction_prompt):
    if task.risk_level in {"low", "medium"}:
        task.risk_level ← "high"
        task.sudo_elevated ← true
```

`critical` 위험도 태스크는 `confirmed: true`가 명시적으로 전달되지 않는 한 `dry_run`이 강제된다. 이를 통해 파괴적 명령의 의도치 않은 실행을 방지한다.

### 4.5.3 비동기 실행 모드

장시간 태스크를 위한 비동기 모드(`async_mode: true`)를 지원한다. 비동기 요청 시 데몬 스레드에서 execute-plan이 백그라운드로 실행되며, `job_id`가 즉시 반환된다. 클라이언트는 `GET /async-jobs/{job_id}`로 진행 상태를 폴링하여 완료를 확인할 수 있다.

### 4.5.4 결과 집계

개별 태스크 결과는 다음 규칙으로 프로젝트 수준의 전체 결과(`overall`)로 집계된다:
- `success`: 모든 태스크가 성공 상태(ok, success)
- `partial`: 일부 태스크 성공, 일부 실패
- `failed`: 모든 태스크 실패
- `dry_run`: dry_run 모드로 실행

## 4.6 Bastion 개선 패키지

Claude Code 소스코드 분석(Bastion 프로젝트)을 통해 6개 패키지를 신규 추가하였다.

| Package | Lines | Function |
|---------|-------|----------|
| prompt_engine | ~300 | 7개 섹션 모듈로 시스템 프롬프트 동적 조합 (7,852자) |
| hook_engine | ~250 | 10개 라이프사이클 이벤트, webhook/script 실행, 차단 가능 |
| tool_validator | ~150 | JSON Schema 기반 Tool 입출력 검증 |
| cost_tracker | ~120 | LLM 토큰/비용 추적, 예산 강제 |
| permission_engine | ~200 | RBAC+Policy+Approval+Risk 다층 퍼미션 |
| memory_manager | ~180 | 자동 메모리 추출, LRU 용량 관리, 유형 분류 |

이는 Claude Code의 도구 시스템(45개 내장 도구, 10단계 파이프라인), Hook 시스템(14개 이벤트), 권한 시스템(4 모드)을 서버 사이드 하네스에 맞게 재설계한 것이다.

## 4.7 구현 통계

표 2에 OpsClaw의 구현 규모를 요약한다.

**표 2. 구현 통계**

| 항목 | 수치 |
|------|------|
| 핵심 패키지 | 13개 |
| 서비스 | 5개 |
| DB 마이그레이션 | 13개 |
| DB 테이블 | 17개 |
| 등록 Tool | 6개 |
| 등록 Skill | 6개 |
| API 엔드포인트 | ~40개 |
| Q-table 상태 공간 | 48 states × 4 actions |
| PoW 기본 난이도 | 4 (선행 제로) |
| 개발 기간 | M0~M25 (약 25 마일스톤) |
| 주요 언어 | Python 3.11 |
| 프레임워크 | FastAPI + LangGraph + PostgreSQL 15 |
