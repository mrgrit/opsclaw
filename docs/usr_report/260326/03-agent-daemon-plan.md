# Agent Daemon 구현 + 실험 계획

**날짜:** 2026-03-26
**목표:** SubAgent가 자율적으로 서버를 파악하고, 상시 감시하며, 보안 이벤트에 자율 대응하는 Agent Daemon 구현 및 실증

---

## Phase 1: 구현

### 1.1 Explore Mission (/a2a/explore)
- 서버 투입 시 1회 실행
- 서버 환경 자동 파악 (프로세스, 서비스, 포트, 디스크, 네트워크)
- 감시 대상(watch_targets) 자동 결정
- 정상 기준(baseline) 자동 설정
- 결과를 local_knowledge.json에 저장

### 1.2 Daemon Loop (/a2a/daemon)
- explore 결과 기반 상시 감시
- 이벤트 드리븐: inotify 또는 적응적 폴링
- 이상 감지 시 LLM 판단 → 자율 조치
- 조치 결과 Manager에 콜백 (VWR 기록)
- 긴급 시 Slack 알림

### 1.3 Manager 자극 생성기 (/projects/{id}/stimulate)
- 대상 서버에 무작위 보안 이벤트 발생
- 예: SQLi 요청, 포트 스캔, 비정상 로그인, 파일 변조
- Daemon이 자율 탐지하는지 검증용

## Phase 2: 인프라 정리

### 2.1 Web 서버
- BunkerWeb/ModSecurity + JuiceShop 상태 확인
- 문제 있으면 ModSecurity + JuiceShop으로 단순화

### 2.2 SIEM
- Wazuh manager active 확인 완료
- agent 연결 상태 재확인

## Phase 3: 실험

### 3.1 Explore → Daemon 기동
- siem SubAgent에 explore → daemon 시작
- web SubAgent에 explore → daemon 시작

### 3.2 자극 발생 + 자율 탐지
- Manager가 web에 SQLi 공격 발생
- Manager가 siem에 비정상 로그 주입
- Daemon이 자율 탐지하는지 확인
- Daemon의 대응 행동 기록

### 3.3 결과 수집
- evidence/PoW 기록 확인
- Daemon 행동 로그 분석
- 탐지 시간(TTD) 측정

## Phase 4: 논문 + 커밋

### 논문 위치 결정
- Paper 3에 추가 (실운영 사례) 또는 새 Paper
- Related Work: 탑티어만

### Git push
- 구현 코드 + 실험 결과 + 논문
