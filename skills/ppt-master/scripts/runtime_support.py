#!/usr/bin/env python3
"""Runtime helpers for repository and globally installed PPT Master skills."""

from __future__ import annotations

import importlib.util
import os
import shutil
import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parent
SKILL_DIR = TOOLS_DIR.parent
BOOTSTRAP_ENV_VAR = "PPT_MASTER_UV_BOOTSTRAPPED"
SKILL_PYPROJECT_FILE = SKILL_DIR / "pyproject.toml"
SKILL_UV_LOCK_FILE = SKILL_DIR / "uv.lock"


def detect_repo_root() -> Path | None:
    """Return the checkout root when the skill lives inside the repository."""
    for candidate in (SKILL_DIR.parent.parent, *SKILL_DIR.parents):
        skill_file = candidate / "skills" / "ppt-master" / "SKILL.md"
        if skill_file.exists() and (candidate / "pyproject.toml").exists():
            return candidate
    return None


REPO_ROOT = detect_repo_root()


def skill_project_file() -> Path | None:
    """Return the skill-local pyproject when available."""
    if SKILL_PYPROJECT_FILE.exists():
        return SKILL_PYPROJECT_FILE
    return None


def find_env_file(start_dir: Path | None = None, max_levels: int = 6) -> Path | None:
    """Find the nearest `.env` by walking upward from the current workspace."""
    env_override = os.environ.get("PPT_MASTER_ENV_FILE", "").strip()
    if env_override:
        candidate = Path(env_override).expanduser()
        return candidate if candidate.exists() else None

    current = (start_dir or Path.cwd()).resolve()
    searched: list[Path] = []

    for _ in range(max_levels + 1):
        candidate = current / ".env"
        searched.append(candidate)
        if candidate.exists():
            return candidate
        if current.parent == current:
            break
        current = current.parent

    for candidate in (
        (REPO_ROOT / ".env") if REPO_ROOT else None,
        SKILL_DIR / ".env",
    ):
        if candidate is not None and candidate not in searched and candidate.exists():
            return candidate

    return None


def _missing_modules(module_names: tuple[str, ...]) -> list[str]:
    missing: list[str] = []
    for module_name in module_names:
        if importlib.util.find_spec(module_name) is None:
            missing.append(module_name)
    return missing


def ensure_uv_runtime(*module_names: str) -> None:
    """Re-exec under the skill-local uv project when required packages are missing."""
    if os.environ.get(BOOTSTRAP_ENV_VAR) == "1":
        return

    missing = _missing_modules(module_names) if module_names else ["__all__"]
    if not missing:
        return

    if shutil.which("uv") is None:
        project_file = skill_project_file()
        package_hint = ", ".join(module_names) if module_names else "the skill runtime dependencies"
        source_hint = str(project_file or SKILL_DIR)
        raise RuntimeError(
            "Missing Python dependencies for PPT Master "
            f"({package_hint}). Install `uv` or install the dependencies declared in {source_hint} manually."
        )

    script_path = Path(sys.argv[0]).resolve()
    env = os.environ.copy()
    env[BOOTSTRAP_ENV_VAR] = "1"
    project_file = skill_project_file()
    if project_file is not None:
        env["PPT_MASTER_RUNTIME_SOURCE"] = "pyproject"
        os.execvpe(
            "uv",
            [
                "uv",
                "run",
                "--project",
                str(SKILL_DIR),
                "python",
                str(script_path),
                *sys.argv[1:],
            ],
            env,
        )

    raise RuntimeError(
        "Missing Python dependencies for PPT Master and no skill-local dependency metadata was found. "
        "Expected skills/ppt-master/pyproject.toml."
    )
