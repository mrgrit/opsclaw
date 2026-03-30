# 5B. 자율 SubAgent 공방전 (Autonomous Purple Team)

## 5B.1 동기: 상용 모델에서 경량 모델로의 지식 전이

IT 운영 환경에는 루틴한 반복·정기 업무가 다수 존재한다. 이러한 업무를 처음에는 고지능 상용 모델(Claude Code, GPT-4)이 수행하면서 Playbook과 경험을 축적하고, 점차 8B~12B 수준의 오픈 경량 모델로 동일 작업을 전이하여 비용과 의존성을 절감하는 것이 실용적 목표이다.

본 절에서는 이전 보안 실험(Red T1~T4, Blue T1)에서 Claude Code가 축적한 경험·Playbook·문서를 경량 SubAgent(gemma3:12b, llama3.1:8b)에 전이하여, 자율적으로 공방전을 재현하는 실험을 보고한다.

## 5B.2 아키텍처: 자율 미션 루프

기존 아키텍처에서 SubAgent는 Manager로부터 개별 명령을 수신·실행하는 수동 실행기였다. 본 실험에서는 SubAgent에 **자율 미션 루프**(`/a2a/mission`)를 추가하여, 로컬 LLM이 미션 목표와 전이된 지식을 기반으로 자율적으로 행동을 결정·실행·반복한다.

```
Manager (미션 개시):
  1. DB에서 관련 Experience 42건, Playbook 10개, 완료보고 11건 검색
  2. 미션 컨텍스트로 압축하여 SubAgent에 전달
  3. Red SubAgent + Blue SubAgent 동시 출발 (ThreadPoolExecutor)

SubAgent (자율 행동):
  loop (max_steps):
    1. 로컬 LLM에 현재 상황 + 미션 목표 + 전이된 지식 제공
    2. LLM이 다음 명령 결정 (JSON 응답)
    3. bash 실행
    4. 결과를 LLM에 피드백 → 다음 판단
  end

Manager (미션 완료):
  5. 양쪽 결과 수집 → Evidence 기록 + PoW 블록 생성
```

## 5B.3 실험 결과

**프로젝트:** prj_11fc984d6cb5
**총 소요:** ~38초 (Red 35.3s, Blue 36.0s 동시)

### Red Team (gemma3:12b, 4 steps)

| Step | Action | 성공 | 비고 |
|------|--------|:----:|------|
| 1 | 서버 헤더 정찰 (curl -I) | ✅ | X-Recruiting, CORS 정보 획득 |
| 2 | SQLi 로그인 시도 | ❌ | JSON 이스케이핑 오류 (exit=2) |
| 3 | SQLi 재시도 (구문 수정) | ❌ | JSON 파싱 에러 반환 |
| 4 | 응답 파싱 실패 | ❌ | LLM JSON 출력 형식 오류 |

**Red 점수: 1/6** (이전 Claude Code: 5.5/6)

### Blue Team (llama3.1:8b, 8 steps)

| Step | Action | 성공 | 비고 |
|------|--------|:----:|------|
| 1 | Wazuh 상태 + 경보 수집 | ✅ | wazuh-manager active, sudo 경보 확인 |
| 2 | 경보 로그 분석 | ✅ | T1548.003 (Privilege Escalation) 경보 식별 |
| 3~8 | 탐지 룰 생성 시도 (×6) | ❌ | `wazuh-api create-rule` 존재하지 않는 명령 반복 |

**Blue 점수: 3/16** (이전 Claude Code: 12/16)

### VWR 기록

| 항목 | 값 |
|------|-----|
| Evidence | 11건 (Red 3 + Blue 8) |
| PoW 블록 | 11블록 |
| Total Reward | -1.8 (성공 4건: +5.2, 실패 7건: -7.0) |

## 5B.4 분석: 경량 모델의 능력 경계

**표 6. 상용 모델 vs 경량 모델 성과 비교**

| 능력 | Claude Code (Opus 4) | gemma3:12b | llama3.1:8b |
|------|:---:|:---:|:---:|
| 기본 정찰 (curl, nmap) | ✅ | ✅ | — |
| SSH 원격 명령 | ✅ | ✅ | ✅ |
| SIEM 경보 수집 | ✅ | — | ✅ |
| SQLi 페이로드 구성 | ✅ | ❌ (이스케이핑) | — |
| 탐지 룰 파일 편집 | ✅ | — | ❌ (CLI 환각) |
| 복잡한 다단계 추론 | ✅ | △ | ❌ |

경량 모델은 **단순·반복 작업**(정찰, 상태 확인, 로그 수집)은 수행 가능하지만, **복잡한 페이로드 구성**이나 **도구 CLI 정확성**에서 한계를 보인다.

## 5B.5 지식 전이의 단계적 모델

실험 결과를 바탕으로 다음의 단계적 지식 전이 모델을 제안한다:

```
Phase 1: 상용 대형 모델 → 복잡한 작업 수행 + Playbook 생성 + 경험 축적
     ↓ (Playbook화: 성공한 작업을 결정론적 스크립트로 고정)
Phase 2: 경량 모델 → Playbook 기반 자율 실행 (판단은 LLM, 실행은 Playbook)
     ↓ (경험 축적: 경량 모델의 실행 결과도 VWR로 기록)
Phase 3: 경량 모델 → 새로운 경험 기반 RL 정책 개선
     ↓ (순환)
Phase 1로 복귀 (새로운 유형의 작업이 등장할 때만)
```

이 모델에서 핵심은 **Playbook이 지식 전이의 매개체**라는 점이다. 상용 모델이 생성한 Playbook을 경량 모델이 그대로 실행하면 100% 재현이 가능하다(실험 G). 경량 모델의 역할은 상황 판단(어떤 Playbook을 실행할지)에 한정되며, 복잡한 페이로드 구성은 Playbook에 위임된다.

## 5B.6 동시 공방의 구조적 의의

Red(35.3s)와 Blue(36.0s)가 **서로 다른 LLM 모델**로 동시에 자율 행동한 것은 단독 에이전트나 수동 테스트로는 불가능한 시나리오이다:

- Red(gemma3:12b)가 공격을 시도하는 **같은 시점에** Blue(llama3.1:8b)가 SIEM 경보를 수집
- 두 모델의 학습 데이터가 완전히 다르므로 (Google vs Meta) 공정한 공방
- 모든 행동이 VWR로 자동 기록되어 사후 타임라인 재구성 가능

이 구조는 **24/7 자동 Purple Team 운용**의 기반이 된다: 경량 SubAgent가 상시 공방을 실행하고, 새로운 취약점이 발견되면 상용 모델이 정밀 분석 + Playbook 생성에 개입하는 계층적 운용.

## 5B.7 분산 지식 아키텍처: 로컬 경험 캐시

자율 미션의 한계(Blue의 CLI 환각, Red의 경로 미인식)를 해결하기 위해, 각 SubAgent가 자기 서버에서 축적한 경험을 **로컬 지식 파일**(local_knowledge.json)로 보유하는 분산 지식 아키텍처를 구현하였다.

```
Manager DB (중앙) ─── 전체 통합 지식 (master copy)
     │ 미션 시작 시 관련 지식 주입
     ├── opsclaw SubAgent ─── opsclaw.json (Red 공격 경험, 네트워크맵)
     ├── siem SubAgent    ─── siem.json (Wazuh 경로, 룰 템플릿, logtest)
     └── web SubAgent     ─── web.json (취약점, sudo, JuiceShop 경로)
```

각 로컬 지식 파일은 다음을 포함한다:
- **tools**: 서버별 실제 명령어·경로 (예: `wazuh_custom_rules: /var/ossec/etc/rules/local_rules.xml`)
- **experiences**: 이전 미션에서 성공한 작업 이력
- **rule_templates**: 재사용 가능한 탐지 룰 템플릿 (Blue용)
- **network_map**: 내부망 서버·포트 정보 (Red용)

### 분산 지식의 효과

**표 7. 로컬 지식 주입 전후 비교**

| 항목 | 지식 없음 | 로컬 지식 주입 | 개선 |
|------|---------|-------------|------|
| Blue SSH 접속 | ❌ `ssh siem@...` (실패) | ✅ `sshpass -p1 ssh ...` | SSH 패턴 학습 |
| Blue Wazuh 상태 | ❌ 미확인 | ✅ `systemctl status wazuh-manager` | 경로 인식 |
| Blue alerts 경로 | ❌ 모름 | ✅ `/var/ossec/logs/alerts/alerts.json` | 도구 경로 참조 |
| Blue 룰 생성 | ❌ `wazuh-api create-rule` (환각) | △ tools 키 혼동 | 부분 개선 |
| Red 공격 시도 횟수 | 4 steps | **8 steps** | 경험 참조로 지속성 향상 |
| Red API 접근 | ❌ 미도달 | △ `/api/Users` 시도 | 새 공격 경로 탐색 |
| 자동 저장 | — | ✅ 미션 완료 시 자동 | 누적 학습 기반 |

### 자동 학습 루프

미션 완료 시 성공한 명령이 local_knowledge.json에 자동 추가된다. 이를 통해 SubAgent는 미션을 반복할수록 자기 서버의 환경을 더 정확히 이해하게 된다:

```
미션 1: SSH 접속 패턴 학습 → siem.json에 저장
미션 2: siem.json 참조 → Wazuh 상태 확인 성공 → alerts 경로 학습
미션 3: alerts 분석 성공 → 룰 생성 명령 학습
...반복...
미션 N: 서버의 모든 도구·경로·패턴을 로컬에 보유 → 자율 운영 가능
```

이 점진적 학습은 RL 보상과 결합되어, 고보상 미션의 경험이 우선적으로 축적된다.
