# OpsClaw Scheduler Worker
# Periodically checks `schedules` table and enqueues job runs.

import time
from fastapi import FastAPI

app = FastAPI(title="Scheduler Worker")

@app.get("/health")
async def health_check():
    return {"status": "scheduler ok"}

def load_schedules():
    """Load due schedules from the database.

    Returns a list of schedule dicts. Placeholder raises NotImplementedError in M0.
    """
    raise NotImplementedError("load_schedules not implemented in M0 – DB integration pending")

def process_schedule(schedule: dict):
    """Process a single schedule and enqueue a JobRun.

    Placeholder implementation – real logic added in M1.
    """
    raise NotImplementedError("process_schedule not implemented in M0 – job creation pending")

def run_loop(poll_interval: int = 60):
    """Main scheduler loop – loads schedules and processes them.
    """
    while True:
        try:
            schedules = load_schedules()
            for sch in schedules:
                process_schedule(sch)
        except NotImplementedError:
            print("Scheduler placeholder executed – no DB integration.")
            break
        time.sleep(poll_interval)

if __name__ == "__main__":
    run_loop()

