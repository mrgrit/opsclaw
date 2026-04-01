# 전 과목 교안 실습 검증 보고서 (2026-04-02)

## 결과: 10과목 × 3주차 = 30/30 ALL PASS ✅

| # | 과목 | W01 | W08 | W15 | 검증상세 | 수정사항 |
|---|------|-----|-----|-----|---------|---------|
| C1 | 사이버공격/해킹 | ✅ nmap | ✅ CTF API | ✅ SQLi | 실행 확인 | W15 URL 수정 |
| C2 | 보안솔루션 운영 | ✅ nftables | ✅ Suricata | ✅ Wazuh | 실행 확인 | - |
| C3 | 웹취약점 점검 | ✅ HTTP headers | ✅ SQLi bypass | ✅ Product API | 실행 확인 | - |
| C4 | 컴플라이언스 | ✅ SSH audit | ✅ PW policy | ✅ Service inventory | 실행 확인 | $srv 변수 수정 |
| C5 | SOC 관제 | ✅ Wazuh status | ✅ auth.log | ✅ Blue Team env | 실행 확인 | - |
| C6 | 클라우드/컨테이너 | ✅ docker ps | ✅ docker inspect | ✅ OpsClaw dispatch | 실행 확인 | - |
| C7 | AI 보안 자동화 | ✅ Ollama models | ✅ OpsClaw lifecycle | ✅ execute-plan | 실행 확인 | - |
| C8 | AI Safety | ✅ Prompt injection | ✅ Jailbreak test | ✅ Model listing | 실행 확인 | - |
| C9 | 자율보안시스템 | ✅ API health | ✅ CTF execute-plan | ✅ PoW+RL verify | W05,06,10,11 수정 | Playbook/Schedule/Notification API 수정 |
| C10 | AI보안에이전트 | ✅ Ollama chat | ✅ Security scan | ✅ Full lifecycle | W01,05 수정 | project ID 추출 14곳 수정 |

## Course 9 (자율보안시스템) 검증 상세
- **1차 검증 (W01-08)**: dispatch, execute-plan, PoW, RL 모두 PASS
  - 수정: W05 Playbook step 필드명(tool→type, description→name)
  - 수정: W06 /pow/verify에 agent_id 파라미터 추가
- **2차 검증 (W09-15)**: Experience, Schedule, Watcher, Blue Agent 모두 PASS
  - 수정: W10 Schedule/Watcher 생성 API 필드명
  - 수정: W11 /notifications → /notifications/channels 엔드포인트
- **전체 재검증**: W01 API health ✅, W08 CTF execute-plan ✅, W15 PoW+RL ✅

## Course 10 (AI보안에이전트) 검증 상세
- **1차 검증 (W01,02,05,07,09)**: Ollama, Tool Calling, Native mode, dispatch 모두 PASS
  - 수정: project ID 추출 경로 `['id']` → `['project']['id']` 14곳
- **전체 재검증**: W01 Ollama chat ✅, W08 Security scan ✅, W15 Full lifecycle ✅

## 교안 보강
- 10과목 W01에 "실습 목적/배우는것/결과해석/실전활용" 설명 박스 추가
- 각 과목 디렉토리에 VERIFIED.md 검증 완료 마크 생성
