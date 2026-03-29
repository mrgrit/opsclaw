# OpsClaw CLI 레퍼런스

> **문서 버전**: 1.0 | **최종 수정**: 2026-03-30
> **소스 파일**: `apps/cli/opsclaw.py`

---

## 개요

OpsClaw CLI는 터미널에서 OpsClaw를 제어하는 커맨드라인 인터페이스이다.
자연어로 작업을 지시하거나, 단일 명령을 실행하거나, 프로젝트 상태를 조회할 수 있다.

### 실행 방법

```bash
# 직접 실행
python3 apps/cli/opsclaw.py <command> [options]

# 또는 PATH에 심볼릭 링크 생성 후
ln -s /home/opsclaw/opsclaw/apps/cli/opsclaw.py /usr/local/bin/opsclaw
chmod +x /usr/local/bin/opsclaw
opsclaw <command> [options]
```

### 도움말

```bash
python3 apps/cli/opsclaw.py --help
# usage: opsclaw [-h] {run,dispatch,d,list,ls,status,st,replay,servers,sv} ...
#
# OpsClaw CLI -- 보안 운영 자동화 플랫폼
```

---

## 환경변수

CLI는 다음 환경변수를 참조한다.

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `OPSCLAW_MANAGER_URL` | `http://localhost:8000` | Manager API 주소 |
| `OPSCLAW_MASTER_URL` | `http://localhost:8001` | Master Service 주소 |
| `OPSCLAW_API_KEY` | `opsclaw-api-key-2026` | API 인증 키 |

```bash
# 환경변수 설정 (선택 - 기본값이 있으므로 변경할 때만)
export OPSCLAW_MANAGER_URL="http://localhost:8000"
export OPSCLAW_MASTER_URL="http://localhost:8001"
export OPSCLAW_API_KEY="opsclaw-api-key-2026"
```

---

## 서버 별명

CLI에 내장된 서버 별명 매핑:

| 별명 | SubAgent URL | 서버 설명 |
|------|-------------|-----------|
| `local` | `http://localhost:8002` | 로컬 (opsclaw 서버) |
| `secu` | `http://192.168.208.150:8002` | 물리 방화벽/IPS |
| `web` | `http://192.168.208.151:8002` | 물리 웹 서버 |
| `siem` | `http://192.168.208.152:8002` | 물리 SIEM |
| `v-secu` | `http://192.168.0.108:8002` | 가상 방화벽/IPS |
| `v-web` | `http://192.168.0.110:8002` | 가상 웹 서버 |
| `v-siem` | `http://192.168.0.109:8002` | 가상 SIEM |

별명 외에도 IP 주소나 URL을 직접 지정할 수 있다:

```bash
# 별명 사용
opsclaw run "점검" -t v-secu

# IP 주소 직접 지정 (자동으로 http://IP:8002 로 변환)
opsclaw run "점검" -t 192.168.0.108

# URL 직접 지정
opsclaw run "점검" -t http://192.168.0.108:8002
```

---

## 명령어 상세

### `run` — 자연어 작업 실행

LLM이 작업 계획을 수립하고 자동으로 실행한다.

**구문**:
```
opsclaw run <요청 내용> [-t 대상서버] [--manual] [--sequential]
```

**옵션**:

| 옵션 | 단축 | 기본값 | 설명 |
|------|------|--------|------|
| `--target` | `-t` | `local` | 대상 서버 (별명 또는 IP) |
| `--manual` | | (없음) | external 모드로 실행 (LLM 계획 없이 직접 실행) |
| `--sequential` | | (없음) | 태스크를 순차 실행 (기본: 병렬) |

**예시**:

```bash
# 기본 사용 (로컬 서버, Native 모드)
opsclaw run "서버 현황 점검해줘"

# 원격 서버 지정
opsclaw run "방화벽 규칙 확인" -t v-secu

# 순차 실행 (의존 관계가 있는 작업)
opsclaw run "패키지 업데이트 후 nginx 설치" -t v-web --sequential

# manual 모드 (LLM 계획 없이 명령 직접 전달)
opsclaw run "df -h && free -m" --manual -t local
```

**실행 흐름 (Native 모드)**:

```
1. POST /projects (master_mode: "native")
2. POST /projects/{id}/master-plan → LLM 계획 수립
3. POST /projects/{id}/plan
4. POST /projects/{id}/execute
5. POST /projects/{id}/execute-plan (tasks 실행)
6. GET  /projects/{id}/evidence/summary
7. POST /projects/{id}/completion-report
```

**실행 흐름 (--manual 모드)**:

```
1. POST /projects (master_mode: "external")
2. POST /projects/{id}/plan
3. POST /projects/{id}/execute
4. POST /projects/{id}/dispatch (요청 텍스트를 명령으로 직접 전달)
```

**출력 예시**:

```
요청: 서버 현황 점검해줘
대상: http://localhost:8002

프로젝트: prj_abc123
Master LLM이 계획 수립 중...
3개 태스크 생성:
   [1] 시스템 기본 정보 수집
   [2] 디스크/메모리 현황
   [3] 네트워크 상태 점검

실행 중...
============================================================
결과: success | 성공: 3/3
============================================================

[1] 시스템 기본 정보 수집 (1.20s)
   Linux opsclaw 6.8.0-106-generic ...

[2] 디스크/메모리 현황 (0.85s)
   /dev/sda1  50G  12G  38G  24% /

[3] 네트워크 상태 점검 (0.92s)
   tcp  0  0 0.0.0.0:8000 ...

Evidence: 3건 | 성공률: 100%
보고서 생성 완료

프로젝트 ID: prj_abc123
```

---

### `dispatch` (별칭: `d`) — 단일 명령 실행

LLM 계획 없이 shell 명령을 즉시 실행한다.

**구문**:
```
opsclaw dispatch <명령어> [-t 대상서버]
opsclaw d <명령어> [-t 대상서버]
```

**옵션**:

| 옵션 | 단축 | 기본값 | 설명 |
|------|------|--------|------|
| `--target` | `-t` | `local` | 대상 서버 |

**예시**:

```bash
# 로컬에서 hostname 확인
opsclaw dispatch "hostname && uptime"

# 별칭 사용
opsclaw d "hostname && uptime"

# 원격 서버에서 실행
opsclaw d "systemctl status apache2" -t v-web

# 방화벽 규칙 확인
opsclaw d "nft list ruleset | head -20" -t v-secu

# Wazuh 알림 확인
opsclaw d "cat /var/ossec/logs/alerts/alerts.json | tail -5" -t v-siem
```

**출력 예시**:

```
opsclaw
 10:30:45 up 5 days, 12:30,  2 users,  load average: 0.15, 0.20, 0.18
```

> **참고**: dispatch는 내부적으로 프로젝트를 자동 생성하고 Stage 전환을 수행한다. Evidence도 자동 기록된다.

---

### `list` (별칭: `ls`) — 프로젝트 목록

최근 프로젝트 목록을 조회한다.

**구문**:
```
opsclaw list [-n 개수]
opsclaw ls [-n 개수]
```

**옵션**:

| 옵션 | 단축 | 기본값 | 설명 |
|------|------|--------|------|
| `--limit` | `-n` | `10` | 표시할 프로젝트 수 |

**예시**:

```bash
# 최근 10개 프로젝트
opsclaw list

# 최근 5개만
opsclaw ls -n 5
```

**출력 예시**:

```
ID             Name                                     Stage      Mode
---------------------------------------------------------------------------
prj_a1b2c3d4e  quickstart-test                          execute    external
prj_f5e6d7c8b  cli-1711800000                           execute    native
prj_99887766a  dispatch-1711799500                      execute    external
```

---

### `status` (별칭: `st`) — 프로젝트 상태

특정 프로젝트의 상세 상태를 조회한다.

**구문**:
```
opsclaw status <project_id>
opsclaw st <project_id>
```

**예시**:

```bash
opsclaw status prj_a1b2c3d4e5f6
```

**출력 예시**:

```
ID:      prj_a1b2c3d4e5f6
Name:    quickstart-test
Stage:   execute
Mode:    external
Request: 서버 현황 점검 및 디스크 사용량 확인
Evidence: 4건
```

---

### `replay` — 실행 이력 재현

프로젝트의 전체 실행 타임라인을 시간순으로 보여준다.

**구문**:
```
opsclaw replay <project_id>
```

**예시**:

```bash
opsclaw replay prj_a1b2c3d4e5f6
```

**출력 예시**:

```
Replay -- 3 events
  [2026-03-30T10:30:45] 시스템 정보 수집                          → opsclaw 10:30:45 up 5 days...
  [2026-03-30T10:30:46] 디스크 사용량 확인                        → /dev/sda1  50G  12G  38G  24%
  [2026-03-30T10:30:47] 메모리 상태 확인                          → Mem: 16384  8192  8192
```

---

### `servers` (별칭: `sv`) — 서버 상태

등록된 모든 서버의 SubAgent 연결 상태를 확인한다.

**구문**:
```
opsclaw servers
opsclaw sv
```

**출력 예시**:

```
Alias      URL                                 Status
-------------------------------------------------------
local      http://localhost:8002               online
secu       http://192.168.208.150:8002         online
siem       http://192.168.208.152:8002         offline
v-secu     http://192.168.0.108:8002           online
v-siem     http://192.168.0.109:8002           offline
v-web      http://192.168.0.110:8002           online
web        http://192.168.208.151:8002         online
```

> **참고**: 각 서버의 `/health` 엔드포인트를 호출하여 상태를 확인한다. 타임아웃은 2초이다.

---

## 실전 활용 시나리오

### 시나리오 1: 일일 서버 점검

```bash
# 1. 전체 서버 상태 확인
opsclaw sv

# 2. 주요 서버 순차 점검
opsclaw run "시스템 현황 종합 점검" -t v-secu
opsclaw run "웹 서비스 상태 점검" -t v-web
opsclaw run "SIEM 알림 현황 확인" -t v-siem

# 3. 결과 확인
opsclaw ls -n 3
opsclaw replay <최신 프로젝트 ID>
```

### 시나리오 2: 긴급 보안 패치

```bash
# 1. 패치 대상 서버 확인
opsclaw d "apt list --upgradable 2>/dev/null | grep -i security" -t v-web

# 2. 패치 적용 (순차 실행)
opsclaw run "보안 패치 업데이트 적용" -t v-web --sequential

# 3. 서비스 정상 확인
opsclaw d "systemctl status apache2" -t v-web
```

### 시나리오 3: 보안 감사 자동화

```bash
# 1. 방화벽 규칙 감사
opsclaw run "방화벽 규칙을 점검하고 불필요한 오픈 포트를 찾아줘" -t v-secu

# 2. TLS 인증서 확인
opsclaw d "openssl s_client -connect localhost:443 -servername localhost < /dev/null 2>/dev/null | openssl x509 -noout -dates" -t v-web

# 3. 시스템 계정 감사
opsclaw d "awk -F: '\$3 >= 1000 {print \$1, \$3, \$7}' /etc/passwd" -t v-secu
```

### 시나리오 4: 디스크 공간 관리

```bash
# 1. 디스크 사용량 확인
opsclaw d "df -h && echo '---' && du -sh /var/log/* | sort -rh | head -10" -t local

# 2. 로그 정리 (주의: 파괴적 명령)
opsclaw d "journalctl --vacuum-time=7d" -t local
```

---

## 스크립트에서 활용

### Bash 스크립트

```bash
#!/bin/bash
# daily_check.sh - 일일 서버 점검 스크립트

SERVERS=(v-secu v-web v-siem)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

for server in "${SERVERS[@]}"; do
  echo "=== $server 점검 시작 ==="
  python3 /home/opsclaw/opsclaw/apps/cli/opsclaw.py \
    run "서버 전체 현황 점검" -t "$server"
  echo ""
done

# 결과 확인
python3 /home/opsclaw/opsclaw/apps/cli/opsclaw.py ls -n ${#SERVERS[@]}
```

### Cron 등록

```bash
# 매일 오전 9시 일일 점검
0 9 * * * /home/opsclaw/opsclaw/scripts/daily_check.sh >> /var/log/opsclaw_daily.log 2>&1
```

---

## 에러 대응

### "requests 패키지가 필요합니다"

```bash
source .venv/bin/activate
pip install requests
```

### "connection refused" (Manager API)

```bash
# Manager API 재시작
./dev.sh manager
# 또는
kill $(pgrep -f "manager-api"); sleep 2; ./dev.sh manager
```

### "Master LLM 계획 수립 실패"

Ollama 서버 상태 확인:
```bash
curl -s http://192.168.0.105:11434/api/tags
```

LLM 없이 실행하려면 `--manual` 옵션 사용:
```bash
opsclaw run "df -h" --manual -t local
```

### "SubAgent 연결 실패"

```bash
# 서버 상태 확인
opsclaw servers

# 해당 서버에 SubAgent 재배포
./scripts/deploy_subagent.sh secu
```

---

## 다음 단계

- **Master Service API 상세**: [03-master-service.md](03-master-service.md)
- **Claude Code 모드**: [../claude-code-mode/01-overview.md](../claude-code-mode/01-overview.md)
- **API 전체 가이드**: [../claude-code-mode/02-api-guide.md](../claude-code-mode/02-api-guide.md)
