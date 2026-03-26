# DGX Spark Ollama 업데이트 보고서

**날짜:** 2026-03-26
**프로젝트:** prj_acf8ebe849ed (dgx-ollama-update)
**실행 방식:** OpsClaw Manager API → DGX Spark SubAgent (192.168.0.105:8002)

## 업데이트 결과

| 항목 | Before | After |
|------|--------|-------|
| Ollama 버전 | 0.16.1 (2026-02-13) | **0.18.2** (2026-03-18) |
| 설치 방법 | `curl install.sh \| sudo sh` | 동일 |
| 모델 | 20개 정상 | 20개 정상 |

## 실행 이력 (OpsClaw evidence 21건)

1. 현재 버전 확인 → 0.16.1
2. install.sh 실행 (sudo 없이) → 버전 변화 없음
3. install.sh 재실행 (sudo 포함) → **0.18.2 업데이트 성공**
4. 서비스 상태 확인 → active (running)
5. gemma3:12b 추론 테스트 → 성공
6. llama3.1:8b 추론 테스트 → 성공

## 비고
- aarch64 환경에서 sudo 없이 install.sh 실행 시 `/usr/local/bin/ollama` 덮어쓰기 불가
- sudo 암호: cert1.2/ (`echo cert1.2/ | sudo -S bash -c "..."` 패턴)
- Ollama 0.18.2 신기능: Nemotron-3-Super 지원, web search/fetch 플러그인
