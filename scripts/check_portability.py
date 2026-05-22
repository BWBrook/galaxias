from __future__ import annotations

import csv
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_REGISTER = ROOT / "data" / "source_register.csv"
WINDOWS_RESERVED = re.compile(r"(^|/)(con|prn|aux|nul|com[1-9]|lpt[1-9])(\.|/|$)")
WINDOWS_FORBIDDEN = re.compile(r'[<>:"\\|?*]')
DRIVE_PATH = re.compile(r"^[A-Za-z]:[\\/]")


def git_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
    )
    return [item.decode("utf-8") for item in result.stdout.split(b"\0") if item]


def check_case_collisions(paths: list[str]) -> list[str]:
    seen: dict[str, str] = {}
    problems: list[str] = []
    for path in paths:
        lowered = path.lower()
        if lowered in seen and seen[lowered] != path:
            problems.append(f"case-insensitive path collision: {seen[lowered]} <-> {path}")
        seen[lowered] = path
    return problems


def check_windows_names(paths: list[str]) -> list[str]:
    problems: list[str] = []
    for path in paths:
        if WINDOWS_RESERVED.search(path.lower()):
            problems.append(f"Windows-reserved path component: {path}")
        if WINDOWS_FORBIDDEN.search(path):
            problems.append(f"Windows-forbidden filename character: {path}")
    return problems


def check_text_bytes(paths: list[str]) -> list[str]:
    problems: list[str] = []
    for path in paths:
        data = (ROOT / path).read_bytes()
        if b"\0" in data:
            continue
        if data.startswith(b"\xef\xbb\xbf"):
            problems.append(f"UTF-8 BOM present: {path}")
        if b"\r\n" in data:
            problems.append(f"CRLF line endings present: {path}")
    return problems


def check_source_register() -> list[str]:
    problems: list[str] = []
    with SOURCE_REGISTER.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            source_id = row["source_id"]
            local_path = row["local_path"].strip()
            if not local_path:
                continue
            if local_path.startswith("/") or DRIVE_PATH.match(local_path):
                problems.append(f"{source_id} local_path is absolute: {local_path}")
                continue
            resolved = (ROOT / local_path).resolve()
            try:
                resolved.relative_to(ROOT)
            except ValueError:
                problems.append(f"{source_id} local_path escapes repo: {local_path}")
                continue
            if not resolved.exists():
                problems.append(f"{source_id} local_path does not exist: {local_path}")
    return problems


def main() -> int:
    paths = git_files()
    problems = []
    problems.extend(check_case_collisions(paths))
    problems.extend(check_windows_names(paths))
    problems.extend(check_text_bytes(paths))
    problems.extend(check_source_register())

    if problems:
        print("Portability check failed:", file=sys.stderr)
        for problem in problems:
            print(f"- {problem}", file=sys.stderr)
        return 1

    print(f"Portability check passed: {len(paths)} git-managed files inspected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
