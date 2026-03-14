# OldClaw

OldClaw is a **Control‑Plane Orchestration Platform** built on top of the **pi** runtime. This repository currently resides in **M0 – design lock \u0026 skeleton** stage. All core data models, service boundaries, registry specifications and API contracts are defined and ready for concrete implementation in the upcoming M1 phase.

## Repository Structure
```
oldclaw/
├─ apps/                # Service entrypoints (FastAPI)
├─ docs/m0/            # M0 설계 문서 (baseline, DB schema, registry spec, etc.)
├─ migrations/         # Flyway‑like SQL migrations (human‑readable)
├─ packages/pi_adapter # pi runtime 과의 어댑터 계층 (runtime, tools, sessions …)
├─ schemas/            # JSON‑Schema 기반 API 계약 및 Registry 스키마
├─ seed/               # 초기 registry 데이터 (Tool, Skill, Playbook, Policy)
└─ README.md           # This overview
```

## Current Stage
**M0 – design lock \u0026 skeleton**: The architecture, data model, registry boundaries, and service contracts are fixed. The codebase contains only skeletal FastAPI entrypoints with explicit `501`/`NotImplementedError` stubs, and the `pi_adapter` provides only the integration boundary.

## Next Stage (M1)
- Implement the **pi runtime adapter** (session handling, model invocation)
- Build the **policy engine**, validation pipelines, and concrete business logic in services
- Populate the database, add indexes, and flesh out the scheduler and watch workers.

---
*This repository is in M0 completion stage; further development will proceed to M1.*
