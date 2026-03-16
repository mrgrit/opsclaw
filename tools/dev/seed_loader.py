#!/usr/bin/env python3
"""
Seed Loader: load YAML seed files into registry DB.
Usage: PYTHONPATH=. python3 tools/dev/seed_loader.py [--dry-run]
"""
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from packages.registry_service import (
    upsert_playbook,
    upsert_playbook_steps,
    upsert_skill,
    upsert_tool,
)

SEED_ROOT = Path(__file__).resolve().parent.parent.parent / "seed"
DRY_RUN = "--dry-run" in sys.argv


def load_yaml(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def load_tools() -> None:
    print("\n[tools]")
    for p in sorted((SEED_ROOT / "tools").glob("*.yaml")):
        d = load_yaml(p)
        if DRY_RUN:
            print(f"  (dry) {d['name']} v{d['version']}")
            continue
        r = upsert_tool(
            name=d["name"],
            version=d["version"],
            description=d.get("description"),
            runtime_type=d.get("runtime_type"),
            risk_level=d.get("risk_level"),
            policy_tags=d.get("policy_tags"),
            enabled=d.get("enabled", True),
            metadata=d.get("metadata"),
        )
        print(f"  OK  {r['name']} v{r['version']}  id={r['id']}")


def load_skills() -> None:
    print("\n[skills]")
    for p in sorted((SEED_ROOT / "skills").glob("*.yaml")):
        d = load_yaml(p)
        if DRY_RUN:
            print(f"  (dry) {d['name']} v{d['version']}")
            continue
        r = upsert_skill(
            name=d["name"],
            version=d["version"],
            category=d.get("category"),
            description=d.get("description"),
            required_tools=d.get("required_tools", []),
            optional_tools=d.get("optional_tools", []),
            enabled=d.get("enabled", True),
            metadata=d.get("metadata"),
        )
        print(f"  OK  {r['name']} v{r['version']}  id={r['id']}")


def load_playbooks() -> None:
    print("\n[playbooks]")
    for p in sorted((SEED_ROOT / "playbooks").glob("*.yaml")):
        d = load_yaml(p)
        if DRY_RUN:
            print(f"  (dry) {d['name']} v{d['version']}  steps={len(d.get('steps', []))}")
            continue
        pb = upsert_playbook(
            name=d["name"],
            version=d["version"],
            category=d.get("category"),
            description=d.get("description"),
            execution_mode=d.get("execution_mode", "one_shot"),
            default_risk_level=d.get("default_risk_level", "medium"),
            dry_run_supported=d.get("dry_run_supported", False),
            explain_supported=d.get("explain_supported", True),
            enabled=d.get("enabled", True),
            metadata=d.get("metadata"),
        )
        steps_raw = d.get("steps", [])
        if steps_raw:
            upsert_playbook_steps(pb["id"], steps_raw)
        print(f"  OK  {pb['name']} v{pb['version']}  id={pb['id']}  steps={len(steps_raw)}")


def main() -> None:
    print(f"=== OpsClaw Seed Loader {'(DRY RUN)' if DRY_RUN else ''} ===")
    load_tools()
    load_skills()
    load_playbooks()
    print("\n=== Seed loading complete ===")


if __name__ == "__main__":
    main()
