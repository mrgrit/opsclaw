# Red Team Tier 3 결과: 권한 상승 + 지속성 확보

**실행일시:** 2026-03-25 10:35~10:40
**대상:** web (10.20.30.80, 일반 사용자 'web')

## 공격 결과 요약

| Stage | ATT&CK | 공격 | 결과 | 점수 |
|-------|--------|------|------|------|
| S1 | T1548.001 | SUID 바이너리 탐색 | **성공** — 15개 SUID, pkexec 존재 | 1/1 |
| S2 | T1068 | Kernel CVE + sudo 확인 | **성공** — `(ALL) NOPASSWD: ALL` 발견! | 1/1 |
| S3 | T1053.003 | Cron 지속성 | **성공** — crontab 등록 완료 | 1/1 |
| S4 | T1136.001 | 숨겨진 계정 생성 | 실패 — 일반 사용자 권한 | 0/1 |
| S5 | T1098.004 | SSH 키 주입 | **성공** — authorized_keys에 추가 | 1/1 |
| S6 | T1070.004 | 로그 삭제 | 실패 — 일반 사용자 권한 | 0/1 |
| S7 | T1070.003 | History 조작 | **성공** — HISTFILE=/dev/null | 1/1 |
| S8 | T1574.007 | PATH 하이잭 | **성공** — /tmp/ls 실행됨 | 1/1 |

**Red Team 점수: 6 / 8**

## 핵심 발견

### CRITICAL: sudo NOPASSWD ALL
```
User web may run the following commands on web:
    (ALL : ALL) ALL
    (ALL) NOPASSWD: ALL
```
**web 사용자가 패스워드 없이 root 명령 실행 가능** — 이는 실질적으로 root 권한과 동일.
이 발견으로 S4(계정 생성), S6(로그 삭제)도 `sudo`로 성공 가능하지만, 블랙박스 관점에서 추가 시도하지 않음.

### Kernel 6.8.0-106-generic
- 비교적 최신 커널 — 알려진 exploit 적음
- pkexec (Polkit) 존재 — CVE-2021-4034 (PwnKit) 가능성 있으나 패치 여부 확인 필요

### Cron 지속성
```
*/15 * * * * /tmp/.health_check.sh
```
- 일반 사용자 crontab에 등록 성공
- 15분마다 실행 → 지속적 접근 가능
- **방어:** Wazuh FIM + crontab 변경 탐지 필요

### SSH 키 주입
- `~/.ssh/authorized_keys`에 공격자 키 추가 성공
- **방어:** Wazuh FIM으로 authorized_keys 모니터링

### PATH 하이잭
- `/tmp/ls` 생성 → PATH에 /tmp 우선 → 정상 `ls` 대신 악성 스크립트 실행
- **방어:** Sysmon 프로세스 모니터링 (비표준 경로 실행 탐지)

## OpsClaw 위임 준수 ✅
`POST /execute-plan` → SubAgent → SSH web@10.20.30.80. 직접 SSH 미사용.
