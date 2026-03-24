# OpsClaw — sudo 운용 가이드 (M22)

## 개요

SubAgent가 실행하는 명령 중 `sudo`가 포함된 경우, OpsClaw는 자동으로 `risk_level`을 **high** 이상으로 상향 조정한다.
이는 elevated privilege 명령이 시스템에 미치는 영향을 명시적으로 통제하기 위함이다.

---

## 자동 위험도 상향 규칙

| 조건 | 동작 |
|------|------|
| `instruction_prompt`에 `\bsudo\b` 포함 + `risk_level`이 `low` 또는 `medium` | → `risk_level = high` 자동 상향, 응답에 `sudo_elevated: true` 표시 |
| `risk_level = critical` (수동 지정) | → `confirmed: true` 없으면 `dry_run` 강제 (B-05 규칙) |

## 동작 예시

```bash
# sudo 포함 태스크 → risk_level 자동 high 상향
curl -X POST http://localhost:8000/projects/{id}/execute-plan \
  -H "Content-Type: application/json" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "title": "패키지 업데이트",
        "instruction_prompt": "sudo apt-get update && sudo apt-get upgrade -y",
        "risk_level": "low"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }'

# 응답 예시
# {
#   "task_results": [{
#     "risk_level": "high",    ← low에서 자동 상향
#     "sudo_elevated": true,   ← 상향 이유 명시
#     ...
#   }]
# }
```

---

## SubAgent sudoers 설정 (권장)

SubAgent가 실행되는 서버에서 최소 권한 원칙을 따른다.
`/etc/sudoers.d/opsclaw` 파일을 생성하고 허용할 명령만 명시한다.

```bash
# /etc/sudoers.d/opsclaw
# SubAgent 계정(예: opsclaw)에 특정 명령만 NOPASSWD 허용

opsclaw ALL=(ALL) NOPASSWD: /usr/bin/apt-get update
opsclaw ALL=(ALL) NOPASSWD: /usr/bin/apt-get upgrade *
opsclaw ALL=(ALL) NOPASSWD: /bin/systemctl restart *
opsclaw ALL=(ALL) NOPASSWD: /bin/systemctl start *
opsclaw ALL=(ALL) NOPASSWD: /bin/systemctl stop *
opsclaw ALL=(ALL) NOPASSWD: /usr/sbin/service * restart

# 절대 허용 금지 (예시)
# opsclaw ALL=(ALL) NOPASSWD: ALL   ← 전체 허용 금지
# opsclaw ALL=(ALL) NOPASSWD: /bin/rm -rf *   ← 삭제 명령 금지
```

```bash
# 적용
sudo visudo -c -f /etc/sudoers.d/opsclaw   # 문법 검증
sudo chmod 440 /etc/sudoers.d/opsclaw
```

---

## OpsClaw에서 sudo 사용 안전 규칙

### 1. risk_level 지침

| risk_level | 의미 | sudo 사용 |
|-----------|------|---------|
| `low` | 읽기 전용, 조회 | 사용 금지 |
| `medium` | 상태 조회, 서비스 재시작 | 최소한으로 |
| `high` | 패키지 설치, 설정 변경 | 허용 (자동 상향) |
| `critical` | 시스템 전체 변경, 삭제 | `confirmed: true` 필수 |

### 2. Playbook Step에서 sudo 사용 시

Playbook step의 `metadata.script`에 sudo가 포함되면 그대로 실행된다.
`metadata.params.risk_level = "high"` 를 step에 명시하는 것을 권장한다.

```json
{
  "order": 1,
  "type": "tool",
  "ref": "run_command",
  "name": "패키지 설치",
  "metadata": {
    "command": "sudo apt-get install -y nginx",
    "params": {
      "risk_level": "high"
    }
  }
}
```

### 3. critical sudo 명령 실행 절차

```bash
# 1단계: dry_run으로 계획 확인
curl -X POST http://localhost:8000/projects/{id}/execute-plan \
  -d '{"tasks": [...sudo critical commands...], "dry_run": true}'

# 2단계: 결과 검토 후 confirmed=true로 실제 실행
curl -X POST http://localhost:8000/projects/{id}/execute-plan \
  -d '{"tasks": [...], "confirmed": true}'
```

---

## 관련 설정

- `CLAUDE.md` — `risk_level=critical` 태스크 사용자 확인 필수 규칙
- `docs/agent-system-prompt.md` — SubAgent 안전 규칙
- B-05 버그 수정: `confirmed: true` 없으면 critical 태스크 dry_run 강제
