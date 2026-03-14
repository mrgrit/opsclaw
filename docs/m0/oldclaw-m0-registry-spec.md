# OldClaw M0 Registry Specification

## 개요
`registry` 는 **Tool → Skill → Playbook** 의 3‑계층 메타데이터를 정의한다. 각각은 versioned ID(`name:ver`) 로 식별되며, 입력/출력 스키마와 정책 힌트를 포함한다.

## 경계 정의
| 레이어 | 책임 | 금지사항 |
|--------|------|----------|
| **Tool** | 시스템 명령, API 호출, 파일 I/O 등 저수준 동작 제공 | 비즈니스 로직, 상태 저장, 검증 로직 포함 금지 |
| **Skill** | 하나 이상의 Tool 조합, 입력 검증, 출력 가공, 증거(evidence) 기대 정의 | 외부 서비스와 직접 통신(예: DB 쓰기) 금지, 오직 Tool 호출만 허용 |
| **Playbook** | Skill 시퀀스 정의, 흐름 제어(조건/리트라이), 정책 바인딩 | 직접 Tool 호출, 데이터베이스 직접 조작 금지 |

## 필수 메타데이터 (공통)
- `id` : `name:version` 형식 문자열 (예: `run_command:1.0`)
- `name` : 인간 읽기 가능한 식별자
- `version` : SemVer 문자열
- `description` : 기능 요약
- `input_schema_ref`/`output_schema_ref` : `schemas/registry/...` 경로 참조
- `enabled` : 비활성화시 자동 제외
- `metadata` : 자유 JSON, 확장용

## Tool Spec 예시 (run_command)
```json
{
  "id": "run_command:1.0",
  "name": "run_command",
  "version": "1.0",
  "description": "Execute a shell command on the target host",
  "runtime_type": "local",
  "input_schema_ref": "schemas/registry/tools/run_command.input.json",
  "output_schema_ref": "schemas/registry/tools/run_command.output.json",
  "policy_tags": ["security", "operations"],
  "enabled": true
}
```

## Skill Spec 예시 (collect_web_latency_facts)
```json
{
  "id": "collect_web_latency_facts:1.0",
  "name": "collect_web_latency_facts",
  "version": "1.0",
  "category": "observability",
  "description": "Collect latency metrics for a web endpoint using run_command",
  "required_tools": ["run_command"],
  "input_schema_ref": "schemas/registry/skills/collect_web_latency_facts.input.json",
  "output_schema_ref": "schemas/registry/skills/collect_web_latency_facts.output.json",
  "default_validation": {"type": "object", "required": ["latency_ms"]},
  "evidence_expectations": {"type": "object", "properties": {"latency_ms": {"type": "number"}}},
  "enabled": true
}
```

## Playbook Spec 예시 (diagnose_web_latency)
```json
{
  "id": "diagnose_web_latency:1.0",
  "name": "diagnose_web_latency",
  "version": "1.0",
  "category": "observability",
  "description": "Run a series of skills to diagnose web latency issues",
  "execution_mode": "one_shot",
  "required_asset_roles": ["web_server"],
  "failure_policy": {"type": "enum", "values": ["abort", "continue"]},
  "policy_bindings": [{"policy": "latency_threshold", "params": {"max_ms": 200}}]
}
```

---
*임의 적용*: 실제 스키마 파일 경로와 일부 정책 정의는 추후 M1 단계에서 보강될 수 있습니다.*
