#!/usr/bin/env python3
"""Update the repository and sync Python dependencies when needed.

Usage:
    python3 <repo_checkout>/skills/ppt-master/scripts/update_repo.py
    python3 <repo_checkout>/skills/ppt-master/scripts/update_repo.py --skip-python-sync
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from runtime_support import REPO_ROOT, SKILL_PYPROJECT_FILE, SKILL_UV_LOCK_FILE

TOOLS_DIR = Path(__file__).resolve().parent
SKILL_DIR = TOOLS_DIR.parent
ROOT_PYPROJECT_FILE = REPO_ROOT / "pyproject.toml" if REPO_ROOT else None
ROOT_UV_LOCK_FILE = REPO_ROOT / "uv.lock" if REPO_ROOT else None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Pull the latest repository changes and sync Python dependencies "
            "only when dependency metadata changes."
        )
    )
    parser.add_argument(
        "--skip-python-sync",
        action="store_true",
        help="Skip Python dependency sync even if dependency files changed.",
    )
    return parser.parse_args()


def run_command(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    if REPO_ROOT is None:
        raise RuntimeError(
            "This command only works inside a ppt-master repository checkout. "
            "For a globally installed skill, reinstall or update the source repository instead."
        )
    return subprocess.run(
        args,
        cwd=REPO_ROOT,
        check=check,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def file_digest(path: Path) -> str | None:
    if not path.exists():
        return None

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_git_available() -> None:
    if shutil.which("git") is None:
        raise RuntimeError("Missing executable: git")


def ensure_clean_tracked_worktree() -> None:
    status = run_command(["git", "status", "--porcelain", "--untracked-files=no"], check=False)
    if status.returncode != 0:
        details = (status.stderr or status.stdout or "").strip()
        raise RuntimeError(details or "Unable to inspect git status.")

    if status.stdout.strip():
        raise RuntimeError(
            "Tracked local changes detected. Please commit or stash them before running the update command."
        )


def get_head_revision() -> str:
    result = run_command(["git", "rev-parse", "HEAD"])
    return result.stdout.strip()


def sync_project_dependencies(project_dir: Path, label: str) -> None:
    if shutil.which("uv") is None:
        raise RuntimeError("Missing executable: uv")

    print(f"Dependency files changed. Syncing Python dependencies for {label} with uv...")
    result = run_command(["uv", "sync", "--project", str(project_dir)])

    if result.stdout.strip():
        print(result.stdout.strip())
    if result.stderr.strip():
        print(result.stderr.strip())


def main() -> int:
    args = parse_args()

    try:
        ensure_git_available()
        ensure_clean_tracked_worktree()

        before_head = get_head_revision()
        before_dependency_state = {
            "root_pyproject": file_digest(ROOT_PYPROJECT_FILE) if ROOT_PYPROJECT_FILE else None,
            "root_uv_lock": file_digest(ROOT_UV_LOCK_FILE) if ROOT_UV_LOCK_FILE else None,
            "skill_pyproject": file_digest(SKILL_PYPROJECT_FILE),
            "skill_uv_lock": file_digest(SKILL_UV_LOCK_FILE),
        }

        print(f"Repository: {REPO_ROOT}")
        pull_result = run_command(["git", "pull", "--ff-only"])
        if pull_result.stdout.strip():
            print(pull_result.stdout.strip())
        if pull_result.stderr.strip():
            print(pull_result.stderr.strip())

        after_head = get_head_revision()
        after_dependency_state = {
            "root_pyproject": file_digest(ROOT_PYPROJECT_FILE) if ROOT_PYPROJECT_FILE else None,
            "root_uv_lock": file_digest(ROOT_UV_LOCK_FILE) if ROOT_UV_LOCK_FILE else None,
            "skill_pyproject": file_digest(SKILL_PYPROJECT_FILE),
            "skill_uv_lock": file_digest(SKILL_UV_LOCK_FILE),
        }

        if before_head == after_head:
            print("Repository is already up to date.")
        else:
            print(f"Updated from {before_head[:7]} to {after_head[:7]}.")

        if args.skip_python_sync:
            print("Skipped Python dependency sync.")
        else:
            synced_any = False
            root_changed = (
                before_dependency_state["root_pyproject"] != after_dependency_state["root_pyproject"]
                or before_dependency_state["root_uv_lock"] != after_dependency_state["root_uv_lock"]
            )
            skill_changed = (
                before_dependency_state["skill_pyproject"] != after_dependency_state["skill_pyproject"]
                or before_dependency_state["skill_uv_lock"] != after_dependency_state["skill_uv_lock"]
            )

            if root_changed and ROOT_PYPROJECT_FILE is not None and ROOT_PYPROJECT_FILE.exists():
                sync_project_dependencies(REPO_ROOT, "repo root")
                synced_any = True

            if skill_changed and SKILL_PYPROJECT_FILE.exists():
                sync_project_dependencies(SKILL_DIR, "skills/ppt-master")
                synced_any = True

            if not synced_any:
                print("Dependency files unchanged. Skipping Python dependency sync.")

        print("Note: system dependencies such as Node.js and Pandoc still need to be installed manually.")
        return 0
    except subprocess.CalledProcessError as exc:
        details = (exc.stderr or exc.stdout or "").strip()
        print(details or "Command failed.", file=sys.stderr)
        return exc.returncode or 1
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
