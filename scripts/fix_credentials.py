#!/usr/bin/env python3
"""교안의 잘못된 인증 정보, 사용자명, API 호출을 수정."""
import os
import re

DST = "/home/opsclaw/opsclaw/security_education/course_detail"

REPLACEMENTS = [
    # 잘못된 SSH 사용자명
    ("user@10.20.30.100", "siem@10.20.30.100"),
    ("user@10.20.30.1 ", "secu@10.20.30.1 "),  # 뒤에 공백 포함
    ("user@10.20.30.1\"", "secu@10.20.30.1\""),
    ("user@10.20.30.80", "web@10.20.30.80"),
    ("user@192.168.208.152", "siem@10.20.30.100"),
    ("user@192.168.208.150", "secu@10.20.30.1"),
    ("user@192.168.208.151", "web@10.20.30.80"),
    ("student@10.20.30.80", "web@10.20.30.80"),
    ("student@10.20.30.1", "secu@10.20.30.1"),
    ("student@10.20.30.100", "siem@10.20.30.100"),

    # 잘못된 Wazuh API 인증 (API가 동작하지 않으므로 CLI 안내로 변경)
    # 이건 개별 파일에서 수동 처리

    # 외부 IP → 내부 IP
    ("192.168.208.152", "10.20.30.100"),
    ("192.168.208.150", "10.20.30.1"),
    ("192.168.208.151", "10.20.30.80"),
]

def fix_file(filepath):
    with open(filepath, "r") as f:
        content = f.read()

    original = content
    for old, new in REPLACEMENTS:
        content = content.replace(old, new)

    if content != original:
        with open(filepath, "w") as f:
            f.write(content)
        return True
    return False

def main():
    fixed = 0
    for root, dirs, files in os.walk(DST):
        for f in files:
            if f == "lecture.md":
                fp = os.path.join(root, f)
                if fix_file(fp):
                    fixed += 1
                    rel = fp.replace(DST + "/", "")
                    print(f"  ✓ {rel}")
    print(f"\nFixed: {fixed} files")

if __name__ == "__main__":
    main()
