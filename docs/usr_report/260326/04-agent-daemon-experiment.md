# Agent Daemon 자율 보안 관제 실험 보고서

**날짜:** 2026-03-26
**프로젝트:** prj_a2b0007fc03f (daemon-stimulus-test)
**Daemon 모델:** gemma3:12b
**서버:** siem (10.20.30.100), web (10.20.30.80)

## 실행 요약

| 단계 | 결과 |
|------|------|
| SIEM Explore | ✅ 5개 감시 대상 자동 결정, baseline 설정 |
| Web Explore | ✅ 7개 감시 대상, 7개 보안 위험 식별 |
| SIEM Daemon (v1) | ✅ 4 사이클, 20 이벤트 |
| SIEM Daemon (v2) | ✅ 4 사이클, 20 이벤트 |
| 자극 발생 | 5라운드, 22건 (SQLi, XSS, SSH 브루트, sudo, nmap 등) |
| 총 탐지 | **40건** (warning 25, normal 13, unknown 2) |
| TTD | < 30초 |

## Evidence (OpsClaw 경유)
- Evidence: 22건 (success 19, fail 3)
- Completion Report: 자동 생성

## 탐지 이벤트 상세

### 탐지 분포
- sshd 브루트포스 징후: 8건 (warning)
- sudo 남용: 8건 (warning)
- 의심 포트 8002: 8건 (warning)
- wazuh-indexer 보안: 2건 (warning)
- auditd 정상: 8건 (normal)
- 기타: 6건 (normal/unknown)

### Daemon 자율 분석 예시
- "같은 IP(192.168.0.107)에서 반복 패스워드 SSH 로그인 — 브루트포스 공격 징후"
- "siem 사용자가 /tmp 스크립트를 root로 반복 실행 — 보안 위험"
- "Java security manager disabled — 보안 제한 해제됨"

## 구현 완료 항목
- SubAgent `/a2a/explore` — 자율 서버 환경 파악
- SubAgent `/a2a/daemon` — 상시 자율 감시 루프
- SubAgent `/a2a/daemon/stop` — Daemon 중지
- SubAgent `/a2a/daemon/status` — 상태 조회
- Manager `/projects/{id}/stimulate` — 자극 생성기
- 로컬 지식 자동 저장 (daemon_events)
