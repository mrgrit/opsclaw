# OpsClaw 운영 매뉴얼 — 목차

> **버전**: 1.0
> **최종 수정**: 2026-03-30
> **대상 독자**: SOC 분석가, 보안 엔지니어, DevOps, 정보보안 전공 학생

---

## 매뉴얼 구성

OpsClaw 매뉴얼은 아래 5개 섹션으로 구성된다.
각 섹션은 독립적으로 읽을 수 있으나, 처음 사용자라면 **Getting Started** 부터 순서대로 읽기를 권장한다.

---

## 1. Getting Started (시작하기)

OpsClaw를 처음 접하는 사용자를 위한 기초 가이드.

| 파일 | 제목 | 설명 |
|------|------|------|
| `getting-started/01-overview.md` | OpsClaw 개요 | 시스템 소개, 핵심 개념, 아키텍처 다이어그램, 대상 사용자 |
| `getting-started/02-installation.md` | 설치 가이드 | 사전 요구사항, 클론, DB 마이그레이션, 서비스 기동, 헬스체크 |
| `getting-started/03-quickstart.md` | 빠른 시작 | 5분 안에 첫 프로젝트 실행하기 (Native + Claude Code 모드) |

---

## 2. Native Mode (Mode A: 내장 LLM 모드)

OpsClaw 자체 LLM(Ollama)이 작업 계획을 수립하고 자동 실행하는 모드.

| 파일 | 제목 | 설명 |
|------|------|------|
| `native-mode/01-overview.md` | Native 모드 개요 | 동작 원리, 사용 시기, Ollama LLM 구성, 제약 사항 |
| `native-mode/02-cli-guide.md` | CLI 레퍼런스 | opsclaw 명령어 전체 참조 (run, dispatch, list, status, replay, servers) |
| `native-mode/03-master-service.md` | Master Service API | :8001 엔드포인트 상세 (master-plan, review, replan, escalate) |

---

## 3. Claude Code Mode (Mode B: 외부 AI 오케스트레이션)

Claude Code가 Manager API를 직접 호출하여 작업을 오케스트레이션하는 모드.

| 파일 | 제목 | 설명 |
|------|------|------|
| `claude-code-mode/01-overview.md` | Claude Code 모드 개요 | 동작 원리, 사용 시기, 장점, CLAUDE.md 역할 |
| `claude-code-mode/02-api-guide.md` | Manager API 가이드 | 전체 API 레퍼런스 (프로젝트 라이프사이클, Evidence, PoW, RL) |

---

## 4. Architecture (아키텍처) — 예정

| 파일 | 제목 | 설명 |
|------|------|------|
| `architecture/01-system-design.md` | 시스템 설계 | 3계층 구조, 메시지 흐름, 데이터 모델 |
| `architecture/02-pow-chain.md` | PoW 체인 | Proof-of-Work 블록체인 무결성 보장 메커니즘 |
| `architecture/03-rl-engine.md` | 강화학습 엔진 | Q-learning 기반 risk_level 최적화 |

---

## 5. Operations (운영) — 예정

| 파일 | 제목 | 설명 |
|------|------|------|
| `operations/01-subagent-deploy.md` | SubAgent 배포 | 원격 서버에 SubAgent 배포/업데이트 절차 |
| `operations/02-monitoring.md` | 모니터링 | Wazuh, 로그 수집, 알림 설정 |
| `operations/03-troubleshooting.md` | 문제 해결 | 자주 발생하는 오류와 해결 방법 |

---

## 6. Reference (레퍼런스) — 예정

| 파일 | 제목 | 설명 |
|------|------|------|
| `reference/01-tools-skills.md` | Tool/Skill 목록 | 등록된 Tool 6종, Skill 6종 상세 |
| `reference/02-env-variables.md` | 환경변수 | 전체 환경변수 목록과 기본값 |
| `reference/03-db-schema.md` | DB 스키마 | 마이그레이션 파일 기반 테이블 구조 |

---

## 7. Tutorials (실습) — 예정

| 파일 | 제목 | 설명 |
|------|------|------|
| `tutorials/01-server-onboarding.md` | 서버 온보딩 | 신규 서버를 OpsClaw에 등록하고 점검하기 |
| `tutorials/02-security-audit.md` | 보안 점검 | TLS/방화벽/IDS 점검 자동화 |
| `tutorials/03-incident-response.md` | 사고 대응 | Wazuh 알림 기반 자동화된 사고 대응 |

---

## 8. Education (교육) — 예정

| 파일 | 제목 | 설명 |
|------|------|------|
| `education/01-course-catalog.md` | 교육과정 카탈로그 | 8개 코스, 120개 강의 목록 |
| `education/02-ctfd-guide.md` | CTFd 실습 가이드 | CTF 문제 풀이를 통한 실전 학습 |

---

## 인프라 구성 요약

### 물리 서버

| 서버 | IP | 역할 | SubAgent URL |
|------|----|------|--------------|
| opsclaw | 192.168.208.142 | Control Plane (Manager, Master, SubAgent) | http://localhost:8002 |
| secu | 192.168.208.150 | nftables 방화벽 + Suricata IPS | http://192.168.208.150:8002 |
| web | 192.168.208.151 | BunkerWeb WAF + JuiceShop | http://192.168.208.151:8002 |
| siem | 192.168.208.152 | Wazuh 4.11.2 SIEM | http://192.168.208.152:8002 |
| dgx-spark | 192.168.0.105 | GPU + Ollama LLM | http://192.168.0.105:8002 |

### 가상 서버 (실습용)

| 서버 | IP | 역할 | SubAgent URL |
|------|----|------|--------------|
| v-secu | 192.168.0.108 | 가상 방화벽/IPS | http://192.168.0.108:8002 |
| v-web | 192.168.0.110 | 가상 웹 서버 | http://192.168.0.110:8002 |
| v-siem | 192.168.0.109 | 가상 SIEM | http://192.168.0.109:8002 |

### 서비스 포트

| 서비스 | 포트 | 설명 |
|--------|------|------|
| Manager API | 8000 | 주 진입점 — 모든 외부 호출은 여기로 |
| Master Service | 8001 | Native 모드 전용 — LLM 계획 수립 |
| SubAgent Runtime | 8002 | 명령 실행 — Manager를 통해서만 접근 |
| PostgreSQL | 5432 | 데이터 저장소 (Docker) |
| Ollama | 11434 | LLM 추론 (dgx-spark) |

---

## 빠른 링크

- **소스 코드**: https://github.com/mrgrit/opsclaw
- **API 인증 키**: `X-API-Key: opsclaw-api-key-2026`
- **환경 설정**: `.env` 파일 (`cp .env.example .env`)
- **개발 실행**: `./dev.sh all`

---

## 표기 규칙

- `$OPSCLAW_API_KEY` — 환경변수 참조
- `{project_id}` — API 경로의 동적 파라미터
- `:8000` — 포트 번호 (http://localhost:8000)
- `low | medium | high | critical` — risk_level 선택지

---

## 문서 기여

매뉴얼은 `contents/manual/` 디렉토리에 Markdown으로 관리된다.
새 문서를 추가할 때는 이 인덱스 파일에도 항목을 추가한다.

```
contents/manual/
  00-index.md              ← 이 파일
  getting-started/
    01-overview.md
    02-installation.md
    03-quickstart.md
  native-mode/
    01-overview.md
    02-cli-guide.md
    03-master-service.md
  claude-code-mode/
    01-overview.md
    02-api-guide.md
  architecture/
  operations/
  reference/
  tutorials/
  education/
```
