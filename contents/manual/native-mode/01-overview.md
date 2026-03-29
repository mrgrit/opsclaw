# Native 모드 (Mode A) 개요

> **문서 버전**: 1.0 | **최종 수정**: 2026-03-30

---

## Native 모드란 무엇인가

Native 모드(Mode A)는 OpsClaw 자체에 내장된 LLM(Ollama)이 작업 계획을 수립하고
자동으로 실행하는 모드이다. 사용자는 자연어로 요청만 하면 되고,
나머지는 OpsClaw가 자동으로 처리한다.

```
사용자 → CLI → Master Service(:8001) → Ollama LLM → 작업 계획 수립
                                                         ↓
                     Manager API(:8000) ← tasks 배열 전달
                           ↓
                     SubAgent(:8002) → 명령 실행
                           ↓
                     Evidence + PoW 자동 기록 → 완료 보고서
```

---

## 동작 원리

### 전체 흐름 (단계별)

| 단계 | 구성 요소 | 동작 |
|------|-----------|------|
| 1 | CLI / 사용자 | 자연어로 작업 요청 (예: "방화벽 규칙 확인해줘") |
| 2 | CLI | `POST /projects` 로 프로젝트 생성 (`master_mode: "native"`) |
| 3 | CLI → Master Service | `POST /projects/{id}/master-plan` 호출 |
| 4 | Master Service | Ollama LLM에 프롬프트 전송 → tasks 배열 생성 |
| 5 | Master Service | 유사 Playbook/과거 보고서를 RAG로 검색하여 참고 |
| 6 | CLI | Stage 전환: `/plan` → `/execute` |
| 7 | CLI → Manager | `POST /projects/{id}/execute-plan` 으로 tasks 실행 |
| 8 | Manager → SubAgent | 각 task를 SubAgent에 dispatch |
| 9 | Manager | Evidence 기록, PoW 블록 생성, 보상 지급 |
| 10 | CLI | 결과 출력 + 완료보고서 자동 제출 |

### LLM 계획 수립 상세

Master Service의 `/master-plan` 엔드포인트가 호출되면:

1. 프로젝트의 `request_text`를 가져온다
2. **RAG 검색**: 기존 Playbook과 유사한 과거 완료보고서를 검색한다
3. **프롬프트 구성**: 요구사항 + 참고 Playbook + 과거 보고서를 조합하여 LLM 프롬프트를 생성한다
4. **LLM 호출**: Ollama에 프롬프트를 전송하여 JSON 형식의 tasks 배열을 받는다
5. **응답 파싱**: LLM 출력에서 JSON을 추출하고 검증한다
6. **폴백**: LLM 실패 시 단순 단일 태스크 플랜을 반환한다

LLM이 생성하는 tasks 배열 형식:
```json
{
  "summary": "서버 현황 점검을 위해 3단계 작업을 수행합니다",
  "tasks": [
    {
      "order": 1,
      "title": "시스템 기본 정보 수집",
      "playbook_hint": null,
      "instruction_prompt": "hostname && uptime && uname -a",
      "risk_level": "low"
    },
    {
      "order": 2,
      "title": "디스크 사용량 확인",
      "playbook_hint": null,
      "instruction_prompt": "df -h && du -sh /var/log/*",
      "risk_level": "low"
    }
  ]
}
```

---

## 언제 Native 모드를 사용하는가

### 적합한 경우

| 시나리오 | 이유 |
|----------|------|
| **표준화된 반복 작업** | 매일 같은 서버 점검, 패키지 업데이트 등 |
| **단순 상태 확인** | "서버 상태 보여줘", "디스크 사용량 확인" |
| **자동화된 스케줄 작업** | Schedule/Watcher와 연동하여 주기적 실행 |
| **빠른 단발 명령** | dispatch로 한 줄 명령 즉시 실행 |
| **CLI 친화적 환경** | 터미널에서 한 줄로 작업 완료 |

### 부적합한 경우 (Claude Code 모드 권장)

| 시나리오 | 이유 |
|----------|------|
| **복잡한 판단이 필요한 작업** | 소규모 LLM으로는 정교한 분석이 어려움 |
| **동적 워크플로우** | 이전 단계 결과를 보고 다음 단계를 결정해야 할 때 |
| **보안 사고 대응** | 상황 판단 + 즉각 대응이 필요한 경우 |
| **대화형 작업** | 사용자와 왕복 대화하며 작업을 진행할 때 |
| **코드 생성/수정** | 설정 파일 분석/수정이 필요한 경우 |

---

## Ollama LLM 구성

### 지원 모델

| 모델 | 크기 | 용도 | 위치 |
|------|------|------|------|
| `gpt-oss:120b` | 120B | 기본 마스터 모델 (가장 정확) | dgx-spark (192.168.0.105) |
| `qwen3:8b` | 8B | 경량 범용 모델 | dgx-spark |
| `gemma3:12b` | 12B | Red Team 에이전트 (보안 공격 시뮬레이션) | dgx-spark |
| `llama3.1:8b` | 8B | Blue Team 에이전트 (보안 방어 시뮬레이션) | dgx-spark |

### 환경변수 설정

```bash
# .env 파일에서 설정
OLLAMA_BASE_URL=http://192.168.0.105:11434/v1
OLLAMA_MODEL=gpt-oss:120b
```

### Ollama 서버 상태 확인

```bash
# 사용 가능한 모델 목록
curl -s http://192.168.0.105:11434/api/tags | python3 -m json.tool

# 모델 직접 테스트
curl -s http://192.168.0.105:11434/api/generate \
  -d '{"model": "qwen3:8b", "prompt": "hello", "stream": false}' | python3 -m json.tool
```

### 모델 선택 기준

| 상황 | 권장 모델 | 이유 |
|------|-----------|------|
| 일반 운영 작업 | `gpt-oss:120b` | 가장 정확한 계획 수립 |
| 빠른 응답 필요 | `qwen3:8b` | 가볍고 빠름 |
| 보안 공격 시뮬레이션 | `gemma3:12b` | Red Team 특화 |
| 보안 방어 분석 | `llama3.1:8b` | Blue Team 특화 |

---

## Native 모드의 특수 기능

### RAG (Retrieval-Augmented Generation)

Master Service는 작업 계획 수립 시 두 가지 소스를 자동으로 검색한다:

1. **기존 Playbook**: 유사한 이름의 Playbook을 찾아 재활용 가능한 절차를 참고
2. **과거 완료보고서**: 이전에 비슷한 작업을 수행한 기록을 참고하여 학습

이를 통해 반복 작업일수록 점점 더 정확한 계획을 수립한다.

### Review (검토)

Master Service의 `/review` 엔드포인트를 통해 실행 전 계획을 검토할 수 있다:

```bash
# 계획 검토 요청
curl -s -X POST http://localhost:8001/projects/$PID/review \
  -H "Content-Type: application/json" \
  -d '{
    "reviewer_id": "senior-admin",
    "review_status": "approved",
    "summary": "계획 확인 완료, 실행 승인"
  }'
```

검토 상태:
- `approved` — 실행 승인
- `rejected` — 실행 거부
- `needs_replan` — 계획 재수립 필요 (`auto_replan: true` 설정 시 자동 재수립)

### Replan (재계획)

검토 결과 계획 수정이 필요한 경우:

```bash
curl -s -X POST http://localhost:8001/projects/$PID/replan \
  -H "Content-Type: application/json" \
  -d '{"reason": "디스크 정리 단계가 누락됨"}'
```

### Escalate (에스컬레이션)

위험도가 높거나 판단이 어려운 경우 상위 담당자에게 에스컬레이션:

```bash
curl -s -X POST http://localhost:8001/projects/$PID/escalate \
  -H "Content-Type: application/json" \
  -d '{
    "level": 2,
    "reason": "critical risk task - 수동 승인 필요",
    "reviewer_id": "master-service"
  }'
```

---

## 제약 사항

### LLM 한계

| 제약 | 설명 | 대응 |
|------|------|------|
| **계획 정확도** | 8B~120B 모델은 복잡한 시나리오에서 부정확할 수 있음 | Claude Code 모드 사용 또는 Review 활용 |
| **JSON 파싱 실패** | LLM이 올바른 JSON을 출력하지 못할 수 있음 | 자동 폴백: 단일 태스크 플랜 반환 |
| **컨텍스트 제한** | 소규모 모델의 컨텍스트 윈도우 제한 | 요청을 짧고 명확하게 작성 |
| **환각(Hallucination)** | 존재하지 않는 명령이나 경로를 생성할 수 있음 | Evidence에서 exit_code 확인 |

### 네트워크 의존성

| 의존 | 설명 | 장애 시 |
|------|------|---------|
| Ollama 서버 | dgx-spark(192.168.0.105)에 접근 필요 | 폴백 단일 태스크 플랜 사용 |
| SubAgent 서버 | 대상 서버의 8002 포트 접근 필요 | 연결 오류 반환 |
| PostgreSQL | 로컬 5432 포트 접근 필요 | 서비스 기동 실패 |

### 보안 제약

- `risk_level=critical` 태스크는 자동으로 `dry_run`이 강제된다
- 파괴적 명령(rm -rf, DROP TABLE 등)은 LLM이 생성하더라도 사용자 확인이 필요하다
- SubAgent URL은 사용자가 지정한 서버만 사용한다

---

## 자주 사용하는 요청 예시

### 서버 점검

```bash
python3 apps/cli/opsclaw.py run "서버 전체 현황을 점검해줘" -t local
python3 apps/cli/opsclaw.py run "v-secu 보안 상태를 확인해줘" -t v-secu
python3 apps/cli/opsclaw.py run "v-web Apache와 WAF 상태를 확인해줘" -t v-web
```

### 패키지 관리

```bash
python3 apps/cli/opsclaw.py run "시스템 패키지를 업데이트해줘" -t v-secu
python3 apps/cli/opsclaw.py run "nginx를 설치하고 시작해줘" -t v-web
```

### 보안 점검

```bash
python3 apps/cli/opsclaw.py run "TLS 인증서 유효기간을 확인해줘" -t v-web
python3 apps/cli/opsclaw.py run "Wazuh 최근 알림을 분석해줘" -t v-siem
python3 apps/cli/opsclaw.py run "방화벽 규칙을 점검하고 취약점이 있는지 확인해줘" -t v-secu
```

### 로그 분석

```bash
python3 apps/cli/opsclaw.py run "최근 1시간 에러 로그를 분석해줘" -t local
python3 apps/cli/opsclaw.py run "Apache 접근 로그에서 의심스러운 패턴을 찾아줘" -t v-web
```

---

## Mode A vs Mode B 비교 요약

| 항목 | Mode A (Native) | Mode B (Claude Code) |
|------|-----------------|---------------------|
| Master | Ollama LLM (8B~120B) | Claude (대형 모델) |
| 계획 수립 | 자동 (LLM) | 수동 (AI 또는 사용자) |
| 인터페이스 | CLI 한 줄 | curl / Claude Code |
| 판단 정확도 | 보통 | 높음 |
| 동적 워크플로우 | 제한적 | 유연함 |
| 실행 속도 | 빠름 (자동) | 느림 (대화형) |
| 적합한 작업 | 반복/표준 작업 | 복잡/동적 작업 |
| 오프라인 사용 | 가능 (로컬 LLM) | 불가 (인터넷 필요) |

---

## 다음 단계

- **CLI 전체 레퍼런스**: [02-cli-guide.md](02-cli-guide.md)
- **Master Service API 상세**: [03-master-service.md](03-master-service.md)
- **Claude Code 모드로 전환**: [../claude-code-mode/01-overview.md](../claude-code-mode/01-overview.md)
