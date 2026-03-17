# OpsClaw Watch Worker
# Monitors `watch_jobs` and processes events.

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from packages.watch_service import list_watch_jobs, run_watch_check
from fastapi import FastAPI

app = FastAPI(title="Watch Worker")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://opsclaw:opsclaw@127.0.0.1:5432/opsclaw")


@app.get("/health")
async def health_check():
    return {"status": "watch ok"}


def load_watch_jobs() -> list[dict]:
    return list_watch_jobs(status="running", database_url=DATABASE_URL)


def process_watch_job(job: dict) -> dict:
    return run_watch_check(job, database_url=DATABASE_URL)


def run_loop(poll_interval: int = 30):
    while True:
        try:
            jobs = load_watch_jobs()
            for j in jobs:
                result = process_watch_job(j)
                print(f"[watch] checked {j['id']}: ok={result['ok']}")
        except Exception as e:
            print(f"[watch] error: {e}")
        time.sleep(poll_interval)


if __name__ == "__main__":
    run_loop()
