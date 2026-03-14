# OldClaw Registry Specification (M0)

## 1. Tool Specification
Each Tool is an **atomic** capability. Example (run_command):

```yaml
id: run_command
version: 1.0.0
name: run_command
description: Execute a shell command on the assigned runtime.
runtime_type: subagent
risk_level: medium
input_schema_ref: schemas/registry/tools/run_command.input.json
output_schema_ref: schemas/registry/tools/run_command.output.json
policy_tags:
  - command_execution
enabled: true
```

## 2. Skill Specification
Skill composes one or more Tools and adds validation hints.

```yaml
id: collect_web_latency_facts
version: 1.0.0
name: collect_web_latency_facts
category: diagnosis
description: Collect latency‑related facts from web/api/db assets.
supported_modes:
  - one_shot
input_schema_ref: schemas/registry/skills/collect_web_latency_facts.input.json
output_schema_ref: schemas/registry/skills/collect_web_latency_facts.output.json
required_tools:
  - run_command
  - fetch_log
optional_tools:
  - query_metric
default_validation:
  type: fact_completeness
  required_fields:
    - upstream_response_time
    - cpu_usage
    - memory_usage
policy_hint:
  risk_level: low
  approvals: []
evidence_expectations:
  - command_stdout
  - command_exit_code
enabled: true
```

## 3. Playbook Specification
Playbook is an ordered list of steps (skill, validation, report, etc.).

```yaml
id: diagnose_web_latency
version: 1.0.0
name: diagnose_web_latency
category: diagnosis
execution_mode: one_shot
description: Diagnose latency across web/api/db asset chain and produce a validated report.
input_schema_ref: schemas/registry/playbooks/diagnose_web_latency.input.json
output_schema_ref: schemas/registry/playbooks/diagnose_web_latency.output.json
dry_run_supported: true
explain_supported: true
default_risk_level: medium
required_asset_roles:
  - web
  - api
steps:
  - order: 1
    type: skill
    ref: probe_linux_host
    asset_selector: all
  - order: 2
    type: skill
    ref: collect_web_latency_facts
    asset_selector: scoped
  - order: 3
    type: validation
    ref: validate_latency_findings
  - order: 4
    type: report
    ref: generate_latency_report
failure_policy:
  validate_fail: replan
  execution_fail: retry_then_replan
policy_bindings:
  - env: prod
    approval: maybe_required
enabled: true
```

## 4. Registry Enforcement Rules
- **Tool** may only contain primitive actions; never embed full workflows.
- **Skill** must not contain multi‑step procedures; it only orchestrates Tools.
- **Playbook** is the only place where sequential steps are defined.
- Validation, approval gates, and reporting are distinct step types.
- Registry versions are immutable; updates create a new version entry.
