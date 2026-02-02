"""
Recorded Go/No-Go gate: verify Exp3(identity shock) reduces to Exp2 on the *actual*
Exp2 base-point set, using filesystem artifacts produced by:

  - exp-suite exp2-policy-run
  - exp-suite exp3-shock-run (identity configs)

This produces a JSON report suitable for advisor prereg documentation.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from exp_suite.sweep import summarize_sweep


DEFAULT_POLICIES = ["always_act", "always_wait", "wait_on_conflict", "risk_threshold"]
DEFAULT_METRICS = [
    "M3_avg_cost",
    "M4_p95_cost",
    "M4_p99_cost",
    "M5_deferral_rate",
    "M2_mean_wait_seconds_when_wait",
]


@dataclass(frozen=True)
class Diff:
    metric: str
    policy: str
    exp2: float
    exp3: float
    abs_diff: float
    rel_diff: float


def _read_or_build_summary(sweep_dir: Path) -> dict[str, Any]:
    """Return sweep_summary.json dict (create it if missing)."""
    summary_path = sweep_dir / "sweep_summary.json"
    if summary_path.exists():
        return json.loads(summary_path.read_text(encoding="utf-8"))
    s = summarize_sweep(sweep_dir)
    summary_path.write_text(json.dumps(s, indent=2, sort_keys=True), encoding="utf-8")
    return s


def _mean(summary: dict[str, Any], *, policy: str, metric: str) -> float:
    return float(summary["systems"][policy]["metrics"][metric]["mean"])


def _rel_diff(a: float, b: float) -> float:
    # Symmetric-ish relative diff; safe around zero.
    denom = max(1e-12, abs(a), abs(b))
    return abs(a - b) / denom


def _discover_exp2_sweeps(artifacts_dir: Path, sweep_prefix: str) -> dict[str, Path]:
    """Map base_point_key -> sweep_dir."""
    out: dict[str, Path] = {}
    for d in sorted(artifacts_dir.glob(f"sweep_{sweep_prefix}__*")):
        sid = d.name[len("sweep_") :]
        # sweep_id is: {prefix}__{base_point_key}
        base = sid[len(sweep_prefix) + 2 :]
        out[base] = d
    return out


def _discover_exp3_identity_sweeps(artifacts_dir: Path, sweep_prefix: str) -> dict[str, Path]:
    """Map base_point_key -> sweep_dir for identity shock only."""
    out: dict[str, Path] = {}
    for d in sorted(artifacts_dir.glob(f"sweep_{sweep_prefix}__*")):
        sid = d.name[len("sweep_") :]
        point_key = sid[len(sweep_prefix) + 2 :]
        marker = "__shock_identity__"
        if marker not in point_key:
            continue
        base = point_key.split(marker, 1)[0]
        out[base] = d
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exp2-artifacts-dir", type=Path, required=True)
    ap.add_argument("--exp2-sweep-prefix", type=str, required=True)
    ap.add_argument("--exp3-artifacts-dir", type=Path, required=True)
    ap.add_argument("--exp3-sweep-prefix", type=str, required=True)
    ap.add_argument("--abs-tol", type=float, default=1e-9)
    ap.add_argument("--rel-tol", type=float, default=0.0)
    ap.add_argument("--policy", action="append", default=None, help="Repeat to override default policies.")
    ap.add_argument("--metric", action="append", default=None, help="Repeat to override default metrics.")
    ap.add_argument("--out-json", type=Path, default=Path("artifacts/exp3_identity_reduction_gate.json"))
    args = ap.parse_args()

    policies = args.policy or list(DEFAULT_POLICIES)
    metrics = args.metric or list(DEFAULT_METRICS)

    exp2_map = _discover_exp2_sweeps(args.exp2_artifacts_dir, args.exp2_sweep_prefix)
    exp3_map = _discover_exp3_identity_sweeps(args.exp3_artifacts_dir, args.exp3_sweep_prefix)

    bases = sorted(set(exp2_map.keys()) & set(exp3_map.keys()))
    missing_exp2 = sorted(set(exp3_map.keys()) - set(exp2_map.keys()))
    missing_exp3 = sorted(set(exp2_map.keys()) - set(exp3_map.keys()))

    failures: list[dict[str, Any]] = []
    worst: Diff | None = None

    for base in bases:
        s2 = _read_or_build_summary(exp2_map[base])
        s3 = _read_or_build_summary(exp3_map[base])

        for pol in policies:
            for m in metrics:
                try:
                    v2 = _mean(s2, policy=pol, metric=m)
                    v3 = _mean(s3, policy=pol, metric=m)
                except Exception as e:
                    failures.append(
                        {
                            "base_point": base,
                            "policy": pol,
                            "metric": m,
                            "reason": f"missing metric/policy in sweep_summary: {e}",
                        }
                    )
                    continue

                abs_d = abs(v3 - v2)
                rel_d = _rel_diff(v3, v2)
                if (abs_d > float(args.abs_tol)) and (rel_d > float(args.rel_tol)):
                    failures.append(
                        {
                            "base_point": base,
                            "policy": pol,
                            "metric": m,
                            "exp2_mean": v2,
                            "exp3_mean": v3,
                            "abs_diff": abs_d,
                            "rel_diff": rel_d,
                            "abs_tol": float(args.abs_tol),
                            "rel_tol": float(args.rel_tol),
                        }
                    )

                d = Diff(metric=m, policy=pol, exp2=v2, exp3=v3, abs_diff=abs_d, rel_diff=rel_d)
                if worst is None or d.abs_diff > worst.abs_diff:
                    worst = d

    report: dict[str, Any] = {
        "gate": "exp3_identity_reduction_vs_exp2",
        "exp2": {"artifacts_dir": str(args.exp2_artifacts_dir), "sweep_prefix": args.exp2_sweep_prefix},
        "exp3": {"artifacts_dir": str(args.exp3_artifacts_dir), "sweep_prefix": args.exp3_sweep_prefix},
        "policies": policies,
        "metrics_compared": metrics,
        "tolerances": {"abs": float(args.abs_tol), "rel": float(args.rel_tol)},
        "base_points_compared": bases,
        "missing_base_points": {"exp2_only": missing_exp3, "exp3_only": missing_exp2},
        "worst_diff": None
        if worst is None
        else {
            "policy": worst.policy,
            "metric": worst.metric,
            "exp2_mean": worst.exp2,
            "exp3_mean": worst.exp3,
            "abs_diff": worst.abs_diff,
            "rel_diff": worst.rel_diff,
        },
        "failures": failures,
        "passed": (len(failures) == 0) and (len(missing_exp2) == 0) and (len(missing_exp3) == 0),
    }

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    # CLI-friendly summary
    if report["passed"]:
        print(f"OK: identity reduction gate passed. wrote: {args.out_json}")
        return 0
    print(f"FAIL: identity reduction gate failed. wrote: {args.out_json}")
    print(f"missing exp2 points: {len(missing_exp3)}; missing exp3 points: {len(missing_exp2)}; failures: {len(failures)}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())


