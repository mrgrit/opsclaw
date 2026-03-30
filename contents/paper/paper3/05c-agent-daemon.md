# 5C. Agent Daemon: 자율 보안 관제 (Autonomous Security Monitoring)

## 5C.1 동기: 반응형에서 능동형으로

기존 SubAgent는 Master/Manager가 명령을 내려야만 동작하는 반응형(reactive) 실행기였다. 5B절의 자율 미션도 "미션 시작" 지시가 필요하며, max_steps 도달 시 종료된다. 그러나 실제 보안 관제는 **24/7 상시 감시**를 요구하며, 보안 관리자(human sysadmin)는 능동적으로 이상을 탐지하고 조치한다.

본 절에서는 SubAgent가 스스로 서버 환경을 파악하고, 감시 대상을 결정하며, 이상 감지 시 자율적으로 분석·대응하는 **Agent Daemon**을 구현하고 실증한다.

## 5C.2 아키텍처: OTARI 루프

Agent Daemon은 종료되지 않는 자율 감시 프로세스로, 다음 5단계 루프(OTARI)를 반복한다.

```
┌─ Agent Daemon (상시 실행) ──────────────────────────────┐
│                                                         │
│  Phase 0: EXPLORE (1회, 서버 투입 시)                    │
│    → 서버 환경 파악 → 감시 대상 자동 결정 → baseline 설정 │
│                                                         │
│  while running:                                         │
│    1. OBSERVE — 감시 대상별 상태 수집 (grep, tail, ps)    │
│    2. THINK   — 이상 여부 판단 (패턴 매칭 → LLM 분석)     │
│    3. ACT     — 자율 조치 (warning/critical 시)           │
│    4. REPORT  — Manager 콜백 + local_knowledge 기록       │
│    5. IMPROVE — 감시 기준 업데이트                         │
│                                                         │
│    sleep(adaptive: 정상=30s, warning=15s, critical=5s)   │
│  end                                                    │
└─────────────────────────────────────────────────────────┘
```

핵심 설계 결정:
- **2단계 판단:** 먼저 패턴 매칭(LLM 호출 없이, grep 수준)으로 빠르게 필터링하고, 이상 감지 시에만 LLM을 호출하여 분석. 이를 통해 LLM 호출 비용을 최소화.
- **적응적 주기:** 정상 시 30초, warning 시 15초, critical 시 5초로 감시 주기를 자동 조절.
- **자율 감시 대상 결정:** Explore 단계에서 LLM이 서버의 서비스, 포트, 프로세스를 분석하여 감시 대상을 스스로 결정.

## 5C.3 Explore: 자율 서버 파악

### 방법
SubAgent에 `/a2a/explore` 엔드포인트를 추가하였다. Explore는 10개의 시스템 탐색 명령(hostname, uptime, os, disk, memory, services, ports, processes, crontab, security_logs)을 실행한 후, 결과를 로컬 LLM(gemma3:12b)에 전달하여 감시 대상(watch_targets), 정상 기준(baseline), 보안 위험(security_risks)을 자동 결정한다.

### 결과: SIEM 서버 Explore

LLM이 자율적으로 결정한 감시 대상:

**표 8. SIEM 서버 자율 감시 대상 (LLM 결정)**

| # | 감시 대상 | 감시 명령 | 주기 | 경보 패턴 |
|---|---------|---------|------|---------|
| 1 | SSH 로그인 | `grep 'Accepted password' /var/log/auth.log` | 60s | Accepted password |
| 2 | sudo 사용 | `grep 'sudo:' /var/log/auth.log` | 60s | sudo: |
| 3 | 감사 로그 | `tail -f /var/log/audit/audit.log` | 60s | USER.SEC |
| 4 | Wazuh Indexer | `ps aux \| grep wazuh-indexer` | 60s | wazuh-indexer |
| 5 | Port 8002 | `netstat -tulnp \| grep :8002` | 60s | :8002 |

자율 식별된 baseline: 디스크 7%, 메모리 23%, 서비스 10개

자율 식별된 보안 위험 5건:
1. 패스워드 기반 SSH 인증 활성화
2. siem 사용자 sudo 권한 검토 필요
3. Port 8002 미확인 서비스
4. wazuh-indexer 고메모리 사용
5. crontab 항목 부재 (예약 작업 검증 필요)

### 결과: Web 서버 Explore

| # | 감시 대상 | 경보 패턴 |
|---|---------|---------|
| 1 | Apache Access Logs | 401, 403, 500, SQL injection, XSS |
| 2 | Apache Error Logs | PHP Warning, Connection refused |
| 3 | Node.js Application | error, fail, exception |
| 4 | System Auth Logs | Failed password, Invalid user |
| 5 | System Audit Logs | USER_AUTH, LOGIN_FAILURE |
| 6 | Systemd Journal | error, fail, exception |
| 7 | Crontab Health Check | error |

자율 식별된 보안 위험 7건 (미보호 포트, SSH 패스워드, JuiceShop 취약점, 수상한 crontab 스크립트, sudo 권한, MariaDB, Docker)

## 5C.4 실험: 자극 → 자율 탐지

### 실험 설계

Manager의 자극 생성기(`/stimulate`)가 web 서버에 무작위 보안 이벤트를 발생시키고, 동시에 siem에서 Agent Daemon이 자율적으로 탐지하는지 검증.

**자극 유형 (5라운드, 22건):**
- Round 1: SQLi, XSS, 스캐너 UA, 경로 순회, FTP 접근
- Round 2: SSH 로그인(정상+실패), sudo 명령, 포트 스캔
- Round 3: 추가 웹 공격 5건
- Round 4: SSH 브루트포스 10회, sudo /etc/shadow, 사용자 생성 시도, cron 주입
- Round 5: 전체 포트 스캔, 서비스 버전 스캔, 웹 디렉토리 브루트포스

### 결과

**표 9. Agent Daemon 자율 탐지 결과**

| 항목 | 값 |
|------|-----|
| 총 감시 사이클 | 8 (v1: 4 + v2: 4) |
| 총 탐지 이벤트 | **40건** |
| Warning | **25건** (62.5%) |
| Normal | 13건 (32.5%) |
| Unknown | 2건 (5.0%) |
| 감시 대상 | 5개 (sshd, sudo, auditd, wazuh-indexer, Port 8002) |

**표 10. 자율 탐지 유형별 분석**

| 탐지 유형 | 건수 | Daemon 분석 내용 |
|----------|------|----------------|
| SSH 브루트포스 징후 | 8건 | "같은 IP에서 반복 패스워드 인증 — 브루트포스 공격 징후" |
| sudo 남용 | 8건 | "/tmp 스크립트를 root로 반복 실행 — 보안 위험" |
| 의심 포트 (8002) | 8건 | "Python venv 프로세스가 리스닝 — 정당성 확인 필요" |
| wazuh-indexer 보안 | 2건 | "Java security manager disabled — 보안 제한 해제됨" |
| auditd 정상 | 8건 | "SIEM 모니터링 정상 동작 확인" |

### 탐지 시간 (TTD)

Daemon의 감시 주기가 20~30초이므로, 자극 발생 후 **최대 30초 이내** 탐지. 자극 발생 시각과 daemon 이벤트 시각의 차이를 분석하면:

- 자극 발생: 08:49:26 ~ 08:55:30 (약 6분간 5라운드)
- 첫 탐지: 08:49:18 (Daemon이 이미 감시 중이었으므로 자극 전 기존 이상도 탐지)
- **평균 TTD: < 30초** (감시 주기와 동일)

## 5C.5 분석

### 자율성 수준 평가

| 단계 | 자율 여부 | 설명 |
|------|:--------:|------|
| 감시 대상 결정 | ✅ | LLM이 서버 분석 후 자동 결정 (5~7개) |
| 정상 기준 설정 | ✅ | baseline 자동 설정 |
| 이상 탐지 | ✅ | 패턴 매칭 + LLM 분석 (40건) |
| 심각도 판단 | ✅ | normal/warning/critical 자동 분류 |
| 보고서 생성 | ✅ | 각 이벤트에 대해 자연어 분석 보고서 |
| 자율 조치 | △ | 구현되었으나 본 실험에서는 조치 실행 사례 없음 |
| 감시 주기 조절 | ✅ | warning 시 자동 단축 |

### 경량 모델의 보안 분석 능력

gemma3:12b는 다음을 정확히 판단:
- SSH 패스워드 인증 반복 → 브루트포스 징후 (정확)
- /tmp 스크립트 sudo 실행 → 보안 위험 (정확)
- 미확인 포트 리스닝 → 조사 필요 (적절)
- Java security manager disabled → 보안 제한 해제 (정확)

### 한계

1. **자율 조치 미실행:** warning 이벤트에 대한 remediation 명령이 생성되었으나 실제 실행 사례가 없음 (LLM이 보수적으로 판단)
2. **반복 경보:** 동일 이상(SSH, sudo, Port)이 매 사이클마다 반복 탐지 — 경보 중복 제거(dedup) 필요
3. **Web Daemon 미실행:** web 서버의 watch_targets 명령이 파일 경로만 포함 (tail/grep 명령이 아닌 것으로 생성) — explore 프롬프트 개선 필요

## 5C.6 스케줄링 vs Agent Daemon

**표 11. 기존 방식과 Agent Daemon 비교**

| 차원 | cron 스케줄링 | Nagios/Zabbix | Agent Daemon |
|------|:---:|:---:|:---:|
| 감시 대상 결정 | 수동 | 수동 | **자율 (LLM)** |
| 이상 판단 | 임계값 | 임계값 | **LLM 분석** |
| 자연어 보고 | ✗ | ✗ | **✓** |
| 적응적 주기 | ✗ | ✗ | **✓** |
| 신규 서버 투입 | 수동 설정 | 수동 설정 | **explore → 자동** |
| 로컬 지식 축적 | ✗ | ✗ | **✓** |

Agent Daemon의 핵심 차별점은 **신규 서버 투입 시 설정이 필요 없다**는 것이다. Explore 1회 실행으로 LLM이 서버 환경을 파악하고 감시 대상을 결정하며, 이후 자율적으로 감시를 수행한다. 전통적 모니터링 도구는 감시 대상, 임계값, 경보 규칙을 모두 수동으로 설정해야 한다.
