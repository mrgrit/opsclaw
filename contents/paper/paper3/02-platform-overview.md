# 2. 플랫폼 개요 (Platform Overview)

OpsClaw는 IT 운영·보안 자동화를 위한 에이전트 하네스 플랫폼이다. 상세 아키텍처는 별도 논문 [Paper 1]에서 기술하며, 본 장에서는 사례 연구에 필요한 핵심 요소만 요약한다.

## 2.1 아키텍처 요약

OpsClaw는 **Master→Manager→SubAgent** 3계층 위임 아키텍처를 채택한다.

- **Master** (LLM): 자연어 요청 분석, 작업 계획 수립, 결과 해석
- **Manager** (API :8000): 프로젝트 라이프사이클, 증적 기록, 보상 산출, Playbook 실행
- **SubAgent** (Runtime :8002): 대상 서버에서 명령 실행, 결과 반환

두 가지 실행 모드를 지원한다: Mode A(내장 LLM이 계획)와 Mode B(외부 AI가 API 직접 호출). 본 사례에서는 주로 Mode B(Claude Code as External Master)를 사용하였다.

## 2.2 기술 스택

| 구성 요소 | 기술 |
|----------|------|
| 언어 | Python 3.11 |
| API 프레임워크 | FastAPI + Uvicorn |
| 상태 머신 | LangGraph (StateGraph) |
| 데이터베이스 | PostgreSQL 15 (Docker) |
| 해시 체인 | SHA-256 PoW (difficulty=4) |
| 강화학습 | Q-learning + UCB1 (48 states × 4 actions) |
| 검색 | PostgreSQL FTS (to_tsvector) |

## 2.3 인프라 구성

| 서버 | IP | 역할 |
|------|----|------|
| opsclaw | 10.20.30.201 | Control plane |
| secu | 10.20.30.1 | nftables + Suricata IPS |
| web | 10.20.30.80 | BunkerWeb WAF + JuiceShop |
| siem | 10.20.30.100 | Wazuh 4.11.2 SIEM |

## 2.4 규모

| 항목 | 수치 |
|------|------|
| 핵심 패키지 | 13개 |
| 서비스 | 5개 |
| DB 테이블 | 17개 |
| DB 마이그레이션 | 13개 |
| API 엔드포인트 | ~40개 |
| 개발 기간 | M0~M25 (약 25 마일스톤) |
