# OpsClaw 실전 운영 가이드

## 1. 개요

이 문서는 OpsClaw를 실제 IT 운영 업무에 활용하는 방법을 다룬다.
6가지 실전 시나리오를 통해 프로젝트 생성부터 완료보고까지의 전체 흐름을 보여준다.

**공통 사전 설정:**

```bash
export OPSCLAW_API_KEY=opsclaw-api-key-2026
export MANAGER=http://localhost:8000
alias oc='curl -s -H "X-API-Key: $OPSCLAW_API_KEY" -H "Content-Type: application/json"'
```

---

## 2. 예시 1: 다중 서버 보안 감사

v-secu, v-web, v-siem 3대 서버를 동시에 점검한다.

### 2.1 프로젝트 생성

```bash
oc -X POST $MANAGER/projects \
  -d '{
    "name": "security-audit-2026Q1",
    "request_text": "1분기 보안 감사: 방화벽, 웹서버, SIEM 전체 점검",
    "master_mode": "external"
  }'
# → project_id 확인
PID="<응답에서 project.id 복사>"
```

### 2.2 Stage 전환

```bash
oc -X POST $MANAGER/projects/$PID/plan
oc -X POST $MANAGER/projects/$PID/execute
```

### 2.3 병렬 execute-plan (3대 서버 동시 점검)

```bash
oc -X POST $MANAGER/projects/$PID/execute-plan \
  -d '{
    "parallel": true,
    "tasks": [
      {
        "order": 1,
        "title": "v-secu 방화벽 규칙 감사",
        "instruction_prompt": "nft list ruleset && ss -tlnp && cat /etc/nftables.conf",
        "risk_level": "low",
        "subagent_url": "http://192.168.0.108:8002"
      },
      {
        "order": 2,
        "title": "v-web Apache 설정 감사",
        "instruction_prompt": "apache2ctl -S && apache2ctl configtest && ls -la /etc/apache2/sites-enabled/",
        "risk_level": "low",
        "subagent_url": "http://192.168.0.110:8002"
      },
      {
        "order": 3,
        "title": "v-siem Wazuh 상태 점검",
        "instruction_prompt": "systemctl status wazuh-manager && /var/ossec/bin/agent_control -l",
        "risk_level": "low",
        "subagent_url": "http://192.168.0.109:8002"
      }
    ]
  }'
```

### 2.4 결과 확인 및 추가 점검

```bash
# Evidence 요약
oc $MANAGER/projects/$PID/evidence/summary

# 상세 Evidence 조회
oc $MANAGER/projects/$PID/evidence

# 추가 점검 (취약점 발견 시)
oc -X POST $MANAGER/projects/$PID/dispatch \
  -d '{
    "command": "grep -r PermitRootLogin /etc/ssh/sshd_config",
    "subagent_url": "http://192.168.0.108:8002"
  }'
```

### 2.5 완료보고서 생성

```bash
oc -X POST $MANAGER/projects/$PID/completion-report \
  -d '{
    "summary": "1분기 보안 감사 완료. 3대 서버 정상, 미흡사항 2건 발견.",
    "outcome": "success",
    "work_details": [
      "v-secu: nftables 규칙 정상, SSH 포트 제한 확인",
      "v-web: Apache 설정 정상, TLS 인증서 갱신 필요",
      "v-siem: Wazuh 에이전트 3대 연결 정상"
    ],
    "issues": [
      "v-web TLS 인증서 만료 예정 (2026-04-15)",
      "v-secu SSH PermitRootLogin=yes 발견"
    ],
    "next_steps": [
      "TLS 인증서 갱신 작업 스케줄 등록",
      "SSH root 로그인 비활성화"
    ]
  }'
```

### 2.6 PoW 블록 확인

```bash
# 프로젝트 PoW 블록
oc $MANAGER/projects/$PID/pow

# 체인 무결성 검증
oc "$MANAGER/pow/verify?agent_id=http://192.168.0.108:8002"
```

---

## 3. 예시 2: 인시던트 대응 워크플로

SSH 브루트포스 공격을 감지하고 대응하는 전체 과정이다.

### 3.1 NIST IR 6단계

```
1. 준비(Preparation) → 사전 모니터링 설정
2. 탐지(Detection) → Wazuh 알림 확인
3. 분석(Analysis) → 공격 IP/패턴 분석
4. 격리(Containment) → nftables 차단
5. 제거(Eradication) → 침입 흔적 제거
6. 복구(Recovery) → 서비스 정상화 확인
```

### 3.2 실행

```bash
# 프로젝트 생성
oc -X POST $MANAGER/projects \
  -d '{
    "name": "ir-ssh-bruteforce-20260330",
    "request_text": "SSH 브루트포스 공격 대응",
    "master_mode": "external"
  }'
PID="<project_id>"
oc -X POST $MANAGER/projects/$PID/plan
oc -X POST $MANAGER/projects/$PID/execute

# 1단계: 탐지 — Wazuh 알림 확인
oc -X POST $MANAGER/projects/$PID/execute-plan \
  -d '{
    "tasks": [
      {
        "order": 1,
        "title": "Wazuh SSH 브루트포스 알림 확인",
        "instruction_prompt": "grep -i \"sshd\" /var/ossec/logs/alerts/alerts.json | tail -50 | python3 -c \"import json,sys; [print(json.dumps(json.loads(l), indent=2)) for l in sys.stdin if json.loads(l).get(\\\"rule\\\",{}).get(\\\"level\\\",0)>=10]\"",
        "risk_level": "low",
        "subagent_url": "http://192.168.0.109:8002"
      }
    ]
  }'

# 2단계: 분석 — 공격 IP 추출
oc -X POST $MANAGER/projects/$PID/dispatch \
  -d '{
    "command": "journalctl -u ssh --since \"1 hour ago\" | grep \"Failed password\" | awk \"{print \\$11}\" | sort | uniq -c | sort -rn | head -10",
    "subagent_url": "http://192.168.0.108:8002"
  }'

# 3단계: 격리 — nftables로 공격 IP 차단
oc -X POST $MANAGER/projects/$PID/execute-plan \
  -d '{
    "tasks": [
      {
        "order": 3,
        "title": "공격 IP nftables 차단",
        "instruction_prompt": "nft add rule inet filter input ip saddr 203.0.113.50 drop && nft list ruleset | grep 203.0.113.50",
        "risk_level": "high",
        "subagent_url": "http://192.168.0.108:8002"
      }
    ],
    "confirmed": true
  }'

# 4단계: 제거 — 침입 흔적 확인
oc -X POST $MANAGER/projects/$PID/dispatch \
  -d '{
    "command": "last -i | head -20 && cat /var/log/auth.log | grep 203.0.113.50 | tail -20",
    "subagent_url": "http://192.168.0.108:8002"
  }'

# 5단계: 복구 — SSH 서비스 정상 확인
oc -X POST $MANAGER/projects/$PID/dispatch \
  -d '{
    "command": "systemctl status sshd && ss -tlnp | grep 22",
    "subagent_url": "http://192.168.0.108:8002"
  }'

# 완료보고
oc -X POST $MANAGER/projects/$PID/completion-report \
  -d '{
    "summary": "SSH 브루트포스 대응 완료. 공격 IP 차단, 침입 흔적 없음 확인.",
    "outcome": "success",
    "work_details": [
      "공격 IP: 203.0.113.50, 시도 횟수: 487회",
      "nftables drop 규칙 적용",
      "침입 성공 없음 확인 (last 명령)"
    ]
  }'
```

---

## 4. 예시 3: 정기 유지보수 (Schedule)

백업, 패치, 로그 회전을 스케줄로 등록한다.

### 4.1 백업 스케줄 등록

```bash
# 매일 새벽 2시 백업
oc -X POST $MANAGER/schedules \
  -d '{
    "project_name": "daily-backup",
    "schedule_type": "backup",
    "cron_expr": "0 2 * * *",
    "metadata": {
      "targets": ["v-secu", "v-web", "v-siem"],
      "backup_type": "full"
    }
  }'
```

### 4.2 패치 스케줄

```bash
# 매주 일요일 새벽 3시 패치 확인
oc -X POST $MANAGER/schedules \
  -d '{
    "project_name": "weekly-patch-check",
    "schedule_type": "maintenance",
    "cron_expr": "0 3 * * 0",
    "metadata": {
      "command": "apt list --upgradable 2>/dev/null | grep -i security",
      "targets": ["v-secu", "v-web", "v-siem"]
    }
  }'
```

### 4.3 로그 회전 스케줄

```bash
# 매주 월요일 자정 로그 회전
oc -X POST $MANAGER/schedules \
  -d '{
    "project_name": "weekly-log-rotation",
    "schedule_type": "log_rotation",
    "cron_expr": "0 0 * * 1",
    "metadata": {
      "command": "logrotate -f /etc/logrotate.conf && du -sh /var/log/"
    }
  }'
```

### 4.4 스케줄 관리

```bash
# 전체 스케줄 목록
oc $MANAGER/schedules

# 특정 스케줄 비활성화
oc -X PATCH $MANAGER/schedules/<schedule_id> \
  -d '{"enabled": false}'

# 즉시 실행 (테스트용)
oc -X POST $MANAGER/schedules/<schedule_id>/run
```

---

## 5. 예시 4: Watcher 기반 모니터링

### 5.1 디스크 사용량 감시

```bash
# 디스크 사용량 Watcher 등록
oc -X POST $MANAGER/watchers \
  -d '{
    "project_name": "disk-monitor-vsecu",
    "watch_type": "disk_usage",
    "metadata": {
      "target": "http://192.168.0.108:8002",
      "threshold_percent": 80,
      "check_interval_s": 300,
      "command": "df -h / | awk \"NR==2{print \\$5}\" | tr -d \"%\""
    }
  }'
```

### 5.2 서비스 상태 감시

```bash
# Apache 서비스 Watcher
oc -X POST $MANAGER/watchers \
  -d '{
    "project_name": "apache-monitor",
    "watch_type": "service_status",
    "metadata": {
      "target": "http://192.168.0.110:8002",
      "service": "apache2",
      "command": "systemctl is-active apache2"
    }
  }'

# Wazuh 서비스 Watcher
oc -X POST $MANAGER/watchers \
  -d '{
    "project_name": "wazuh-monitor",
    "watch_type": "service_status",
    "metadata": {
      "target": "http://192.168.0.109:8002",
      "service": "wazuh-manager",
      "command": "systemctl is-active wazuh-manager"
    }
  }'
```

### 5.3 인증서 만료 감시

```bash
# TLS 인증서 만료 Watcher
oc -X POST $MANAGER/watchers \
  -d '{
    "project_name": "cert-expiry-monitor",
    "watch_type": "cert_expiry",
    "metadata": {
      "target": "http://192.168.0.110:8002",
      "command": "openssl x509 -in /etc/ssl/certs/server.pem -noout -enddate 2>/dev/null || echo notAfter=unknown",
      "warn_days_before": 30
    }
  }'
```

### 5.4 Watcher 관리

```bash
# Watcher 목록
oc $MANAGER/watchers

# 수동 체크 실행
oc -X POST $MANAGER/watchers/<watch_job_id>/check

# Watcher 이벤트 이력
oc $MANAGER/watchers/<watch_job_id>/events

# Watcher 중지
oc -X PATCH $MANAGER/watchers/<watch_job_id>/status \
  -d '{"status": "stopped"}'
```

### 5.5 인시던트 관리

Watcher가 이상을 감지하면 자동으로 Incident가 생성된다.

```bash
# 열린 인시던트 목록
oc "$MANAGER/incidents?status=open"

# 인시던트 해결 처리
oc -X POST $MANAGER/incidents/<incident_id>/resolve
```

---

## 6. 예시 5: Red/Blue Team 연습

OpsClaw의 자율 미션 기능으로 Red/Blue Team 연습을 수행한다.

### 6.1 프로젝트 생성

```bash
oc -X POST $MANAGER/projects \
  -d '{
    "name": "purple-team-exercise-Q1",
    "request_text": "Red/Blue Team 합동 훈련",
    "master_mode": "external"
  }'
PID="<project_id>"
oc -X POST $MANAGER/projects/$PID/plan
oc -X POST $MANAGER/projects/$PID/execute
```

### 6.2 Red Team (공격) 실행

```bash
# Red Team: 정보 수집
oc -X POST $MANAGER/projects/$PID/execute-plan \
  -d '{
    "tasks": [
      {
        "order": 1,
        "title": "Red: 대상 서버 포트 스캔",
        "instruction_prompt": "ss -tlnp | grep LISTEN",
        "risk_level": "low",
        "subagent_url": "http://192.168.0.110:8002"
      },
      {
        "order": 2,
        "title": "Red: 웹 취약점 확인",
        "instruction_prompt": "curl -s -o /dev/null -w \"%{http_code}\" http://localhost:3000/rest/admin/application-configuration",
        "risk_level": "medium",
        "subagent_url": "http://192.168.0.110:8002"
      },
      {
        "order": 3,
        "title": "Red: SSH 설정 취약점 확인",
        "instruction_prompt": "cat /etc/ssh/sshd_config | grep -E \"(PermitRootLogin|PasswordAuthentication|MaxAuthTries)\"",
        "risk_level": "low",
        "subagent_url": "http://192.168.0.108:8002"
      }
    ]
  }'
```

### 6.3 Blue Team (방어) 실행

```bash
# Blue Team: 방어 현황 확인 및 강화
oc -X POST $MANAGER/projects/$PID/execute-plan \
  -d '{
    "tasks": [
      {
        "order": 4,
        "title": "Blue: 방화벽 현황 확인",
        "instruction_prompt": "nft list ruleset | head -50",
        "risk_level": "low",
        "subagent_url": "http://192.168.0.108:8002"
      },
      {
        "order": 5,
        "title": "Blue: Suricata 규칙 확인",
        "instruction_prompt": "cat /etc/suricata/rules/local.rules | head -30",
        "risk_level": "low",
        "subagent_url": "http://192.168.0.108:8002"
      },
      {
        "order": 6,
        "title": "Blue: Wazuh 최근 고위험 알림",
        "instruction_prompt": "tail -100 /var/ossec/logs/alerts/alerts.json | python3 -c \"import json,sys; alerts=[json.loads(l) for l in sys.stdin]; high=[a for a in alerts if a.get(\\\"rule\\\",{}).get(\\\"level\\\",0)>=10]; print(f\\\"High alerts: {len(high)}\\\"); [print(f\\\"  [{a[\\\"rule\\\"][\\\"level\\\"]}] {a[\\\"rule\\\"].get(\\\"description\\\",\\\"\\\")}  src={a.get(\\\"srcip\\\",\\\"-\\\")}\\\") for a in high[:10]]\"",
        "risk_level": "low",
        "subagent_url": "http://192.168.0.109:8002"
      }
    ]
  }'
```

### 6.4 결과 분석 및 보고

```bash
# Evidence 기반 작업 타임라인
oc $MANAGER/projects/$PID/replay

# 보상 비교 (Red vs Blue 성과)
oc $MANAGER/pow/leaderboard

# 완료보고서
oc -X POST $MANAGER/projects/$PID/completion-report \
  -d '{
    "summary": "Purple Team 훈련 완료. Red 3건 시도, Blue 방어 확인.",
    "outcome": "success",
    "work_details": [
      "Red: 포트 스캔 완료, JuiceShop admin API 노출 확인, SSH root 허용 발견",
      "Blue: 방화벽 규칙 정상, Suricata 규칙 업데이트 필요, Wazuh 고위험 0건"
    ],
    "issues": ["JuiceShop admin API 접근 제한 필요", "SSH PermitRootLogin 비활성화 필요"],
    "next_steps": ["Apache reverse proxy에 admin API 차단 규칙 추가", "sshd_config 수정"]
  }'
```

---

## 7. 예시 6: 컴플라이언스 감사

ISO 27001 / SOC 2 요구사항에 대한 자동 Evidence 수집이다.

### 7.1 감사 프로젝트 생성

```bash
oc -X POST $MANAGER/projects \
  -d '{
    "name": "iso27001-audit-2026Q1",
    "request_text": "ISO 27001 A.12 운영 보안 통제항목 감사",
    "master_mode": "external"
  }'
PID="<project_id>"
oc -X POST $MANAGER/projects/$PID/plan
oc -X POST $MANAGER/projects/$PID/execute
```

### 7.2 통제항목별 Evidence 수집

```bash
oc -X POST $MANAGER/projects/$PID/execute-plan \
  -d '{
    "tasks": [
      {
        "order": 1,
        "title": "A.12.1.1 운영 절차 문서화",
        "instruction_prompt": "ls -la /etc/opsclaw/playbooks/ && cat /etc/opsclaw/playbooks/README.md 2>/dev/null || echo \"Playbook directory check\"",
        "risk_level": "low",
        "subagent_url": "http://192.168.0.108:8002"
      },
      {
        "order": 2,
        "title": "A.12.2.1 악성코드 통제",
        "instruction_prompt": "dpkg -l | grep -E \"(clamav|rkhunter|chkrootkit)\" && systemctl is-active clamav-freshclam 2>/dev/null || echo \"No AV found\"",
        "risk_level": "low",
        "subagent_url": "http://192.168.0.108:8002"
      },
      {
        "order": 3,
        "title": "A.12.3.1 백업 검증",
        "instruction_prompt": "ls -la /backup/ 2>/dev/null && find /backup/ -name \"*.gz\" -mtime -7 | head -5 || echo \"No recent backups\"",
        "risk_level": "low",
        "subagent_url": "http://192.168.0.108:8002"
      },
      {
        "order": 4,
        "title": "A.12.4.1 이벤트 로깅",
        "instruction_prompt": "systemctl is-active rsyslog && ls -la /var/log/syslog /var/log/auth.log && wc -l /var/log/auth.log",
        "risk_level": "low",
        "subagent_url": "http://192.168.0.108:8002"
      },
      {
        "order": 5,
        "title": "A.12.6.1 기술 취약성 관리",
        "instruction_prompt": "apt list --upgradable 2>/dev/null | grep -i security | wc -l && echo \"security patches pending\"",
        "risk_level": "low",
        "subagent_url": "http://192.168.0.108:8002"
      }
    ]
  }'
```

### 7.3 Evidence Pack 내보내기

```bash
# 전체 Evidence 보고서 생성
oc $MANAGER/reports/project/$PID

# Evidence Pack JSON 내보내기 (감사 제출용)
oc $MANAGER/reports/project/$PID/evidence-pack/json

# 감사 로그 CSV 내보내기
oc -X POST $MANAGER/admin/audit/export \
  -d '{
    "format": "csv",
    "project_id": "'$PID'",
    "limit": 1000
  }'
```

### 7.4 PoW 기반 감사 증적

```bash
# 감사 대상 프로젝트의 PoW 블록 (변조 불가능한 실행 증적)
oc $MANAGER/projects/$PID/pow

# 체인 무결성 검증 (감사관에게 제공)
oc "$MANAGER/pow/verify?agent_id=http://192.168.0.108:8002"
```

---

## 8. CLI 사용법 정리

OpsClaw CLI(`opsclaw`)로 위의 모든 작업을 간편하게 수행할 수 있다.

```bash
# 자연어 작업 지시 (native 모드)
opsclaw run "v-secu 방화벽 점검" --target v-secu

# 직접 명령 실행 (external 모드)
opsclaw run "nft list ruleset" --target v-secu --manual

# 대상 서버 지정 (별명 사용)
opsclaw run "Apache 상태 확인" --target v-web

# 프로젝트 목록
opsclaw list

# 프로젝트 상태
opsclaw status <project_id>

# 작업 Replay
opsclaw replay <project_id>

# 서버 별명 목록
opsclaw servers
```

**서버 별명 매핑:**

| 별명 | SubAgent URL |
|------|-------------|
| v-secu | http://192.168.0.108:8002 |
| v-web | http://192.168.0.110:8002 |
| v-siem | http://192.168.0.109:8002 |
| secu | http://192.168.208.150:8002 |
| web | http://192.168.208.151:8002 |
| siem | http://192.168.208.152:8002 |
| local | http://localhost:8002 |

---

## 9. 운영 팁

### 9.1 dry_run 우선 사용

변경 작업은 항상 dry_run으로 먼저 확인한다.

```bash
oc -X POST $MANAGER/projects/$PID/execute-plan \
  -d '{"tasks": [...], "dry_run": true}'
```

### 9.2 risk_level=critical 처리

critical 작업은 반드시 `confirmed: true`를 명시해야 실행된다.

```bash
oc -X POST $MANAGER/projects/$PID/execute-plan \
  -d '{
    "tasks": [{"order": 1, "instruction_prompt": "iptables -F", "risk_level": "critical"}],
    "confirmed": true,
    "subagent_url": "http://192.168.0.108:8002"
  }'
```

### 9.3 Experience 축적

작업 완료 후 항상 Task Memory를 생성하여 경험을 축적한다.

```bash
# Task Memory 생성 + Experience 자동 승격
oc -X POST "$MANAGER/projects/$PID/memory/build?promote=true"
```

### 9.4 Notification 활용

중요 이벤트에 Slack/Email 알림을 설정한다.

```bash
# Slack 채널
oc -X POST $MANAGER/notifications/channels \
  -d '{"name": "ops-slack", "channel_type": "slack", "config": {"channel": "#ops-alerts"}}'

# 인시던트 → Slack 규칙
oc -X POST $MANAGER/notifications/rules \
  -d '{"name": "incident-slack", "event_type": "incident.created", "channel_id": "<ch_id>"}'
```
