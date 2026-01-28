from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SweepAudit:
    sweep_dir: str
    sweep_id: str
    point_key: str | None
    has_sweep_manifest: bool
    has_sweep_progress: bool
    runs_dirs_count: int
    runs_manifest_count: int
    runs_missing_run_manifest: int
    runs_missing_metrics: int
    sample_missing_run_manifest: list[str]


def _is_run_dir_name(name: str) -> bool:
    return name.startswith("sweep_")


def _extract_point_key_from_sweep_dirname(dirname: str, sweep_prefix: str) -> str | None:
    # dirname example:
    #   "sweep_exp2_grid_v1__B_r2__cr0p01__sig0p25__cfa10p00__cws0p05"
    if not dirname.startswith("sweep_"):
        return None
    sweep_id = dirname[len("sweep_") :]
    if not sweep_id.startswith(sweep_prefix):
        return None
    i = sweep_id.find("__cr")
    if i < 0:
        i = sweep_id.find("cr")
        if i < 0:
            return None
    point_key = sweep_id[i:].lstrip("_")
    if "__sig" not in point_key or "__cfa" not in point_key or "__cws" not in point_key:
        return None
    return point_key


def _expected_point_keys(config_dir: Path, experiment_id: str) -> set[str]:
    point_keys: set[str] = set()
    for p in config_dir.glob(f"{experiment_id}__*__*.toml"):
        stem = p.stem
        parts = stem.split("__")
        if len(parts) < 3:
            continue
        point_key = "__".join(parts[1:-1])
        if point_key:
            point_keys.add(point_key)
    return point_keys


def _safe_slug(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", s).strip("_")


def audit_sweeps(
    *,
    artifacts_dir: Path,
    sweep_prefix: str,
    expected_points: set[str],
    sample_limit: int = 25,
) -> dict[str, Any]:
    sweeps: list[SweepAudit] = []

    for d in sorted(artifacts_dir.iterdir(), key=lambda p: p.name):
        if not d.is_dir():
            continue
        if not d.name.startswith("sweep_"):
            continue
        if not d.name.startswith(f"sweep_{sweep_prefix}"):
            continue

        sweep_id = d.name[len("sweep_") :]
        point_key = _extract_point_key_from_sweep_dirname(d.name, sweep_prefix=sweep_prefix)

        has_sweep_manifest = (d / "sweep_manifest.json").exists()
        has_sweep_progress = (d / "sweep_progress.json").exists()

        run_dirs = [p for p in d.iterdir() if p.is_dir() and _is_run_dir_name(p.name)]
        runs_dirs_count = len(run_dirs)

        runs_manifest_count = 0
        runs_missing_run_manifest = 0
        runs_missing_metrics = 0
        missing_samples: list[str] = []

        for rd in run_dirs:
            man = rd / "run_manifest.json"
            if man.exists():
                runs_manifest_count += 1
                if not (rd / "metrics.json").exists():
                    runs_missing_metrics += 1
            else:
                runs_missing_run_manifest += 1
                if len(missing_samples) < sample_limit:
                    missing_samples.append(str(rd))

        sweeps.append(
            SweepAudit(
                sweep_dir=str(d),
                sweep_id=sweep_id,
                point_key=point_key,
                has_sweep_manifest=has_sweep_manifest,
                has_sweep_progress=has_sweep_progress,
                runs_dirs_count=runs_dirs_count,
                runs_manifest_count=runs_manifest_count,
                runs_missing_run_manifest=runs_missing_run_manifest,
                runs_missing_metrics=runs_missing_metrics,
                sample_missing_run_manifest=missing_samples,
            )
        )

    found_points_any = {s.point_key for s in sweeps if s.point_key}
    found_points_finalized = {s.point_key for s in sweeps if s.point_key and s.has_sweep_manifest}

    missing_points_any = sorted(expected_points - found_points_any)
    missing_points_finalized = sorted(expected_points - found_points_finalized)

    return {
        "sweep_prefix": sweep_prefix,
        "artifacts_dir": str(artifacts_dir),
        "expected_points_count": len(expected_points),
        "found_points_any_count": len(found_points_any),
        "found_points_finalized_count": len(found_points_finalized),
        "missing_points_any_count": len(missing_points_any),
        "missing_points_finalized_count": len(missing_points_finalized),
        "missing_points_any": missing_points_any[:100],
        "missing_points_finalized": missing_points_finalized[:100],
        "counts": {
            "sweeps_found": len(sweeps),
            "sweeps_missing_manifest": sum(1 for s in sweeps if not s.has_sweep_manifest),
            "sweeps_missing_progress": sum(1 for s in sweeps if not s.has_sweep_progress),
            "runs_dirs_count": sum(s.runs_dirs_count for s in sweeps),
            "runs_manifest_count": sum(s.runs_manifest_count for s in sweeps),
            "runs_missing_run_manifest": sum(s.runs_missing_run_manifest for s in sweeps),
            "runs_missing_metrics": sum(s.runs_missing_metrics for s in sweeps),
        },
        "issues_sample": [
            f"{s.sweep_dir}: missing sweep_manifest.json" for s in sweeps if not s.has_sweep_manifest
        ][:sample_limit],
        "missing_run_manifest_sample": [p for s in sweeps for p in s.sample_missing_run_manifest][:sample_limit],
        "sweeps": [s.__dict__ for s in sweeps],
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Audit Exp2 grid completeness (expected points vs sweep dirs and run manifests).")
    ap.add_argument("--config-dir", type=Path, default=Path("configs/locked/exp2_grid_v1"))
    ap.add_argument("--experiment-id", type=str, default="exp2_grid_v1")
    ap.add_argument("--artifacts-dir", type=Path, default=Path("artifacts/exp2"))
    ap.add_argument(
        "--sweep-prefix",
        type=str,
        required=True,
        help='Sweep id prefix, e.g. "exp2_grid_v1__A" or "exp2_grid_v1__B_r2".',
    )
    ap.add_argument("--out", type=Path, default=None, help="Optional output JSON path (defaults under artifacts/).")
    args = ap.parse_args()

    expected = _expected_point_keys(args.config_dir, experiment_id=args.experiment_id)
    report = audit_sweeps(
        artifacts_dir=args.artifacts_dir,
        sweep_prefix=args.sweep_prefix,
        expected_points=expected,
    )

    out = args.out or (Path("artifacts") / f"audit_{_safe_slug(args.sweep_prefix)}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    c = report["counts"]
    print(f"sweep_prefix={args.sweep_prefix}")
    print(f"artifacts_dir={args.artifacts_dir}")
    print(f"points expected={report['expected_points_count']}")
    print(f"points found (finalized)={report['found_points_finalized_count']}")
    print(f"missing points (finalized)={report['missing_points_finalized_count']}")
    print(
        f"runs dirs={c['runs_dirs_count']} manifests={c['runs_manifest_count']} missing_run_manifest={c['runs_missing_run_manifest']}"
    )
    print(f"wrote: {out}")


if __name__ == "__main__":
    main()


