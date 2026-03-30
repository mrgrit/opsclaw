# 비교 실험 결과: OpsClaw vs Claude Code (공정 비교)

**실행일:** 2026-03-25
**태스크:** 다중 서버 운영 점검 5건
**서버:** opsclaw(localhost), secu(10.20.30.1), web(10.20.30.80), siem(10.20.30.100)
**OpsClaw 프로젝트:** prj_c9d49578ce2d

---

## 태스크 구성

| # | 태스크 | 대상 서버 | 명령 |
|---|--------|---------|------|
| 1 | 시스템 현황 | opsclaw | `hostname && uptime && uname -a` |
| 2 | 디스크 사용량 | secu | `df -h` |
| 3 | 메모리/프로세스 | web | `free -m && ps aux --sort=-rss \| head -10` |
| 4 | 네트워크 포트 | siem | `ss -tlnp` |
| 5 | 보안 점검 | web | `last -10 && sudo -l` |

---

## Round 1: 속도 비교 (양쪽 모두 병렬 허용)

| 방식 | 순차 (ms) | 병렬 (ms) |
|------|----------|----------|
| **OpsClaw** (execute-plan, parallel=true) | — | **570** |
| **Claude Code** (SSH 직접) | 1,908 | **414** |

**분석:** Claude Code 병렬 SSH(414ms)가 OpsClaw(570ms)보다 **156ms (27%) 빠르다.** OpsClaw의 오버헤드는 API 요청 처리, evidence 기록(5건), PoW 블록 생성(5개), reward 산출(5건)에 기인한다. 이는 하네스가 속도가 아닌 다른 차원에서 가치를 제공함을 보여준다.

---

## Round 2: 7차원 비교

| # | 차원 | OpsClaw | Claude Code | 차이 |
|---|------|---------|-------------|------|
| D1 | **실행 시간** (병렬) | 570ms | 414ms | CC가 27% 빠름 |
| D2 | **증적 자동 기록** | evidence 5건 + PoW 5블록 = **10건** | **0건** (터미널 로그만) | +10건 |
| D3 | **위변조 방지** | verify_chain: valid=True, 149블록, tampered=0 | **불가** | 해시 체인 보장 |
| D4 | **재현성** | Playbook 또는 동일 tasks 배열로 **1 API call 재실행** | 히스토리 복사 필요 | 구조적 재현 |
| D5 | **프로젝트 추적** | project lifecycle + replay(5 steps, reward 6.5) | **없음** | 전 과정 추적 |
| D6 | **RL 정책** | UCB1 추천: medium (미방문 탐색) | **없음** | 자율 학습 |
| D7 | **완료 보고** | completion-report 자동 생성 | **없음** (수동 작성) | 자동화 |

---

## Round 3: OpsClaw 상세 증적

### Evidence Summary
```json
{
  "total": 5,
  "success_count": 5,
  "failure_count": 0,
  "success_rate": 1.0,
  "first_at": "2026-03-25T06:40:07.573891Z",
  "last_at": "2026-03-25T06:40:07.632012Z"
}
```

### PoW Chain Verification
```json
{
  "agent_id": "http://localhost:8002",
  "valid": true,
  "blocks": 149,
  "orphans": 0,
  "tampered": []
}
```

### Replay Timeline
| order | title | exit_code | duration_s | reward |
|-------|-------|-----------|-----------|--------|
| 1 | 시스템현황-opsclaw | 0 | 0.197 | +1.3 |
| 2 | 디스크사용량-secu | 0 | 0.168 | +1.3 |
| 3 | 메모리프로세스-web | 0 | 0.224 | +1.3 |
| 4 | 네트워크포트-siem | 0 | 0.158 | +1.3 |
| 5 | 보안점검-web | 0 | 0.156 | +1.3 |
| **합계** | | | | **6.5** |

### RL Recommend (UCB1)
```json
{
  "state": 9,
  "state_desc": {"risk_level":"low", "success_rate":0.906, "task_order":1},
  "recommended_risk_level": "medium",
  "exploration": "ucb1",
  "ucb_values": {"low":1.31, "medium":2.79, "high":2.79, "critical":2.79}
}
```
→ UCB1이 미방문 행동(medium)을 추천하여 정책 다양성 확보

---

## 핵심 결론

### 1. 속도는 하네스의 장점이 아니다
Claude Code 병렬 SSH가 27% 더 빠르다. 하네스의 오케스트레이션 오버헤드(API, evidence, PoW)는 순수 실행 속도에서 불리하다. **이전 비교(3.4x)는 Claude Code 순차 vs OpsClaw 병렬의 불공정 비교였음을 확인.**

### 2. 하네스의 진짜 가치: 증적·추적·학습
| 가치 | 설명 |
|------|------|
| **감사 추적** | 10건 자동 증적 (evidence + PoW), 위변조 100% 탐지 |
| **프로젝트 추적** | lifecycle, replay, completion-report |
| **자율 학습** | RL reward → policy → UCB1 추천 |
| **구조적 재현** | 동일 tasks 배열 또는 Playbook으로 재실행 |

### 3. 하네스 프리미엄 = "실행 후" 가치
순수 실행(명령 전송→결과 수신)에서는 직접 SSH가 빠르다. 하네스의 가치는 실행 "후"에 발생한다: 증적 기록, 위변조 방지, 보상 산출, 경험 축적, 정책 학습, 타임라인 재구성, 완료 보고. 이는 **1회성 작업보다 반복·감사·학습이 필요한 운영 환경**에서 진가를 발휘한다.
