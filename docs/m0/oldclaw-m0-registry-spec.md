# Registry Specification (M0)

The registry is the **single source of truth** for all executable primitives in OldClaw. It defines three hierarchical layers – **Tool**, **Skill**, and **Playbook** – each with strict boundaries to guarantee composability, auditability, and policy enforcement.

## 1. 개념 정의
- **Tool** – 가장 낮은 수준의 시스템/SDK 호출. 반드시 **단일 원자 동작**만 수행한다. 예: `run_command`, `read_file`, `fetch_log`.
- **Skill** – 하나 이상의 Tool을 조합하고 입력을 검증하며 **Evidence** 를 생성한다. 비즈니스 로직은 허용되지 않으며, 결과는 반드시 `evidence_expectations` 에 정의된 형식이어야 한다.
- **Playbook** – Skill을 순차·조건부로 연결하고, 흐름 제어(조건, 리트라이, 실패 정책)와 정책 바인딩을 정의한다. Tool을 직접 호출하는 것은 금지된다.

## 2. 경계 및 금지사항
| 레이어 | 허용 행동 | 금지 행동 |
|--------|----------|-----------|
| **Tool** | 시스템 명령, 파일 I/O, 외부 API 호출 (단일 요청) | DB 쓰기, 복합 트랜잭션, 비즈니스 의사결정 |
| **Skill** | Tool 호출, 입력 검증, 증거 메타데이터 기록 | 직접 DB 조작, 외부 서비스와 직접 통신 (Tool을 통해서만) |
| **Playbook** | Skill 순서 정의, 조건/리트라이, 정책 바인딩 | Tool 직접 호출, 비정형 상태 유지 |

## 3. 메타데이터 필수 항목 (공통)
- `id` : `<name>:<semver>` (예: `run_command:1.0`)
- `name` : 사람 친화적 식별자
- `version` : SemVer 문자열
- `description` : 기능 요약
- `input_schema_ref` / `output_schema_ref` – `schemas/registry/*` 에 위치한 JSON‑Schema 경로
- `enabled` : 비활성화 시 자동 제외
- `metadata` : 자유 JSON, 확장용

### Tool 전용
- `runtime_type` : `local` | `remote` (예: pi‑model) 
- `policy_tags` : 정책 엔진이 활용할 태그 리스트 (예: `security`, `operations`)

### Skill 전용
- `required_tools` : 최소 의존 Tool 리스트 (예: `["run_command"]`)
- `optional_tools` : 선택적 Tool 리스트
- `default_validation` : 입력 검증 스키마 (JSON‑Schema 혹은 OpenAPI 조각)
- `evidence_expectations` : 생성될 Evidence 의 구조와 필수 필드

### Playbook 전용
- `required_asset_roles` : Playbook 실행에 필요한 Asset 역할 리스트
- `execution_mode` : `one_shot` | `batch` | `continuous`
- `failure_policy` : `abort` | `continue` | 커스텀 재시도 정책
- `policy_bindings` : 적용할 정책/제한 목록 및 파라미터

## 4. 설계 결정 (M0 고정)
- **Tool** 은 `runtime_type` 으로 로컬(서버 내부) 혹은 원격(pi) 실행을 구분한다.
- **Skill** 은 최소 `required_tools` 로 의존성을 선언하고, `optional_tools` 로 유연성을 제공한다. 모든 Skill 은 입력/출력을 **JSON** 형태로 표준화한다.
- **Playbook** 은 `execution_mode` 로 실행 형태를 지정하고, `failure_policy` 로 오류 시 동작을 명시한다. 정책 바인딩은 `policy_bindings` 에 JSON 객체 형태로 기술한다.

## 5. M1 로 넘기는 항목
- **Tool** 의 `policy_tags` 구체화 및 정책 엔진 연동 구현
- **Skill** 의 `validation_hint` 상세 구현 및 자동 테스트
- **Playbook** 의 `policy_bindings` 복합 정책 표현 및 동적 적용 로직

---
*임의 적용*: 일부 필드(예: `policy_tags`) 는 현재 placeholder이며, M1 에서 구체화 예정.*
