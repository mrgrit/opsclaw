# OldClaw

OldClaw is a **Control‑Plane Orchestration Platform** built on top of the **pi** runtime. This repository currently resides in **M0 – design lock & skeleton** stage. All core data models, service boundaries, registry specifications and API contracts are defined and ready for concrete implementation in the upcoming M1 phase.

## Repository Structure
```
oldclaw/
├─ apps/                # Service entrypoints (FastAPI)
├─ docs/m0/            # M0 설계 문서 (baseline, DB schema, registry spec, etc.)
├─ migrations/         # Flyway‑like SQL migrations (human‑readable)
├─ packages/pi_adapter # Adapter layer between OldClaw and pi runtime
├─ schemas/            # JSON‑Schema contracts for API & registry
├─ seed/               # Initial registry data (Tools, Skills, Playbooks, Policies)
└─ README.md           # This overview
```

## Current Status (M0)
- **Design**: High‑level architecture, data model, and registry boundaries are documented and fixed.
- **Skeleton**: FastAPI entrypoints for Manager API, Master Service, SubAgent Runtime, Scheduler Worker and Watch Worker are present with explicit `501`/`NotImplementedError` stubs.
- **Adapter**: `pi_adapter` package provides clear runtime, session, model‑profile and tool‑bridge interfaces (no real SDK calls yet).
- **Migrations**: SQL files are fully expanded, include PK/FK/CHECK/UNIQUE/INDEX definitions, and reflect the 4‑layer memory model.
- **Contracts**: JSON Schema files for API endpoints and registry objects are pretty‑printed and versioned.

## Next Step (M1)
The next milestone will implement the actual business logic, policy engine, validation pipelines and integrate the real pi SDK. See `docs/m0/oldclaw-m1-next-todo.md` for a detailed task list.

---
*This repository is in M0 completion stage; further development will proceed to M1.*
