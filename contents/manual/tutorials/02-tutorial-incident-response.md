# 튜토리얼: SSH 브루트포스 대응 -- NIST IR 6단계

## 학습 목표

이 튜토리얼을 완료하면 다음을 할 수 있다.

- NIST 인시던트 대응 프레임워크 6단계를 OpsClaw로 실행한다
- Wazuh 알림에서 공격 정보를 추출한다
- nftables로 공격 IP를 차단한다
- 인시던트의 전체 과정을 Evidence로 기록한다
- PoW 체인으로 대응 이력의 무결성을 보장한다

**소요 시간:** 약 45분
**난이도:** 중급
**시나리오 출처:** 기술 소설 Vol.1 Ch.2 "침입의 시작"

---

## 시나리오

```
2026-03-30 오전 10시.
OpsClaw SOC 대시보드에 Wazuh 고위험 알림이 표시되었다.
rule.id 5763 — "Multiple SSH login failures from same source IP."
공격자 IP 203.0.113.50에서 30초 안에 SSH 로그인 시도가 8회 발생.
현재도 진행 중인 브루트포스 공격으로 판단된다.

대응팀은 NIST SP 800-61의 인시던트 대응 절차에 따라
탐지, 분석, 격리, 제거, 복구, 교훈 6단계를 수행한다.
```

---

## 사전 준비

```bash
export OPSCLAW_API_KEY=opsclaw-api-key-2026
SECU="http://192.168.0.108:8002"
SIEM="http://192.168.0.109:8002"
alias oc='curl -s -H "X-API-Key: $OPSCLAW_API_KEY" -H "Content-Type: application/json"'
```

---

## 1단계: 준비 (Preparation)

인시던트 대응 프로젝트를 생성하고 초기 정보를 기록한다.

```bash
# 인시던트 대응 프로젝트 생성
oc -X POST http://localhost:8000/projects \
  -d '{
    "name": "ir-ssh-bruteforce-20260330",
    "request_text": "SSH 브루트포스 공격 탐지. 공격자 IP: 203.0.113.50. NIST IR 6단계 대응 수행.",
    "master_mode": "external"
  }'

PID="<project.id>"

# Stage 전환
oc -X POST http://localhost:8000/projects/$PID/plan
oc -X POST http://localhost:8000/projects/$PID/execute
```

**결과:** 프로젝트가 `execute` stage로 전환되었다. 이제부터 모든 명령이 Evidence로 기록된다.

---

## 2단계: 탐지 (Detection)

Wazuh SIEM에서 알림 상세를 확인한다.

### 2.1 Wazuh 알림 조회

```bash
oc -X POST http://localhost:8000/projects/$PID/execute-plan \
  -d '{
    "tasks": [
      {
        "order": 1,
        "title": "[Detection] Wazuh SSH 알림 조회",
        "instruction_prompt": "tail -300 /var/ossec/logs/alerts/alerts.json | python3 -c \"import json,sys\nalerts=[json.loads(l) for l in sys.stdin if l.strip()]\nssh=[a for a in alerts if \\\"sshd\\\" in str(a.get(\\\"rule\\\",{}).get(\\\"groups\\\",[])) and a.get(\\\"rule\\\",{}).get(\\\"level\\\",0)>=8]\nprint(f\\\"SSH 관련 고위험 알림: {len(ssh)}건\\\")\nfor a in ssh[-10:]:\n    print(f\\\"  [{a[\\\"rule\\\"][\\\"level\\\"]}] rule.id={a[\\\"rule\\\"][\\\"id\\\"]} {a[\\\"rule\\\"].get(\\\"description\\\",\\\"\\\")} srcip={a.get(\\\"srcip\\\",\\\"-\\\")}\\\")\n\"",
        "risk_level": "low",
        "subagent_url": "'$SIEM'"
      },
      {
        "order": 2,
        "title": "[Detection] v-secu SSH 로그 확인",
        "instruction_prompt": "journalctl -u ssh --since \"2 hours ago\" | grep -i \"failed\" | tail -30",
        "risk_level": "low",
        "subagent_url": "'$SECU'"
      }
    ]
  }'
```

**기대 결과:** Wazuh 알림에서 공격 IP와 시도 횟수를 확인할 수 있다.

---

## 3단계: 분석 (Analysis)

공격의 범위와 심각도를 파악한다.

### 3.1 공격 IP 분석

```bash
oc -X POST http://localhost:8000/projects/$PID/execute-plan \
  -d '{
    "tasks": [
      {
        "order": 3,
        "title": "[Analysis] 공격 IP별 시도 횟수",
        "instruction_prompt": "journalctl -u ssh --since \"6 hours ago\" | grep \"Failed password\" | awk \"{print \\$11}\" | sort | uniq -c | sort -rn | head -20",
        "risk_level": "low",
        "subagent_url": "'$SECU'"
      },
      {
        "order": 4,
        "title": "[Analysis] 대상 계정 분석",
        "instruction_prompt": "journalctl -u ssh --since \"6 hours ago\" | grep \"Failed password\" | grep 203.0.113.50 | awk \"{print \\$9}\" | sort | uniq -c | sort -rn | head -10",
        "risk_level": "low",
        "subagent_url": "'$SECU'"
      },
      {
        "order": 5,
        "title": "[Analysis] 성공한 로그인 확인 (침입 여부)",
        "instruction_prompt": "journalctl -u ssh --since \"6 hours ago\" | grep \"Accepted\" | grep 203.0.113.50 || echo \"NO successful login from 203.0.113.50\"",
        "risk_level": "low",
        "subagent_url": "'$SECU'"
      },
      {
        "order": 6,
        "title": "[Analysis] 현재 세션 확인",
        "instruction_prompt": "who && echo \"---\" && last -i | head -20",
        "risk_level": "low",
        "subagent_url": "'$SECU'"
      }
    ]
  }'
```

### 3.2 분석 결과 해석

Evidence를 확인하여 다음을 판단한다.

```bash
# Evidence 확인
oc http://localhost:8000/projects/$PID/evidence/summary
```

판단 기준:
- 공격 IP에서 성공한 로그인이 있는가? → 있으면 침입 확정, 없으면 시도만
- 어떤 계정을 노렸는가? → root, admin 등 고위험 계정 여부
- 현재 세션에 공격자가 있는가? → 있으면 즉시 강제 종료 필요

---

## 4단계: 격리 (Containment)

공격 IP를 차단하고 추가 피해를 방지한다.

### 4.1 nftables로 공격 IP 차단

```bash
oc -X POST http://localhost:8000/projects/$PID/execute-plan \
  -d '{
    "tasks": [
      {
        "order": 7,
        "title": "[Containment] 공격 IP nftables 차단",
        "instruction_prompt": "nft insert rule inet filter input ip saddr 203.0.113.50 counter drop && echo \"IP 203.0.113.50 blocked\"",
        "risk_level": "high",
        "subagent_url": "'$SECU'"
      },
      {
        "order": 8,
        "title": "[Containment] 차단 규칙 확인",
        "instruction_prompt": "nft list chain inet filter input | grep -A1 203.0.113.50",
        "risk_level": "low",
        "subagent_url": "'$SECU'"
      },
      {
        "order": 9,
        "title": "[Containment] SSH MaxAuthTries 제한",
        "instruction_prompt": "grep MaxAuthTries /etc/ssh/sshd_config && echo \"현재 설정 확인 완료\"",
        "risk_level": "low",
        "subagent_url": "'$SECU'"
      }
    ],
    "confirmed": true
  }'
```

### 4.2 차단 후 즉시 확인

```bash
# 차단 IP에서 더 이상 시도가 없는지 실시간 확인
oc -X POST http://localhost:8000/projects/$PID/dispatch \
  -d '{
    "command": "timeout 10 tail -f /var/log/auth.log | grep 203.0.113.50 || echo \"No more attempts from blocked IP (10s timeout)\"",
    "subagent_url": "'$SECU'",
    "timeout_s": 15
  }'
```

---

## 5단계: 제거 (Eradication)

침입 흔적을 확인하고 제거한다.

### 5.1 침입 흔적 조사

```bash
oc -X POST http://localhost:8000/projects/$PID/execute-plan \
  -d '{
    "tasks": [
      {
        "order": 10,
        "title": "[Eradication] 의심스러운 프로세스 확인",
        "instruction_prompt": "ps auxf | grep -v grep | head -30 && echo \"---\" && netstat -tlnp 2>/dev/null || ss -tlnp",
        "risk_level": "low",
        "subagent_url": "'$SECU'"
      },
      {
        "order": 11,
        "title": "[Eradication] 최근 수정된 파일 확인",
        "instruction_prompt": "find /tmp /var/tmp /home -mmin -120 -type f 2>/dev/null | head -20 || echo \"No recently modified suspicious files\"",
        "risk_level": "low",
        "subagent_url": "'$SECU'"
      },
      {
        "order": 12,
        "title": "[Eradication] crontab 확인 (백도어 확인)",
        "instruction_prompt": "for user in $(cut -f1 -d: /etc/passwd); do crontab -l -u $user 2>/dev/null | grep -v '^#' | grep . && echo \"  ↑ crontab for: $user\"; done || echo \"No suspicious crontabs\"",
        "risk_level": "low",
        "subagent_url": "'$SECU'"
      },
      {
        "order": 13,
        "title": "[Eradication] authorized_keys 확인",
        "instruction_prompt": "find /home /root -name authorized_keys -exec echo \"=== {} ===\" \\; -exec cat {} \\; 2>/dev/null || echo \"No authorized_keys found\"",
        "risk_level": "low",
        "subagent_url": "'$SECU'"
      }
    ]
  }'
```

### 5.2 SSH 설정 강화 (침입이 확인된 경우)

```bash
oc -X POST http://localhost:8000/projects/$PID/execute-plan \
  -d '{
    "tasks": [
      {
        "order": 14,
        "title": "[Eradication] SSH 설정 강화",
        "instruction_prompt": "cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak.$(date +%Y%m%d) && sed -i \"s/^#*PermitRootLogin.*/PermitRootLogin no/\" /etc/ssh/sshd_config && sed -i \"s/^#*MaxAuthTries.*/MaxAuthTries 3/\" /etc/ssh/sshd_config && sed -i \"s/^#*PasswordAuthentication.*/PasswordAuthentication no/\" /etc/ssh/sshd_config && echo \"SSH config hardened\"",
        "risk_level": "high",
        "subagent_url": "'$SECU'"
      },
      {
        "order": 15,
        "title": "[Eradication] SSH 설정 검증 및 재시작",
        "instruction_prompt": "sshd -t && systemctl restart sshd && systemctl is-active sshd && grep -E \"(PermitRootLogin|MaxAuthTries|PasswordAuthentication)\" /etc/ssh/sshd_config | grep -v '^#'",
        "risk_level": "high",
        "subagent_url": "'$SECU'"
      }
    ],
    "confirmed": true
  }'
```

---

## 6단계: 복구 (Recovery)

서비스 정상 동작을 확인한다.

```bash
oc -X POST http://localhost:8000/projects/$PID/execute-plan \
  -d '{
    "tasks": [
      {
        "order": 16,
        "title": "[Recovery] SSH 서비스 정상 확인",
        "instruction_prompt": "systemctl status sshd --no-pager && ss -tlnp | grep :22",
        "risk_level": "low",
        "subagent_url": "'$SECU'"
      },
      {
        "order": 17,
        "title": "[Recovery] 정상 사용자 SSH 접속 테스트",
        "instruction_prompt": "echo \"SSH service is active on port 22\" && who | wc -l && echo \"active sessions\"",
        "risk_level": "low",
        "subagent_url": "'$SECU'"
      },
      {
        "order": 18,
        "title": "[Recovery] Wazuh 에이전트 정상 확인",
        "instruction_prompt": "/var/ossec/bin/agent_control -l | head -10",
        "risk_level": "low",
        "subagent_url": "'$SIEM'"
      },
      {
        "order": 19,
        "title": "[Recovery] nftables 차단 규칙 영구 저장",
        "instruction_prompt": "nft list ruleset > /etc/nftables.conf && echo \"Rules saved permanently\"",
        "risk_level": "medium",
        "subagent_url": "'$SECU'"
      }
    ]
  }'
```

---

## 사후 처리: 교훈 (Lessons Learned)

### Evidence 전체 확인

```bash
# Evidence 요약
oc http://localhost:8000/projects/$PID/evidence/summary

# 전체 Evidence 목록 (19건)
oc http://localhost:8000/projects/$PID/evidence
```

### PoW 체인 검증

```bash
# 대응 이력의 무결성 검증
oc "http://localhost:8000/pow/verify?agent_id=$SECU"
# → {"valid": true, "blocks": N, "orphans": 0, "tampered": []}

# 프로젝트 PoW 블록 조회
oc http://localhost:8000/projects/$PID/pow
```

### 작업 Replay

```bash
# 전체 대응 과정 타임라인
oc http://localhost:8000/projects/$PID/replay
```

### 완료보고서 작성

```bash
oc -X POST http://localhost:8000/projects/$PID/completion-report \
  -d '{
    "summary": "SSH 브루트포스 인시던트 대응 완료. NIST IR 6단계 수행.",
    "outcome": "success",
    "work_details": [
      "[Detection] Wazuh rule.id 5763, 공격자 IP: 203.0.113.50, 시도 487회",
      "[Analysis] 침입 성공 없음 확인, 대상 계정: root, admin, ubuntu",
      "[Containment] nftables drop 규칙 적용, 즉시 차단 확인",
      "[Eradication] 백도어/crontab/authorized_keys 이상 없음, SSH 설정 강화",
      "[Recovery] SSH 서비스 정상, nftables 규칙 영구 저장"
    ],
    "issues": [
      "PermitRootLogin=yes 상태였음 → no로 변경 완료",
      "MaxAuthTries 제한 없었음 → 3으로 설정"
    ],
    "next_steps": [
      "fail2ban 또는 OpsClaw Watcher로 자동 차단 구축",
      "SSH key-based authentication 전면 도입",
      "정기 보안 감사에 SSH 설정 점검 항목 추가"
    ]
  }'
```

### 경험 축적

```bash
# Task Memory + Experience 자동 생성
oc -X POST "http://localhost:8000/projects/$PID/memory/build?promote=true"
```

이 경험은 다음에 유사한 인시던트가 발생했을 때 Master의 작업 계획에 RAG로 참조된다.

### 프로젝트 종료

```bash
oc -X POST http://localhost:8000/projects/$PID/close
```

---

## 전체 흐름 요약 (NIST 6단계 + OpsClaw)

```
단계              Task 수   risk_level    주요 명령
─────────────────────────────────────────────────────
1. Preparation    1         -            프로젝트 생성
2. Detection      2         low          Wazuh 알림 + SSH 로그
3. Analysis       4         low          IP 분석 + 침입 여부 + 세션
4. Containment    3         high         nftables 차단 + 확인
5. Eradication    4-6       low~high     프로세스/파일/crontab/SSH 강화
6. Recovery       4         low~medium   서비스 확인 + 규칙 저장
─────────────────────────────────────────────────────
합계             18-20건    Evidence + PoW 블록 전체 기록
```

---

## 소설 Vol.1 Ch.2 연결

이 튜토리얼의 시나리오는 기술 소설 Vol.1 Ch.2의 장면과 동일하다.

> "여기 봐." 재현이 화면을 가리켰다.
> Wazuh 대시보드에 rule.id 5763이 빨간 점으로 점멸하고 있었다.
> 203.0.113.50에서 30초 안에 8번의 SSH 로그인 시도.
>
> 수진이 OpsClaw 터미널을 열었다.
> `opsclaw run "203.0.113.50 SSH 차단" --target v-secu`
>
> 화면에 Evidence가 기록되었다. PoW 블록이 생성되었다.
> 이 기록은 영원히 남는다.

소설의 독자는 이 튜토리얼을 통해 실제 같은 작업을 수행할 수 있다.
CTF 문제 "ssh-bruteforce-block"에서 이 시나리오를 플래그로 검증한다.
