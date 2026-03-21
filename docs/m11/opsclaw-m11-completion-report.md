# M11 Completion Report: Integration Fixes & Real-System Deployment Prep

**Date:** 2026-03-20
**Milestone:** M11 — Integration Fixes & Real-System Deployment Prep
**Status:** COMPLETE ✓

---

## Summary

M11은 M10까지 구현된 기능들의 실제 실행 경로 버그를 수정하고, 실 시스템(secu/web/siem)에 subagent를 배포하기 위한 기반을 마련했다. 주요 수정 내용은 pi CLI 경로 문제, ToolBridge subprocess 실행, subagent A2A LLM 호출 오류, 민감정보 제거다.

---

## Work Items Completed

### WORK-37: subagent A2A LLM 호출 수정
- `/a2a/invoke_llm`, `/a2a/analyze` → 500 에러 수정
- 원인: pi CLI가 ollama provider 미지원
- 해결: `packages/pi_adapter/runtime/client.py` → subprocess 제거, httpx로 Ollama 직접 호출
- Ollama endpoint: `http://192.168.0.105:11434/v1`

### WORK-38: ToolBridge.run_tool subprocess 구현
- 기존 stub → 실제 subprocess 실행으로 구현
- exit_code 127 (command not found), 124 (timeout) 처리 추가

### WORK-39: ops 스크립트 pi 탐색 경로 수정
- pi CLI 바이너리 탐색 경로 수정으로 실행 환경 정상화

### WORK-40: 민감정보 제거
- API 키, 토큰 등 민감정보 코드에서 제거
- .env.example 기반 환경변수 관리로 전환

### WORK-41: 실 시스템 subagent 배포 (수동)
- secu (192.168.0.113), web (192.168.0.108), siem (192.168.0.109)에 subagent-runtime 배포
- `/opt/opsclaw/` 에 설치, systemd service 등록 및 자동 기동 설정
- 각 시스템 port 8002로 기동 확인

### WORK-42: Email/Slack 알림 채널 구현
- Email: smtplib STARTTLS/SSL 구현
- Slack: Bot Token + `chat.postMessage`, `#bot-cc` 채널 연동
- Bot name: OldClaw

---

## 통합 테스트 결과

- manager-api (:8000), master-service (:8001), subagent-runtime (:8002) 정상 기동 확인
- Project / Asset / Notification / Schedule / Watcher / MasterReview CRUD 전체 정상
- subagent A2A (invoke_llm / analyze) 정상 동작 확인

---

## 이슈

없음 (모든 항목 완료)
