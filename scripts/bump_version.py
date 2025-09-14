#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Automatisches Version-Bumping via Git-Tags und Push zu GitHub.

Nutzung:
  uv run python scripts/bump_version.py [patch|minor|major]

Voraussetzungen:
  - Git-Repository mit Remote "origin"
  - uv-dynamic-versioning nutzt Git-Tags (z. B. v1.2.3)
  - Arbeitsverzeichnis ist sauber (keine uncommitted Änderungen)
"""

import re
import sys
import subprocess
from typing import Tuple


def run(cmd: list[str], check: bool = True) -> Tuple[int, str]:
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
        return 0, out.strip()
    except subprocess.CalledProcessError as e:
        if check:
            print(e.output.strip())
            raise
        return e.returncode, e.output.strip()


def ensure_clean_worktree() -> None:
    code, out = run(["git", "status", "--porcelain"], check=False)
    if code != 0:
        print("Fehler beim Prüfen des Git-Status.")
        sys.exit(1)
    if out.strip():
        print("Arbeitsverzeichnis ist nicht sauber. Bitte committe/stashe deine Änderungen und versuche es erneut.")
        sys.exit(1)


def ensure_origin_remote() -> None:
    code, out = run(["git", "remote"], check=False)
    if code != 0 or "origin" not in out.split():
        print('Kein "origin" Remote gefunden. Bitte richte ein Remote-Repository ein (z. B. GitHub).')
        sys.exit(1)


def get_current_branch() -> str:
    _, branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    return branch


def fetch_tags() -> None:
    run(["git", "fetch", "--tags", "origin"], check=False)


def get_latest_tag() -> str:
    code, out = run(["git", "describe", "--tags", "--abbrev=0"], check=False)
    if code != 0 or not out:
        return "v0.0.0"
    return out.strip()


def parse_version(tag: str) -> Tuple[int, int, int]:
    tag = tag.lstrip("v")
    m = re.match(r"^(\d+)\.(\d+)\.(\d+)$", tag)
    if not m:
        print(f"Ungültiges Tag-Format: {tag}. Erwartet SemVer wie v1.2.3")
        sys.exit(1)
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def bump_version(kind: str, major: int, minor: int, patch: int) -> Tuple[int, int, int]:
    if kind == "major":
        return major + 1, 0, 0
    if kind == "minor":
        return major, minor + 1, 0
    # default patch
    return major, minor, patch + 1


def tag_exists(tag: str) -> bool:
    _, out = run(["git", "tag", "-l", tag])
    return any(line.strip() == tag for line in out.splitlines())


def create_and_push_tag(new_tag: str, branch: str) -> None:
    print(f"Erstelle Tag {new_tag} ...")
    run(["git", "tag", "-a", new_tag, "-m", f"Release {new_tag.lstrip('v')}"])
    print(f"Push Branch {branch} nach origin ...")
    run(["git", "push", "origin", f"{branch}"])
    print(f"Push Tag {new_tag} nach origin ...")
    run(["git", "push", "origin", new_tag])


def main() -> None:
    kind = "patch"
    if len(sys.argv) >= 2:
        arg = sys.argv[1].strip().lower()
        if arg in ("patch", "minor", "major"):
            kind = arg
        else:
            print("Ungültiges Argument. Nutzung: bump_version.py [patch|minor|major]")
            sys.exit(2)

    ensure_origin_remote()
    ensure_clean_worktree()
    fetch_tags()

    latest_tag = get_latest_tag()
    major, minor, patch = parse_version(latest_tag)
    new_major, new_minor, new_patch = bump_version(kind, major, minor, patch)
    new_version = f"{new_major}.{new_minor}.{new_patch}"
    new_tag = f"vnew_version".replace("new_version", new_version)  # robuste String-Ersetzung

    if tag_exists(new_tag):
        print(f"Tag {new_tag} existiert bereits. Abbruch.")
        sys.exit(1)

    branch = get_current_branch()
    print(f"Aktuelles Tag: {latest_tag}  ->  Neues Tag: {new_tag}  auf Branch: {branch}")

    create_and_push_tag(new_tag, branch)
    print("Fertig! uv-dynamic-versioning wird diese Version beim Build übernehmen.")


if __name__ == "__main__":
    main()
