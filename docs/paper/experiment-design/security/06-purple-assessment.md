# Purple Team: 종합 평가 + 반복 개선 사이클

## 개요

Red Team 공격 → Blue Team 방어 → 재공격 → 재방어 사이클을 반복하며,
OpsClaw 하네스가 이 반복 루프에서 얼마나 효율적인지 비교 평가.

---

## Purple Team 역할

1. **Red 결과 전달:** 성공한 공격 기법 + 우회 방법을 Blue에게 전달
2. **Blue 검증:** 생성된 룰이 실제로 탐지하는지 재공격으로 검증
3. **갭 분석:** 미탐지 공격 기법 식별 → 추가 룰 요구
4. **ATT&CK 매핑:** 탐지 커버리지를 MITRE Navigator에 매핑

---

## 반복 사이클 (Round)

### Round 1: 초기 공격 + 초기 방어

```
Red: Tier 1~4 공격 실행 (16개 stage)
Blue: SIEM 경보 → 탐지 룰 생성 (SIGMA + Suricata + Wazuh custom)
Purple: 탐지 성공/실패 매핑
```

### Round 2: 적응 공격 + 강화 방어

```
Red: Round 1에서 탐지되지 않은 기법만 재실행 + 변형
Blue: 미탐지 기법 분석 → 추가 룰 작성
Purple: 커버리지 변화 측정
```

### Round 3: 최종 평가

```
Red: 전체 Tier 1~4 재실행 (변형 포함)
Blue: 전체 룰셋 기반 탐지
Purple: 최종 커버리지, 점수, 보고서
```

---

## OpsClaw에서의 Purple Team 운용

### 프로젝트 구조

```
purple-assessment (프로젝트)
  ├── Round 1
  │   ├── red-execute-plan (공격 태스크)
  │   ├── blue-execute-plan (방어 태스크)
  │   └── purple-verify-plan (검증 태스크)
  ├── Round 2 (적응)
  │   ├── red-adapted-plan
  │   ├── blue-hardened-plan
  │   └── purple-verify-plan
  └── Round 3 (최종)
```

### OpsClaw 고유 이점

```bash
# 1) RL 추천으로 최적 방어 전략 선택
curl "http://localhost:8000/rl/recommend?agent_id=http://localhost:8002&risk_level=high&exploration=ucb1"
# → 이전 Round 결과 기반으로 최적 risk_level 추천

# 2) 이전 Round 경험이 RAG로 자동 참조
curl -X POST http://localhost:8000/chat -d '{
  "message": "Tier 2 DNS 터널링 공격에 대한 탐지 룰을 추천해줘",
  "context_type": "project",
  "context_id": "purple-round1-prj-id"
}'
# → Round 1 경험이 RAG로 주입되어 더 정확한 답변

# 3) 병렬 검증 (Red+Blue 동시 실행)
curl -X POST ".../execute-plan" -d '{
  "tasks": [
    {"order":1,"title":"red-replay-sqli","instruction_prompt":"...","risk_level":"high","subagent_url":"http://localhost:8002"},
    {"order":2,"title":"blue-check-alert","instruction_prompt":"...","risk_level":"low","subagent_url":"http://localhost:8002"}
  ],
  "parallel": true
}'
```

---

## ATT&CK 커버리지 매핑

### 탐지 대상 기법 (16개)

| ID | 기법 | Tier | Round 1 | Round 2 | Round 3 |
|----|------|------|---------|---------|---------|
| T1595.002 | Vulnerability Scanning | 1 | | | |
| T1190 | Exploit Public-Facing App | 1 | | | |
| T1059.004 | Unix Shell | 1 | | | |
| T1505.003 | Web Shell | 1 | | | |
| T1046 | Network Service Scanning | 2 | | | |
| T1572 | Protocol Tunneling | 2 | | | |
| T1048.003 | Exfil Over Unencrypted | 2 | | | |
| T1071.001 | Application Layer Protocol | 2 | | | |
| T1548.001 | Setuid/Setgid | 3 | | | |
| T1053.003 | Cron | 3 | | | |
| T1136.001 | Create Local Account | 3 | | | |
| T1070.004 | File Deletion | 3 | | | |
| T1562.001 | Disable Security Tools | 4 | | | |
| T1027 | Obfuscated Files | 4 | | | |
| T1562.006 | Indicator Blocking | 4 | | | |
| T1036.005 | Masquerading | 4 | | | |

**기대:**
- Round 1: 50~60% 탐지 (기존 룰)
- Round 2: 70~80% 탐지 (적응 룰 추가)
- Round 3: 85~95% 탐지 (최종 강화)

---

## OpsClaw vs 비교대상 — Purple Team 효율 비교

| 지표 | OpsClaw | Claude Code | Codex |
|------|---------|-------------|-------|
| Round간 경험 전달 | RAG 자동 (experience DB) | 수동 (대화 컨텍스트 의존) | 수동 |
| Red→Blue 정보 공유 | evidence DB + completion-report | 텍스트 복사/붙여넣기 | 텍스트 |
| 커버리지 추적 | PoW 블록 + task_reward 분석 | 수동 스프레드시트 | 수동 |
| 반복 비용 | Playbook 재실행 (1 API call) | 전체 재타이핑 | 전체 재타이핑 |
| 검증 자동화 | execute-plan parallel | 순차 수동 | 순차 수동 |
| 최종 보고서 | auto completion-report + PoW timeline | 수동 작성 | 수동 작성 |

---

## 최종 보고서 체크리스트

Purple Team 최종 보고서에 포함되어야 할 항목:

- [ ] ATT&CK 커버리지 히트맵 (Round별)
- [ ] 탐지 시간(TTD) 분포 (공격→경보)
- [ ] 룰 생성 시간 분포 (경보→대응)
- [ ] 검증 결과 (재공격 시 탐지율)
- [ ] False Positive Rate
- [ ] 3자 비교 결과 (점수, 시간, 증적)
- [ ] 하네스 프리미엄 분석 (OpsClaw만의 이점)
- [ ] 개선 권고사항
