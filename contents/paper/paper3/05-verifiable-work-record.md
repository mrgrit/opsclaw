# 5. 검증 가능한 작업 기록의 활용 (Verifiable Work Record Applications)

본 장에서는 OpsClaw의 PoW 해시 체인과 보상 체계를 **검증 가능한 작업 기록(Verifiable Work Record, VWR)**으로 재정의하고, 3가지 활용 시나리오를 실제 데이터로 실증한다.

## 5.1 VWR의 정의

검증 가능한 작업 기록(VWR)은 에이전트가 수행한 태스크의 실행 결과, 해시 무결성, 보상을 하나의 블록으로 결합한 구조이다.

```
VWR Block = {
  WHO:    agent_id (어떤 에이전트가)
  WHAT:   task_title + instruction_prompt (무엇을)
  WHEN:   ts_raw (언제)
  RESULT: evidence_hash = H(stdout ‖ stderr ‖ exit_code) (어떤 결과로)
  PROOF:  block_hash, nonce, prev_hash (검증 가능하게)
  VALUE:  total_reward = base + speed_bonus + risk_penalty (얼마의 가치로)
}
```

VWR은 "위변조가 불가능한 블록체인"이 아니라, **에이전트 작업의 검증 가능한 영수증**이다. DB 관리자가 전체 체인을 재작성하면 무력화되므로 분산 합의 수준의 보장은 제공하지 않는다. 그러나 단일 조직 내에서 (1) 부분 변조를 탐지하고, (2) "이만큼 일했다"를 양측이 검증하며, (3) 보상 기반 성과를 추적하는 데 실용적 가치를 제공한다.

## 5.2 활용 시나리오

### 시나리오 1: 에이전트 성과 평가

누적 VWR로 SubAgent별 신뢰도 점수를 산출한다.

```
secu agent:  150 blocks, avg_reward = 1.25, success_rate = 92%
web agent:   200 blocks, avg_reward = 0.85, success_rate = 78%
siem agent:  80 blocks,  avg_reward = 1.10, success_rate = 88%
```

→ 중요도가 높은 태스크는 avg_reward가 높은 에이전트에 우선 배정. 이는 RL 정책 엔진의 `recommend()` API와 연결되어 자동화할 수 있다.

**실증 결과 (prj_e8bb1b986ebb).** 4개 SubAgent(opsclaw, secu, web, siem)에 동일 태스크(hostname, uptime, uname, df, free)를 실행한 결과:

**표 3. 에이전트별 성과 비교**

| Agent (서버) | Duration (s) | Reward | Exit Code |
|-------------|-------------|--------|-----------|
| secu (10.20.30.1) | **0.150** | +1.3 | 0 |
| siem (10.20.30.100) | 0.153 | +1.3 | 0 |
| opsclaw (localhost) | 0.171 | +1.3 | 0 |
| web (10.20.30.80) | 0.185 | +1.3 | 0 |

secu가 가장 빠르고(0.150s), web이 가장 느리다(0.185s). 이 데이터를 누적하면 agent별 avg_reward와 avg_duration 기반의 성과 점수를 산출할 수 있다. RL UCB1 추천이 현재 상태(low, success_rate=91%)에서 미방문 행동(medium)을 추천하여 정책 다양성 확보를 유도하였다.

### 시나리오 2: 비용 정산 (Chargeback) — 실증

**실증 결과.** 47개 프로젝트, 153 PoW 블록의 축적 데이터를 프로젝트별로 집계하였다.

**표 4. 프로젝트별 비용 정산 (실데이터, 상위 7건)**

| Project | Name | Blocks | Success | Fail | Reward |
|---------|------|--------|---------|------|--------|
| prj_4cc0 | red-tier1-webapp-attack | 12 | 10 | 2 | 10.2 |
| prj_6709 | blue-tier1-defense | 8 | 8 | 0 | 9.4 |
| prj_c9d4 | compare-opsclaw-r1 | 5 | 5 | 0 | 6.5 |
| prj_b2dc | exp-F-seq-N5 | 5 | 5 | 0 | 6.5 |
| prj_e8bb | vwr-agent-benchmark | 4 | 4 | 0 | 5.2 |
| prj_0c77 | compare-opsclaw | 5 | 4 | 1 | 4.2 |
| prj_96cf | exp-G-run-8 | 3 | 3 | 0 | 3.9 |

**전체 집계:** 47 프로젝트, 153 블록, 성공 139, 실패 14, 총 reward 162.6, 태스크당 평균 reward 1.06.

reward 1.0 = ₩1,000으로 가정한 팀별 정산 시뮬레이션:

```
보안팀 (red-t1 + blue-t1):  20 blocks, reward 19.6 → ₩19,600
실험팀 (exp-F/G/B/C/D/E/H): ~80 blocks, reward ~85  → ₩85,000
비교팀 (compare + benchmark): 14 blocks, reward 15.9 → ₩15,900
```

VWR이 **작업 수행의 검증 가능한 영수증** 역할을 하여, 양측(서비스 제공자/소비자)이 동일한 데이터(해시 체인)로 사용량을 확인할 수 있다.

### 시나리오 3: 컴플라이언스 증빙 — 실증

**실증 결과.** "3월 25일 agent benchmark 프로젝트 이력 제출" 시나리오를 replay API로 검증하였다.

```
GET /projects/prj_e8bb1b986ebb/replay →
  4 steps, total_reward=5.2
  [1] syscheck-opsclaw  exit=0 dur=0.171s reward=+1.3 hash=000016c7...
  [2] syscheck-secu     exit=0 dur=0.150s reward=+1.3 hash=000002f9...
  [3] syscheck-web      exit=0 dur=0.185s reward=+1.3 hash=0000d742...
  [4] syscheck-siem     exit=0 dur=0.153s reward=+1.3 hash=0000b67c...

GET /pow/verify →
  valid=True, blocks=153, orphans=0, tampered=[]
```

WHO(agent), WHAT(task_title), WHEN(ts), RESULT(exit_code, duration), PROOF(block_hash), VALUE(reward) 모든 필드를 포함하는 구조화된 감사 증빙이 자동으로 제공된다. 해시 체인 검증으로 153블록 전체에서 부분 변조 미발생을 확인.

### 시나리오 4: 에이전트 마켓플레이스 — 실증 근거

실험 1의 4개 agent 비교 데이터와 RL recommend를 결합하면, 태스크 유형별 최적 agent를 자동 선택하는 마켓플레이스 기반을 확인할 수 있다.

**표 5. RL 추천 결과 (UCB1)**

| 현재 Risk | Success Rate | RL 추천 | 근거 |
|----------|-------------|---------|------|
| low | 91% | **medium** | 미방문 행동 탐색 (UCB 2.79 > Q 1.23) |
| medium | 91% | **low** | Q-value 최고 행동 (Q 1.23) |
| high | 91% | **low** | Q-value 최고 행동 |

RL 엔진이 누적 reward 데이터에서 학습한 정책으로 최적 risk_level을 추천한다. 이를 agent 선택으로 확장하면(agent_id별 독립 Q-table), 동일 태스크 유형에 대해 가장 높은 누적 reward를 가진 agent를 자동 선택하는 마켓플레이스가 가능하다.

### 시나리오 5: SLA 모니터링 — 방향 제시

SLA 모니터링은 reward 추이의 시계열 분석으로 구현 가능하나, 인위적 부하 주입이 필요하여 본 실험에서는 데이터 기반 방향만 제시한다. 현재 데이터에서 태스크당 평균 reward는 1.06이며, 이 값이 특정 임계값(예: 0.7) 이하로 하락하면 SLA 경보를 발생시키는 구조를 설계할 수 있다.

## 5.3 VWR의 한계

| 한계 | 설명 |
|------|------|
| DB 전체 재작성 | 단일 DB에 저장되므로 관리자가 체인 전체를 재작성하면 탐지 불가 |
| 분산 합의 부재 | 외부 검증자 없이 내부 해시 체인만 사용 — 블록체인 수준의 보장은 아님 |
| 보상 함수 설계 의존 | 보상 산출 공식(base + speed + risk)이 작업 가치를 정확히 반영하는지는 도메인 전문가의 검증 필요 |
| 단일 에이전트 편중 | 현재 RL 커버리지 4.2% — 다중 에이전트 환경에서 다양성 확보 필요 |

이러한 한계에도 불구하고, VWR은 **에이전트 작업의 구조화된 기록 + 무결성 체크 + 보상 추적**을 통합하여, 단독 에이전트에는 없는 운영 가시성(operational visibility)을 제공한다.
