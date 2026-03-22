#!/usr/bin/env python3
"""
M17 부하 테스트 스크립트 — Pi Freeze Bug Fix 검증

시나리오:
  1. 동시 N개 LLM 요청 (freeze 재현/검증)
  2. 결과 요약: 성공/실패/timeout 건수, 총 소요 시간

사용법:
  PYTHONPATH=. .venv/bin/python3 scripts/m17_load_test.py [--concurrency 3] [--rounds 2]

  또는 subagent-runtime API 경유:
  python3 scripts/m17_load_test.py --via-api --url http://localhost:8002
"""
import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# subagent API 경유 테스트
SUBAGENT_URL = "http://localhost:8002"
PROMPTS = [
    "서버의 현재 시간을 출력하라. 한 줄로 답하라.",
    "리눅스 top 명령어의 목적을 한 문장으로 설명하라.",
    "Nginx와 Apache의 차이를 두 줄로 설명하라.",
    "SSH 포트 기본값은 무엇인가? 숫자만 답하라.",
    "UFW 방화벽에서 포트 80을 여는 명령어를 알려달라.",
]


def call_invoke_llm(url: str, prompt: str, idx: int) -> dict:
    import httpx
    t0 = time.time()
    try:
        resp = httpx.post(
            f"{url}/a2a/invoke_llm",
            json={
                "project_id": f"m17-loadtest-{idx}",
                "job_run_id": f"run-{idx}",
                "task": prompt,
            },
            timeout=120.0,
        )
        elapsed = time.time() - t0
        if resp.status_code == 200:
            data = resp.json()
            response_text = data.get("response") or data.get("stdout", "")
            exit_code = data.get("exit_code", -1)
            return {
                "idx": idx,
                "status": "ok" if exit_code == 0 else "error",
                "exit_code": exit_code,
                "elapsed": round(elapsed, 2),
                "preview": response_text[:80].replace("\n", " "),
            }
        return {
            "idx": idx,
            "status": "http_error",
            "http_status": resp.status_code,
            "elapsed": round(elapsed, 2),
            "preview": resp.text[:80],
        }
    except httpx.TimeoutException:
        elapsed = time.time() - t0
        return {"idx": idx, "status": "timeout", "elapsed": round(elapsed, 2), "preview": ""}
    except Exception as exc:
        elapsed = time.time() - t0
        return {"idx": idx, "status": "exception", "elapsed": round(elapsed, 2), "preview": str(exc)[:80]}


def call_direct_ollama(prompt: str, idx: int) -> dict:
    """pi_adapter를 직접 호출 (API 우회)."""
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    # 환경변수 로드
    env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    if os.path.exists(env_file):
        for line in open(env_file):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

    from packages.pi_adapter.runtime.client import PiRuntimeClient, PiRuntimeConfig
    t0 = time.time()
    try:
        client = PiRuntimeClient(PiRuntimeConfig(default_role="subagent"))
        result = client.invoke_model(prompt, {"role": "subagent"})
        elapsed = time.time() - t0
        return {
            "idx": idx,
            "status": "ok",
            "exit_code": result["exit_code"],
            "elapsed": round(elapsed, 2),
            "preview": result.get("stdout", "")[:80].replace("\n", " "),
        }
    except Exception as exc:
        elapsed = time.time() - t0
        return {"idx": idx, "status": "error", "elapsed": round(elapsed, 2), "preview": str(exc)[:80]}


def run_test(concurrency: int, rounds: int, via_api: bool, url: str) -> None:
    print(f"\n{'='*60}")
    print(f"M17 Pi Freeze 부하 테스트")
    print(f"  모드: {'subagent API' if via_api else 'pi_adapter 직접'}")
    print(f"  동시 요청: {concurrency}개 × {rounds}회")
    print(f"{'='*60}\n")

    all_results = []
    for r in range(1, rounds + 1):
        print(f"[Round {r}/{rounds}] 동시 {concurrency}개 요청 시작...")
        jobs = [(PROMPTS[i % len(PROMPTS)], i + (r - 1) * concurrency) for i in range(concurrency)]
        t0 = time.time()
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            if via_api:
                futures = {executor.submit(call_invoke_llm, url, p, idx): idx for p, idx in jobs}
            else:
                futures = {executor.submit(call_direct_ollama, p, idx): idx for p, idx in jobs}
            for f in as_completed(futures):
                result = f.result()
                all_results.append(result)
                icon = "✅" if result["status"] == "ok" else "❌"
                print(f"  {icon} [{result['idx']}] {result['status']} ({result['elapsed']}s) | {result['preview']}")
        round_elapsed = round(time.time() - t0, 2)
        print(f"  → Round {r} 완료: {round_elapsed}s\n")

        if r < rounds:
            time.sleep(2)

    # 요약
    ok = sum(1 for r in all_results if r["status"] == "ok")
    timeout = sum(1 for r in all_results if r["status"] == "timeout")
    error = len(all_results) - ok - timeout
    avg_elapsed = round(sum(r["elapsed"] for r in all_results) / len(all_results), 2)
    max_elapsed = round(max(r["elapsed"] for r in all_results), 2)

    print(f"{'='*60}")
    print(f"결과 요약")
    print(f"  총 요청:  {len(all_results)}개")
    print(f"  성공:     {ok}개")
    print(f"  timeout:  {timeout}개")
    print(f"  오류:     {error}개")
    print(f"  평균 응답: {avg_elapsed}s")
    print(f"  최대 응답: {max_elapsed}s")
    print(f"{'='*60}")

    if timeout == 0 and error == 0:
        print("\n✅ PASS — pi freeze 미발생")
    else:
        print(f"\n❌ FAIL — timeout {timeout}건, error {error}건 발생")

    # JSON 결과 저장
    out = {
        "test_mode": "api" if via_api else "direct",
        "concurrency": concurrency,
        "rounds": rounds,
        "total": len(all_results),
        "ok": ok,
        "timeout": timeout,
        "error": error,
        "avg_elapsed": avg_elapsed,
        "max_elapsed": max_elapsed,
        "results": all_results,
    }
    out_path = os.path.join(os.path.dirname(__file__), "m17_load_test_result.json")
    with open(out_path, "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\n결과 저장: {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="M17 Pi Freeze 부하 테스트")
    parser.add_argument("--concurrency", type=int, default=3, help="동시 요청 수 (기본 3)")
    parser.add_argument("--rounds", type=int, default=2, help="반복 횟수 (기본 2)")
    parser.add_argument("--via-api", action="store_true", help="subagent API 경유 테스트")
    parser.add_argument("--url", default=SUBAGENT_URL, help=f"subagent URL (기본 {SUBAGENT_URL})")
    args = parser.parse_args()
    run_test(args.concurrency, args.rounds, args.via_api, args.url)
