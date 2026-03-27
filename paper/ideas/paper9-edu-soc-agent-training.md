---
name: Paper 9 아이디어 — 자율 에이전트 기반 SOC 인력 양성
description: Agent Daemon이 실시간 자극을 생성하고 학생이 관제/분석/대응. AI 튜터가 실시간 피드백.
type: project
---

## 핵심 주장
Agent Daemon(자극 생성기)이 실시간 보안 이벤트를 발생시키고, 학생이 SOC 분석가로서 탐지·분석·대응하는 과정을 OpsClaw가 자동 평가하는 SOC 교육 시스템.

## 시나리오
1. Agent Daemon이 web 서버에 랜덤 공격 자극 발생 (SQLi, 브루트포스, 포트스캔)
2. 학생은 Wazuh SIEM에서 경보를 확인하고 분석
3. 학생이 OpsClaw를 통해 대응 조치 실행 (룰 생성, IP 차단 등)
4. 모든 행동이 VWR로 기록 → TTD/MTTR 자동 측정 → 채점

## 차별점
- 기존 SOC 교육: 정적 로그 파일 분석 (실시간성 없음)
- 제안: 실시간 자극 → 실시간 탐지/대응 → 자동 평가

## 필요 실험
- 자극 시나리오 20가지 이상 구성
- 학생 그룹 대상 SOC 훈련 실시
- TTD/MTTR 측정 + 학습 곡선 분석

## 대상 학회
보안 교육: USENIX ASE, ACM CCS Education Workshop
SOC: FIRST Conference, SANS Workshops
