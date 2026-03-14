# OldClaw Repository & Service Structure (M0)

## Repository Layout
```
oldclaw/
├─ README.md
├─ LICENSE
├─ .env.example
├─ pyproject.toml
├─ Makefile
├─ docker/
│  ├─ manager.Dockerfile
│  ├─ subagent.Dockerfile
│  └─ postgres-compose.yaml
├─ deploy/
│  └─ (deployment scripts – placeholder)
├─ docs/
│  └─ m0/ (design docs)
├─ schemas/
│  ├─ api/
│  └─ registry/
├─ migrations/
├─ seed/
├─ tests/
├─ tools/
├─ apps/
│  ├─ manager-api/
│  ├─ master-service/
│  └─ subagent-runtime/
└─ packages/
   ├─ pi_adapter/
   ├─ core/
   ├─ asset_registry/
   ├─ project_service/
   ├─ registry_service/
   ├─ evidence_service/
   ├─ validation_service/
   ├─ history_service/
   ├─ experience_service/
   ├─ retrieval_service/
   ├─ policy_engine/
   ├─ approval_engine/
   ├─ a2a_protocol/
   └─ shared/
```

## Service Boundaries
- **Manager API** (`apps/manager-api`): Human/REST entry point, project & asset orchestration.
- **Master Service** (`apps/master-service`): High‑cost planning, re‑planning, final review.
- **SubAgent Runtime** (`apps/subagent-runtime`): Local command execution, evidence capture.
- **pi_adapter** (`packages/pi_adapter`): Thin wrapper translating OldClaw calls to pi runtime.

Each service lives in its own `src/` package and can be containerised independently.
