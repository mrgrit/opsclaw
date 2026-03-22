# Master / Manager / SubAgent 프롬프트 작성 가이드

## 계층 구조와 프롬프트 역할

```
External Master (외부 AI)
   ↓ 자연어 작업 계획 → API 호출
Manager API (:8000)
   ↓ execute-plan / dispatch
SubAgent Runtime (:8002)
   ↓ 실제 명령 실행
대상 서버
```

각 계층은 다른 종류의 "판단"을 담당한다.
프롬프트는 해당 계층의 역할에 맞게 작성해야 한다.

---

## External Master (Mode B) 프롬프트

External Master는 **사용자 의도 → 구체적 작업 계획**을 담당한다.

### 핵심 원칙

```
1. 무엇을 해야 하는가? (사용자 요청 해석)
2. 어떤 순서로? (task order 결정)
3. 위험도는? (risk_level 판단)
4. 결과가 올바른가? (evidence stdout 해석)
5. 보고서에 무엇을 남길까? (completion-report 작성)
```

### 권장 System Prompt 구조

```
[역할 정의]
당신은 OpsClaw External Master입니다.
OpsClaw Manager API를 호출하여 IT 운영 작업을 완료하는 역할입니다.

[필독 가이드]
작업 시작 전 docs/agent-system-prompt.md를 읽으십시오.

[환경 정보]
- Manager API: http://localhost:8000
- SubAgent: http://{target-host}:8002
- 대상 서버: {description}

[제약 조건]
- 파괴적 명령은 반드시 사용자 확인 후 실행
- risk_level=critical은 dry_run 먼저
- 작업 완료 후 completion-report 제출 필수
```

전체 시스템 프롬프트 템플릿: `docs/agent-system-prompt.md` 참조.

---

## instruction_prompt 작성 요령

execute-plan의 `instruction_prompt`는 SubAgent가 실행할 bash 명령이다.

### 좋은 예

```json
{"instruction_prompt": "apt-get update -y && apt-get install -y nginx && systemctl enable nginx"}
```

- 단계적으로 연결된 명령은 `&&` 사용
- 대화형 입력이 없는 명령 (`-y` 플래그 등)
- 결과 확인 명령 포함 (`&& nginx -v`)

### 나쁜 예

```json
{"instruction_prompt": "nginx 설치해줘"}   ← 자연어 → 실행 실패
{"instruction_prompt": "read -p 'confirm?' x && ..."}  ← 대화형 → 무한 대기
```

### dispatch mode=auto (자동 변환)

자연어를 자동으로 bash 변환하려면 `mode=auto` 사용:

```bash
POST /projects/{id}/dispatch
{
  "command": "nginx 설치하고 서비스 시작해줘",
  "mode": "auto",
  "subagent_url": "http://localhost:8002"
}
```

내부적으로 LLM이 bash 명령으로 변환 후 실행. 단, 결과 예측 불가능하므로 프로덕션에서는 권장하지 않음.

---

## Native Master (Mode A) 프롬프트 커스터마이징

Mode A에서 master-service의 LLM이 사용하는 프롬프트:

```bash
# 현재 Master 프롬프트 조회
GET http://localhost:8001/prompt

# 프롬프트 업데이트 (Mode A 전용)
POST http://localhost:8001/prompt
{
  "system_prompt": "당신은 IT 운영 전문가입니다. ...",
  "instruction_template": "다음 요청을 분석하고 작업 계획을 수립하세요: {request_text}"
}
```

---

## risk_level 판단 기준

| risk_level | 기준 | 예시 |
|-----------|------|------|
| `low` | 읽기 전용, 상태 조회 | `df -h`, `cat /etc/os-release`, `systemctl status` |
| `medium` | 설치, 설정 변경 (가역적) | `apt-get install`, `systemctl restart`, `nginx -s reload` |
| `high` | 데이터 변경, 서비스 중단 가능성 | `systemctl stop`, `iptables -F`, DB 스키마 변경 |
| `critical` | 복구 불가능한 파괴적 작업 | `rm -rf`, `DROP TABLE`, `fdisk`, 인증서 삭제 |

`critical` 작업 처리 패턴:
```python
# 1. dry_run으로 계획 확인
dry = api.post(f"/projects/{id}/execute-plan",
               {"tasks": tasks, "dry_run": True, ...})
print(f"실행 예정 명령: {dry}")

# 2. 사용자 확인
if not confirm("정말 실행하시겠습니까?"):
    return

# 3. 실제 실행
api.post(f"/projects/{id}/execute-plan",
         {"tasks": tasks, "dry_run": False, ...})
```

---

## 에이전트 응답 해석

### execute-plan 응답

```json
{
  "tasks_total": 3,
  "tasks_ok": 3,
  "tasks_failed": 0,
  "overall": "success",
  "task_results": [
    {
      "order": 1,
      "title": "현황 수집",
      "status": "ok",
      "stdout": "hostname: web-01\n...",
      "stderr": "",
      "exit_code": 0
    }
  ]
}
```

해석 규칙:
- `overall=success`: 모든 task 성공 → completion-report outcome=success
- `overall=partial`: 일부 실패 → 실패 task 재실행 또는 outcome=partial
- `overall=failed`: 전체 실패 → 원인 분석 후 replan

### evidence 해석

```bash
GET /projects/{id}/evidence/summary
# {"total":5, "success_count":4, "failure_count":1, "success_rate":0.8}
```

`success_rate < 1.0` 이면:
1. 실패한 evidence의 stderr 확인
2. 원인 분석
3. instruction_prompt 수정 후 재실행 또는 completion-report에 이슈로 기록
