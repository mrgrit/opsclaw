# subagent runtime placeholder

import subprocess
import sys

def run_command(cmd: str, timeout: int = 60):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        print("STDOUT:\n", result.stdout)
        print("STDERR:\n", result.stderr, file=sys.stderr)
        print("EXIT CODE:", result.returncode)
    except subprocess.TimeoutExpired as e:
        print("Command timed out", file=sys.stderr)
        sys.exit(124)

if __name__ == "__main__":
    # Simple demo runner – real SubAgent will receive A2A messages.
    if len(sys.argv) > 1:
        run_command(" ".join(sys.argv[1:]))
    else:
        print("Usage: python main.py <command>")
