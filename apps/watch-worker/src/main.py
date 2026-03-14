# OldClaw Watch Worker
# Monitors `watch_jobs` and processes events.

import time
from fastapi import FastAPI

app = FastAPI(title="Watch Worker")

@app.get("/health")
async def health_check():
    return {"status": "watch ok"}

def process_watches():
    # TODO: query DB for pending watch jobs and handle events
    print("Processing watch jobs… (placeholder)")

def main():
    while True:
        process_watches()
        time.sleep(30)  # run every 30 seconds

if __name__ == "__main__":
    main()

