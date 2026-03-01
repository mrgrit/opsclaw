from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from .models import TaskRequest
from .orchestrator import ManagerOrchestrator


def main() -> None:
    parser = argparse.ArgumentParser(description="Run OpsClaw MVP orchestrator")
    parser.add_argument("--task-id", default="demo-1")
    parser.add_argument("--objective", required=True)
    parser.add_argument("--requires-master", action="store_true")
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Run dependency bootstrap step (python3 -m pip ...) before task dispatch",
    )
    args = parser.parse_args()

    orchestrator = ManagerOrchestrator()
    result = orchestrator.run(
        TaskRequest(
            task_id=args.task_id,
            objective=args.objective,
            requires_master=args.requires_master,
            install_dependencies=args.install_deps,
        )
    )
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
