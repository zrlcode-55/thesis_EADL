from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


@dataclass(frozen=True)
class SummaryStats:
    count: int
    mean: float | None
    median: float | None
    std: float | None
    min: float | None
    max: float | None


def _stats(values: list[float]) -> SummaryStats:
    if not values:
        return SummaryStats(count=0, mean=None, median=None, std=None, min=None, max=None)
    arr = np.array(values, dtype=float)
    return SummaryStats(
        count=int(arr.size),
        mean=float(arr.mean()),
        median=float(np.median(arr)),
        std=float(arr.std(ddof=1)) if arr.size >= 2 else 0.0,
        min=float(arr.min()),
        max=float(arr.max()),
    )


def summarize_sweep(sweep_dir: Path, *, metrics_filename: str = "metrics.json") -> dict[str, Any]:
    """Summarize a sweep directory produced by `exp-suite sweep`.

    Reads:
      - sweep_manifest.json
      - each run's metrics.json

    Writes (by the caller):
      - sweep_summary.json

    Returns the summary dict.
    """
    sweep_manifest_path = sweep_dir / "sweep_manifest.json"
    if not sweep_manifest_path.exists():
        raise FileNotFoundError(f"Missing sweep_manifest.json at: {sweep_manifest_path}")

    sweep_manifest = json.loads(sweep_manifest_path.read_text(encoding="utf-8"))
    runs = list(sweep_manifest.get("runs", []))

    included = []
    excluded = []

    # Collect metric values per system per metric name
    per_system: dict[str, dict[str, list[float]]] = {}

    for r in runs:
        system = r.get("system")
        run_id = r.get("run_id")
        metrics_path = r.get("metrics_path")

        if not system or not run_id:
            excluded.append(
                {
                    "run_id": run_id,
                    "reason": "missing required fields in sweep_manifest run entry",
                    "entry": r,
                }
            )
            continue

        # Prefer reading metrics from the run directory (supports versioned recomputation).
        mp = sweep_dir / run_id / metrics_filename
        if not mp.exists() and metrics_path:
            mp = Path(metrics_path)
            if not mp.is_absolute():
                mp = (Path.cwd() / mp).resolve()
        if not mp.exists():
            excluded.append({"run_id": run_id, "system": system, "reason": f"missing metrics.json: {mp}"})
            continue

        m = json.loads(mp.read_text(encoding="utf-8"))
        if m.get("status") != "ok":
            excluded.append({"run_id": run_id, "system": system, "reason": f"metrics status != ok: {m.get('status')}"})
            continue

        metrics = dict(m.get("metrics", {}))
        if not metrics:
            excluded.append({"run_id": run_id, "system": system, "reason": "empty metrics dict"})
            continue

        included.append({"run_id": run_id, "system": system, "seed": r.get("seed")})
        sys_bucket = per_system.setdefault(system, {})

        for k, v in metrics.items():
            # Only summarize numeric metrics.
            try:
                fv = float(v)
            except Exception:
                continue
            sys_bucket.setdefault(k, []).append(fv)

    system_summaries: dict[str, Any] = {}
    for system, metric_map in sorted(per_system.items(), key=lambda x: x[0]):
        system_summaries[system] = {
            "metrics": {name: _stats(vals).__dict__ for name, vals in sorted(metric_map.items(), key=lambda x: x[0])}
        }

    return {
        "sweep_id": sweep_manifest.get("sweep_id"),
        "created_utc": sweep_manifest.get("created_utc"),
        "git_rev": sweep_manifest.get("git_rev"),
        "configs": sweep_manifest.get("configs"),
        "seeds": sweep_manifest.get("seeds"),
        "included_runs": included,
        "excluded_runs": excluded,
        "systems": system_summaries,
    }


