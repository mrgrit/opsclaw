# OpsClaw

> LLM 기반 IT 운영/보안 자동화 Control-Plane 플랫폼

OpsClaw는 자연어 요청을 신뢰할 수 있는 운영 작업으로 바꾸는 플랫폼이다. 프로젝트 단위 접수, 단계별 상태 관리, Asset/SubAgent/Playbook 기반 실행, Evidence/Report 중심 기록, PoW 블록체인 작업증명, 강화학습(RL) 기반 품질 개선을 하나의 시스템에 통합한다.

## 아키텍처

```
                    ┌─────────────────────────────┐
                    │       Central Server :7000    │
                    │  인스턴스관리 / 통합블록체인   │
                    │  CTF / Config / NMS/SMS       │
                    └──────┬──────┬──────┬─────────┘
                           │      │      │
              ┌────────────┘      │      └────────────┐
              v                   v                    v
    ┌──────────────┐    ┌──────────────┐     ┌──────────────┐
    │ Bastion :9000 │    │  CCC :9100   │     │OpsClaw :8000 │
    │  실무 에이전트 │    │  교육 플랫폼  │     │  연구/개발    │
    └──────┬───────┘    └──────┬───────┘     └──────────────┘
           │                   │
     ┌─────┴─────┐      ┌─────┴─────┐
     │ SubAgent  │      │  학생 인프라 │
     │ :8002     │      │  개별 VM    │
     └───────────┘      └───────────┘
```

## 3개 시스템 + 중앙서버

| 시스템 | 포트 | 레포 | 역할 |
|--------|------|------|------|
| **OpsClaw** | :8000 | 이 레포 | 연구/개발 — 전체 기능 모놀리스 |
| **Central Server** | :7000 | 이 레포 `apps/central-server/` | 통합 관리 — 인스턴스/블록체인/CTF/Config/NMS |
| **Bastion** | :9000 | [github.com/mrgrit/bastion](https://github.com/mrgrit/bastion) | 실무 운영/보안 AI 에이전트 |
| **CCC** | :9100 | [github.com/mrgrit/ccc](https://github.com/mrgrit/ccc) | 사이버보안 교육 플랫폼 |

## 핵심 기능

### OpsClaw (연구용)
- **3계층 구조**: Master(:8001) → Manager(:8000) → SubAgent(:8002)
- **프로젝트 라이프사이클**: plan → execute → validate → report → close
- **35개 패키지**: pow_service, rl_service, evidence_service, playbook_engine, prompt_engine, hook_engine, cost_tracker, permission_engine 등
- **블록체인 작업증명(PoW)**: SHA-256, difficulty=4, 284+ 블록
- **강화학습(RL)**: Q-learning + UCB1, 48 상태 x 4 액션
- **교육 포털**: 12과목 180개 교안, 소설 10권, CTF, 커뮤니티, AI 채팅봇
- **에이전트 소셜**: 5개 AI 에이전트가 RSS/Reddit 수집 → 분석 → 커뮤니티 게시

### Central Server (통합 관리)
- **인스턴스 관리**: opsclaw/bastion/CCC 등록, 하트비트, 상태 모니터링
- **통합 블록체인**: 모든 인스턴스 블록 수신 → 통합 검증 → 리더보드
- **CTF 서버**: 문제 관리, 플래그 검증, 스코어보드
- **Central Config**: 49개 설정 (IP/포트/DB/LLM/SSH 등) 중앙 관리
- **NMS/SMS**: 네트워크 도달성, 시스템 메트릭, 알림
- **Slack 연동**: `/opsclaw status|task|nms|labs|battle|leaderboard`

## 인프라

| 서버 | 내부 IP | 외부 IP | 역할 |
|------|---------|---------|------|
| opsclaw | 10.20.30.201 | 192.168.0.107 | Control Plane |
| secu | 10.20.30.1 | 192.168.208.150 | nftables + Suricata IPS |
| web | 10.20.30.80 | 192.168.208.151 | BunkerWeb WAF + JuiceShop |
| siem | 10.20.30.100 | 192.168.208.152 | Wazuh 4.11.2 |
| dgx-spark | - | 192.168.0.105 | GPU + Ollama LLM |

## 기술 스택

- **Backend**: Python 3.11, FastAPI, PostgreSQL 15, LangGraph
- **Frontend**: React 19, TypeScript, Vite
- **LLM**: Ollama (gpt-oss:120b, qwen3.5-coder:122b, nemotron-3-super:120b)
- **Blockchain**: SHA-256 PoW, difficulty=4
- **RL**: Q-learning, epsilon-greedy, UCB1

## Quick Start

```bash
# PostgreSQL
sudo docker compose -f docker/postgres-compose.yaml up -d

# 서비스 기동
./dev.sh all           # 전체 (manager + master + subagent)
./dev.sh manager       # manager-api만

# Central Server
scripts/deploy-central.sh

# 접속
# OpsClaw Portal: http://localhost:8000
# Central:        http://localhost:7000
```

## 연구 논문

- Paper 1: 아키텍처 (3계층 오케스트레이션)
- Paper 2: 보안/모의해킹 (자율 Purple Team)
- Paper 3: 사례연구 (개발 여정)
- Paper 4: 하네스 비교 (Claude Code vs OpsClaw)
- Paper 5: 교육 파이프라인

## License

MIT
