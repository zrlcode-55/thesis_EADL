from __future__ import annotations

import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from exp_suite import __version__


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def try_git_rev(repo_root: Path) -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(repo_root),
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        return out or None
    except Exception:
        return None


def build_run_manifest(
    *,
    run_id: str,
    config: dict[str, Any],
    seed: int,
    artifacts: dict[str, str],
    checksums: dict[str, str],
    repo_root: Path,
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "created_utc": utc_now_iso(),
        "suite_version": __version__,
        "git_rev": try_git_rev(repo_root),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "seed": seed,
        "config": config,
        "artifacts": artifacts,
        "checksums_sha256": checksums,
    }


