# OpsClaw Scheduler Worker
# Periodically checks `schedules` table and enqueues job runs.

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from packages.scheduler_service import get_due_schedules, execute_due_schedule
from fastapi import FastAPI

app = FastAPI(title="Scheduler Worker")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://opsclaw:opsclaw@127.0.0.1:5432/opsclaw")


@app.get("/health")
async def health_check():
    return {"status": "scheduler ok"}


def load_schedules() -> list[dict]:
    return get_due_schedules(database_url=DATABASE_URL)


def process_schedule(schedule: dict) -> dict:
    return execute_due_schedule(schedule, database_url=DATABASE_URL)


def run_loop(poll_interval: int = 60):
    while True:
        try:
            schedules = load_schedules()
            for sch in schedules:
                result = process_schedule(sch)
                print(f"[scheduler] processed {sch['id']}: {result}")
        except Exception as e:
            print(f"[scheduler] error: {e}")
        time.sleep(poll_interval)


if __name__ == "__main__":
    run_loop()
