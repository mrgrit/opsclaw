# 실험 재검증 보고서 (2026-04-02)

## 실험 환경
- OpsClaw Manager: localhost:8000
- Master Service: localhost:8001
- SubAgents: localhost:8002, v-secu(192.168.0.108), v-web(192.168.0.110), v-siem(192.168.0.109)
- Ollama: 192.168.0.105:11434 (22 models)
- PostgreSQL: 51 tables
- CTFd: localhost:8080
- Portal: localhost:8000/app/

## 재검증 결과

| # | 실험 | 결과 | 비고 |
|---|------|------|------|
| A | dispatch + execute-plan | ✅ PASS | 3/3 VM 병렬 점검 |
| B | Native 모드 (LLM 자율 계획) | ⚠️ 부분 | Plan OK, 실행 셸 문법 이슈 |
| C | PoW + RL | ⚠️ 부분 | RL train 299ep OK, 가상서버 데이터 미축적 |
| D | 교육 파이프라인 4계층 | ✅ PASS | Education+System+Novel+CTF 4/4 |
| E | 신규 패키지 6개 | ✅ PASS | hook_engine import 수정 후 전부 OK |
| F | RAG + 챗봇 | ✅ PASS | 288문서, SQLi 질문 2,869자 |
| G | Portal (게시판/회원) | ✅ PASS | 7 boards, 10 members, 57 posts |
| H | RL Train + Recommend | ✅ PASS | 299 episodes |
| I | Replay | ✅ PASS | 4 events, reward=5.2 |
| J | CLI (opsclaw dispatch) | ✅ PASS | v-secu hostname OK |
| K | Streaming Chat | ✅ PASS | SSE nftables 응답 OK |

## 수정 사항
1. hook_engine/__init__.py: HookInput export 추가
2. Native 모드: LLM 프롬프트 개선 필요 (향후)
3. PoW: 가상서버에서 작업 축적 필요 (시간이 지나면 해결)

## Bastion 패치 (신규)
- prompt_engine: 7,852자 시스템 프롬프트 동적 생성 ✅
- hook_engine: 10개 이벤트 Hook 시스템 ✅
- tool_validator: JSON Schema 검증 ✅
- cost_tracker: 토큰 비용 추적 ✅
- permission_engine: 다층 퍼미션 ✅
- memory_manager: 자동 추출 + LRU ✅

## 논문 반영 필요 사항
- Paper 1 (아키텍처): 6개 신규 패키지 추가 반영
- Paper 3 (사례연구): 교육 파이프라인 실험 데이터 업데이트
- Paper 4 (하네스 비교): Claude Code 소스 분석(Bastion) 결과 반영
