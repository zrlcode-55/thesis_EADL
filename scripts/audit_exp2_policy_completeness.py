from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def _expected_point_keys(config_dir: Path, experiment_id: str) -> set[str]:
    keys: set[str] = set()
    for p in config_dir.glob(f"{experiment_id}__*__*.toml"):
        parts = p.stem.split("__")
        if len(parts) < 3:
            continue
        keys.add("__".join(parts[1:-1]))
    return keys


def _safe_slug(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", s).strip("_")


def _extract_point_key_from_sweep_dirname(dirname: str, sweep_prefix: str) -> str | None:
    # dirname example:
    #   sweep_exp2_policy_v1__A__wc_linear__ps0p05
    if not dirname.startswith("sweep_"):
        return None
    sweep_id = dirname[len("sweep_") :]
    pref = f"{sweep_prefix}__"
    if not sweep_id.startswith(pref):
        return None
    return sweep_id[len(pref) :]


def audit_policy_sweeps(
    *,
    artifacts_dir: Path,
    sweep_prefix: str,
    expected_points: set[str],
    expected_seed_count: int,
    expected_policy_count: int,
    sample_limit: int = 25,
) -> dict[str, Any]:
    sweeps = []
    found_points_any: set[str] = set()
    found_points_finalized: set[str] = set()

    for d in sorted(artifacts_dir.iterdir(), key=lambda p: p.name):
        if not d.is_dir() or not d.name.startswith(f"sweep_{sweep_prefix}"):
            continue

        point_key = _extract_point_key_from_sweep_dirname(d.name, sweep_prefix=sweep_prefix)
        if point_key:
            found_points_any.add(point_key)

        sp = d / "sweep_progress.json"
        sm = d / "sweep_manifest.json"
        has_sp = sp.exists()
        has_sm = sm.exists()

        total_expected = expected_seed_count * expected_policy_count
        finalized = False
        if has_sp:
            try:
                j = json.loads(sp.read_text(encoding="utf-8"))
                finalized = (
                    j.get("last_run_id") == "FINALIZED"
                    and int(j.get("total", -1)) == int(total_expected)
                    and int(j.get("completed", -2)) == int(total_expected)
                )
            except Exception:
                finalized = False

        if finalized and point_key:
            found_points_finalized.add(point_key)

        run_dirs = [p for p in d.iterdir() if p.is_dir() and p.name.startswith("sweep_")]
        missing_rm = []
        for rd in run_dirs:
            if not (rd / "run_manifest.json").exists():
                if len(missing_rm) < sample_limit:
                    missing_rm.append(str(rd))

        sweeps.append(
            {
                "sweep_dir": str(d),
                "point_key": point_key,
                "has_sweep_progress": has_sp,
                "has_sweep_manifest": has_sm,
                "finalized": finalized,
                "run_dirs_count": len(run_dirs),
                "runs_missing_run_manifest": len(missing_rm),
                "missing_run_manifest_sample": missing_rm,
            }
        )

    missing_any = sorted(expected_points - found_points_any)
    missing_finalized = sorted(expected_points - found_points_finalized)

    return {
        "sweep_prefix": sweep_prefix,
        "artifacts_dir": str(artifacts_dir),
        "expected_points_count": len(expected_points),
        "expected_runs_per_point": expected_seed_count * expected_policy_count,
        "found_points_any_count": len(found_points_any),
        "found_points_finalized_count": len(found_points_finalized),
        "missing_points_any_count": len(missing_any),
        "missing_points_finalized_count": len(missing_finalized),
        "missing_points_any": missing_any[:100],
        "missing_points_finalized": missing_finalized[:100],
        "sweeps_found": len(sweeps),
        "sweeps": sweeps,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Audit Exp2 policy sweep completeness vs generated config points.")
    ap.add_argument("--config-dir", type=Path, default=Path("configs/locked/exp2_policy_v1"))
    ap.add_argument("--experiment-id", type=str, default="exp2_policy_v1")
    ap.add_argument("--artifacts-dir", type=Path, default=Path(r"C:\exp2_policy_artifacts"))
    ap.add_argument("--sweep-prefix", type=str, required=True)
    ap.add_argument("--expected-seed-count", type=int, default=30)
    ap.add_argument("--expected-policy-count", type=int, default=4)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    expected_points = _expected_point_keys(args.config_dir, experiment_id=args.experiment_id)
    report = audit_policy_sweeps(
        artifacts_dir=args.artifacts_dir,
        sweep_prefix=args.sweep_prefix,
        expected_points=expected_points,
        expected_seed_count=int(args.expected_seed_count),
        expected_policy_count=int(args.expected_policy_count),
    )

    out = args.out or (Path("artifacts") / f"audit_{_safe_slug(args.sweep_prefix)}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(f"sweep_prefix={args.sweep_prefix}")
    print(f"points expected={report['expected_points_count']}")
    print(f"points found (finalized)={report['found_points_finalized_count']}")
    print(f"missing points (finalized)={report['missing_points_finalized_count']}")
    print(f"wrote: {out}")


if __name__ == "__main__":
    main()


