# OpsClaw M20 완료보고서: User & Agent Manual

**날짜:** 2026-03-22
**마일스톤:** M20 — User & Agent Manual
**상태:** ✅ 완료

---

## 개요

OpsClaw를 처음 접하는 운영자와 AI 에이전트 개발자가 매뉴얼만으로 설치, 작업 실행, 에이전트 연동을 완료할 수 있도록 전체 문서 체계를 완성했다.

특히 AI 에이전트가 OpsClaw를 제어할 때 역할 분담을 정확히 인지하고 올바르게 동작할 수 있도록 시스템 프롬프트 문서를 핵심으로 설계했다.

---

## 완료 항목

### WORK-85: 사용자 매뉴얼 (`docs/manual/user/`)

| 파일 | 내용 |
|------|------|
| `01-installation.md` | 설치 요구사항, Python venv, PostgreSQL, 마이그레이션, Seed 로드, 서비스 기동 |
| `02-quickstart.md` | Claude Code / curl 두 가지 방법으로 첫 작업 실행 |
| `03-project-management.md` | 프로젝트 상태 전이, Evidence, execute-plan/dispatch, Approval Gate, replan |
| `04-playbook-guide.md` | Playbook/Step 생성, Tool/Skill 목록, 커스텀 Playbook 예시 |
| `05-notification-setup.md` | Slack/Email/Webhook 채널 등록, 알림 규칙, Schedule/Watch 설정 |
| `06-web-ui-guide.md` | 현재 API 전용 (Swagger UI 안내), M16 예정 기능 목록 |
| `07-troubleshooting.md` | 서비스 기동, DB 연결, stage 전환, SubAgent, Ollama, 로그 확인 FAQ |

### WORK-86: 에이전트 매뉴얼 (`docs/manual/agent/`)

| 파일 | 내용 |
|------|------|
| `01-subagent-install.md` | Bootstrap API / 수동 설치 / install.sh 3가지 방법, systemd 등록, 다중 SubAgent |
| `02-agent-prompts.md` | External Master 프롬프트 원칙, instruction_prompt 작성 요령, risk_level 기준, 응답 해석 |
| `03-custom-skill-tool.md` | Tool/Skill API 등록, Seed YAML, Playbook 단계별 등록, Experience 활용 |
| `04-a2a-protocol.md` | A2A 엔드포인트 명세, 커스텀 SubAgent 개발 최소 구현, 보안 고려사항 |
| `05-ai-driven-mode.md` | *(이전 세션에서 완료)* AI 에이전트 연동 방법 상세, 에이전트 루프 의사코드 |

### WORK-87: README.md 최종 정리

- 마일스톤 테이블: M14/M15/M17/M19/M20 ✅ 완료로 업데이트
- 현재 구현 상태 섹션: M14~M20 완료 내용 반영
- 저장소 구조: 신규 디렉토리(`docs/manual/`, `scripts/`, `CLAUDE.md`) 추가

### 핵심 문서: `docs/agent-system-prompt.md`

어떤 AI 에이전트든 system prompt에 주입하면 OpsClaw와 올바르게 연동되는 자기완결형 가이드:
- 역할 분담 테이블 (External Master / Manager API / SubAgent 각각 할 것 / 하면 안 되는 것)
- 필수 작업 순서 (stage 전환 포함)
- 실행 방법 3가지 선택 기준 (execute-plan / dispatch / playbook/run)
- 안전 규칙 5개, 에러 처리 패턴, 완료보고서 필수 필드
- 시나리오별 빠른 참조 (서버 현황 수집 / 패키지 설치 / 보안 점검)

---

## 문서 접근 방법

```
# Claude Code (자동 로드)
CLAUDE.md → docs/agent-system-prompt.md 참조

# 다른 AI 에이전트
cat docs/agent-system-prompt.md | system_prompt에 삽입

# 운영자
docs/manual/user/01-installation.md 부터 순서대로
```
