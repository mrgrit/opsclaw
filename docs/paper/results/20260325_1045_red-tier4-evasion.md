# Red Team Tier 4 결과: SIEM 탐지 우회 공격

**실행일시:** 2026-03-25 10:40~10:45
**대상:** web (10.20.30.80)

## 공격 결과 요약

| Stage | ATT&CK | 공격 | 결과 | 점수 |
|-------|--------|------|------|------|
| S1 | T1562.001 | Wazuh Agent 정지 | **성공** (sudo NOPASSWD) | 1/1 |
| S2a | T1027 | Base64 난독화 실행 | **성공** — `id` 출력 (uid=1000) | 1/1 |
| S2b | T1027 | XOR 난독화 (python) | 실패 — sh 옵션 오류 | 0/1 |
| S2c | T1027 | 환경변수 기반 실행 | **성공** — `whoami` = web | 1/1 |
| S2d | T1027.011 | /dev/shm 메모리 실행 | **성공** — 디스크 흔적 없음 | 1/1 |
| S3 | T1562.006 | Syslog/Wazuh 통신 차단 | **성공** (iptables DROP) | 1/1 |
| S4 | T1036.005 | 프로세스 위장 [kworker] | 실패 — bash 복사 오류 | 0/1 |

**Red Team 점수: 5 / 7**

## 핵심 발견

### Agent 무력화 성공 (CRITICAL)
- `sudo systemctl stop wazuh-agent` → agent 즉시 정지
- **결과:** SIEM 모니터링 완전 중단
- **원인:** web 사용자의 `NOPASSWD: ALL` sudo 권한
- **방어:** Wazuh Manager에서 agent heartbeat loss 경보 설정 필요

### Syslog 통신 차단 성공
- `iptables -A OUTPUT -p udp --dport 514 -j DROP` → syslog 전송 중단
- `iptables -A OUTPUT -p tcp --dport 1514 -j DROP` → wazuh agent 통신 차단
- **결과:** 호스트의 모든 보안 로그가 SIEM에 전달되지 않음

### /dev/shm 메모리 실행 성공
- 스크립트를 /dev/shm에 작성 → 실행 → 삭제
- 디스크에 흔적 없음 (tmpfs)
- **방어:** AuditD execve 감사 + /dev/shm 실행 탐지 룰

### 복원
- 실험 후 agent 재시작 + iptables 규칙 삭제 완료
- 인프라 정상 상태 복원됨

## OpsClaw 위임 준수 ✅
모든 공격 OpsClaw execute-plan → SubAgent → SSH 경유.
