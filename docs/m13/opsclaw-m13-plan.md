# M13 Plan: Operational Hardening

**Date:** 2026-03-21
**Milestone:** M13 — Operational Hardening
**Status:** PLANNED

---

## 배경

M12 실운영 테스트에서 opsclaw를 실제 시스템에 연결하여 작업을 시도한 결과, 7개의 운영 불가/저하 문제를 발견했다. M13은 이 문제들을 해결하여 opsclaw가 실제 내부망 운영에 사용 가능한 수준으로 만드는 것이 목표다.

---

## 발견된 문제점 요약

| # | 심각도 | 문제 |
|---|--------|------|
| 1 | 🔴 심각 | Playbook 생성 API 없음 (`POST /playbooks` 미구현) |
| 2 | 🔴 심각 | Bootstrap SSH 인증 실패 (sshpass 미동작) |
| 3 | 🔴 심각 | Bootstrap script 표준 없음 (신규 시스템 subagent 설치 방법 미정의) |
| 4 | 🟡 중간 | dispatch가 자연어를 shell로 직접 실행 (LLM 변환 없음) |
| 5 | 🟡 중간 | runtime/invoke 동시 호출 120초 timeout |
| 6 | 🟢 개선 | asset expected_subagent_port 기본값 오류 (8001 → 8002) |
| 7 | 🟢 개선 | pi wake-up 자동화 없음 |
| 8 | 🟢 개선 | asset history 미기록 |
| 9 | 🟢 개선 | master-service 기동 실패 |

---

## 마일스톤 구성

### M13-A: Bootstrap & Deployment (1~3번 문제)

**목표:** 새 시스템에 subagent를 표준화된 방법으로 설치할 수 있어야 한다.

#### WORK-43: Bootstrap script 표준화
- `deploy/bootstrap/install.sh` — 완전한 subagent 설치 스크립트 작성
  - Python 3.11 venv 생성
  - opsclaw 패키지 설치
  - systemd service 파일 생성 및 등록 (포트 8002 고정)
  - 설치 완료 후 health check 자동 수행
- SSH 없이도 수동 실행 가능하도록 독립 실행형으로 작성
- 설치 로그를 `/var/log/opsclaw-bootstrap.log`에 기록

#### WORK-44: Bootstrap API SSH 인증 수정
- `packages/bootstrap_service/__init__.py` 수정
- `sshpass` 의존 제거 → `paramiko` 기반 SSH 클라이언트로 교체
- 패스워드 인증 및 키 인증 모두 지원
- `POST /assets/{id}/bootstrap` body: `ssh_user`, `ssh_pass`, `ssh_key_path`, `ssh_port` 지원
- bootstrap 완료 후 asset `subagent_status` 자동 갱신

#### WORK-45: asset expected_subagent_port 기본값 수정
- asset 생성 시 `expected_subagent_port` 기본값 8001 → 8002 변경
- 기존 asset 마이그레이션 SQL 작성

---

### M13-B: Playbook Operations (1번 문제)

**목표:** Manager가 Playbook 없이도 작업을 거부하지 않도록, 그리고 Playbook을 동적으로 생성/관리할 수 있어야 한다.

#### WORK-46: Playbook 생성/수정/삭제 API 구현
- `POST /playbooks` — playbook 생성
- `PUT /playbooks/{id}` — playbook 수정
- `DELETE /playbooks/{id}` — playbook 삭제
- `POST /playbooks/{id}/steps` — step 추가
- `registry_service`에 `create_playbook`, `update_playbook`, `delete_playbook` 함수 추가

#### WORK-47: ad-hoc 작업 모드 지원
- Manager system prompt 수정: Playbook 없을 때 ad-hoc 모드로 전환 허용
- `POST /projects/{id}/dispatch` 에 `mode: "adhoc"` 파라미터 추가 시 LLM이 스크립트 생성 후 실행
- 기존 Playbook 우선 모드는 유지 (기본값)

---

### M13-C: Execution Reliability (4~5번 문제)

**목표:** dispatch가 자연어를 올바르게 처리하고, 병렬 작업 시 timeout이 발생하지 않아야 한다.

#### WORK-48: dispatch LLM 변환 파이프라인 구현
- `POST /projects/{id}/dispatch` 수정
- `command` 필드 수신 시 LLM으로 shell script 변환 후 실행
- 변환 실패 시 에러 반환 (shell 직접 실행 방지)
- 변환된 스크립트는 evidence에 저장

#### WORK-49: runtime/invoke timeout 및 병렬 처리 개선
- pi 호출 timeout 기본값 120초 → 300초로 증가
- 동시 요청 큐잉 메커니즘 추가 (단일 GPU 서버 한계 고려)
- timeout 발생 시 자동 재시도 1회 (pi wake-up 대응 포함)

---

### M13-D: Observability & Stability (7~9번 문제)

**목표:** opsclaw의 운영 가시성과 안정성을 높인다.

#### WORK-50: pi wake-up 자동화
- `pi_adapter` 에 wake-up 감지 로직 추가
- LLM 응답이 30초 이상 없을 경우 "wake up!" 메시지 자동 전송
- 최대 3회 재시도 후 timeout 처리

#### WORK-51: asset history 자동 기록
- `a2a_protocol` A2AClient 수정: run_script 성공/실패 시 `history_service.ingest_event()` 자동 호출
- `POST /a2a/run_script` subagent 응답 후 manager가 history 기록
- `GET /assets/{id}/history` 에서 실제 이력 조회 가능

#### WORK-52: master-service 기동 문제 해결
- master-service (:8001) 기동 실패 원인 분석 및 수정
- `dev.sh master` 정상 기동 확인

---

## 우선순위 실행 순서

```
M13-A (Bootstrap) → M13-B (Playbook) → M13-C (Execution) → M13-D (Observability)
```

A가 완료되어야 새 시스템에 subagent 설치가 가능하고,
B가 완료되어야 Manager가 실제 작업을 수행할 수 있으며,
C, D는 안정성 개선이므로 순서 유연하게 조정 가능.

---

## 완료 기준

- [ ] 새 Ubuntu 시스템에 `install.sh` 한 번 실행으로 subagent 설치 완료
- [ ] `POST /assets/{id}/bootstrap` 으로 원격 subagent 설치 성공
- [ ] `POST /playbooks` 로 새 playbook 등록 후 Manager가 실행
- [ ] 한국어 자연어 dispatch 명령이 LLM 변환을 거쳐 정상 실행
- [ ] 2개 시스템 동시 작업 시 timeout 없이 완료
- [ ] pi 멈춤 시 자동 wake-up 후 작업 재개
- [ ] subagent 작업 이력이 `GET /assets/{id}/history`에 기록
