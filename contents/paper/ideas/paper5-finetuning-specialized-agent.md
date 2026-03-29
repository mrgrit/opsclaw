---
name: Paper 5 아이디어 — 운영 데이터 기반 특화 SubAgent 파인튜닝
description: 축적된 Evidence/PoW/미션 로그로 서버별 특화 LLM 파인튜닝. 범용→특화 진화 경로.
type: project
---

## 아이디어: 운영 데이터 기반 서버별 특화 SubAgent 파인튜닝

### 진화 경로
```
Phase 1: 범용 모델 + prompt engineering (local_knowledge.json) ← 현재
Phase 2: 범용 모델 + LoRA 파인튜닝 (축적된 미션 로그)
Phase 3: 서버별 완전 특화 모델
  siem-blue:12b  — Wazuh 전문가
  web-red:12b    — 웹앱 공격 전문가
  secu-ops:12b   — nftables/Suricata 전문가
```

### 학습 데이터 (이미 축적됨)
- Evidence 테이블: 153건+ (instruction=command, response=stdout)
- PoW + task_reward: 보상 기반 데이터 선별 가능 (reward > 1.0만)
- 미션 로그: LLM 판단 + 실행 결과 쌍
- local_knowledge: 서버별 도구/경로/경험
- Playbook steps: 검증된 명령 시퀀스

### 데이터셋 변환
```json
{"instruction": "Check Wazuh SIEM for SQLi alerts",
 "response": "sshpass -p1 ssh siem@10.20.30.100 'echo 1 | sudo -S grep -i union /var/ossec/logs/alerts/alerts.json | tail -20'"}
```

### 핵심 연구 질문
- RQ1: 운영 로그로 파인튜닝한 특화 모델이 범용 모델+프롬프트 대비 얼마나 정확한가?
- RQ2: 보상 기반 데이터 선별(reward > 1.0)이 학습 품질에 미치는 영향은?
- RQ3: 소량 데이터(~200건) LoRA 파인튜닝의 효과와 한계는?
- RQ4: 특화 모델의 과적합(이 인프라에만 동작) 위험은 어떻게 측정/완화하는가?

### 필요한 실험
1. Evidence→학습 데이터셋 변환 파이프라인 구축
2. LoRA 파인튜닝 (gemma3:12b 또는 llama3.1:8b 기반)
3. 동일 미션을 범용 vs 특화 모델로 실행 → 성공률/정확도 비교
4. 다른 인프라 환경에서 특화 모델 실행 → 일반화 능력 측정

### 주의점
- 데이터 양 부족 → LoRA/QLoRA 소량 학습
- 과적합 위험 → 교차 검증, 다른 환경 테스트
- 모델 업데이트 주기 관리 (인프라 변경 시 재학습)
- 보안 데이터 노출 위험 (학습 데이터에 패스워드/토큰 포함 가능)

### 상태: 아이디어 단계 — 실험 미수행
