#!/usr/bin/env python3
"""
OpsClaw CTF — 문제 자동 등록 스크립트
CTFd API를 사용하여 YAML 정의 파일에서 문제를 자동 등록합니다.

Usage:
  python3 register_challenges.py --ctfd-url http://localhost:8080 --token <admin-token>
  python3 register_challenges.py --ctfd-url http://localhost:8080 --token <admin-token> --course course1
  python3 register_challenges.py --dry-run  # 등록하지 않고 확인만
"""

import argparse
import glob
import sys
import yaml
import requests


def load_challenges(base_dir: str, course_filter: str = None):
    """YAML 파일에서 문제 목록을 로딩"""
    pattern = f"{base_dir}/challenges/{course_filter or '*'}/*.yaml"
    challenges = []
    for path in sorted(glob.glob(pattern)):
        with open(path) as f:
            data = yaml.safe_load(f)
            data['_file'] = path
            challenges.append(data)
    return challenges


def register_challenge(ctfd_url: str, token: str, challenge: dict) -> dict:
    """CTFd API로 문제를 등록"""
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json",
    }

    # 1. 문제 생성
    payload = {
        "name": challenge["name"],
        "category": challenge.get("category", "misc"),
        "description": challenge.get("description", ""),
        "value": challenge.get("points", 100),
        "state": "visible",
        "type": "standard",
    }

    resp = requests.post(f"{ctfd_url}/api/v1/challenges", json=payload, headers=headers)
    if resp.status_code != 200:
        return {"error": resp.text, "challenge": challenge["name"]}

    chal_id = resp.json()["data"]["id"]

    # 2. FLAG 등록
    flag_payload = {
        "challenge_id": chal_id,
        "content": challenge.get("flag", "FLAG{default}"),
        "type": "static",
    }
    requests.post(f"{ctfd_url}/api/v1/flags", json=flag_payload, headers=headers)

    # 3. 힌트 등록 (있으면)
    for i, hint in enumerate(challenge.get("hints", [])):
        hint_payload = {
            "challenge_id": chal_id,
            "content": hint.get("text", ""),
            "cost": hint.get("cost", 50),
        }
        requests.post(f"{ctfd_url}/api/v1/hints", json=hint_payload, headers=headers)

    return {"ok": True, "id": chal_id, "name": challenge["name"]}


def main():
    parser = argparse.ArgumentParser(description="OpsClaw CTF Challenge Registrar")
    parser.add_argument("--ctfd-url", default="http://localhost:8080")
    parser.add_argument("--token", help="CTFd admin API token")
    parser.add_argument("--course", help="특정 과목만 등록 (예: course1)")
    parser.add_argument("--dry-run", action="store_true", help="등록하지 않고 확인만")
    parser.add_argument("--base-dir", default=".", help="challenges/ 디렉토리 위치")
    args = parser.parse_args()

    challenges = load_challenges(args.base_dir, args.course)
    print(f"Found {len(challenges)} challenges")

    for c in challenges:
        if args.dry_run:
            print(f"  [DRY] {c['name']} ({c.get('category','?')}) {c.get('points',100)}pts — {c['_file']}")
        else:
            if not args.token:
                print("ERROR: --token required for registration")
                sys.exit(1)
            result = register_challenge(args.ctfd_url, args.token, c)
            status = "OK" if result.get("ok") else "FAIL"
            print(f"  [{status}] {c['name']} — {result}")

    print(f"\nTotal: {len(challenges)} challenges {'(dry run)' if args.dry_run else 'registered'}")


if __name__ == "__main__":
    main()
