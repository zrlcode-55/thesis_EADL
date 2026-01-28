from __future__ import annotations

import argparse
import json
import math
import statistics
from pathlib import Path
from typing import Any


PRIMARY_METRIC = "M3_avg_cost"  # lower is better
DEFAULT_POLICIES = ["always_act", "always_wait", "wait_on_conflict", "risk_threshold"]


def _load_json(p: Path) -> dict[str, Any]:
    return json.loads(p.read_text(encoding="utf-8"))


def _extract_point_key(sweep_id: str, sweep_prefix: str) -> str | None:
    pref = f"{sweep_prefix}__"
    if not sweep_id.startswith(pref):
        return None
    return sweep_id[len(pref) :]


def _iter_sweep_dirs(artifacts_dir: Path, sweep_prefix: str) -> list[Path]:
    return sorted([d for d in artifacts_dir.glob(f"sweep_{sweep_prefix}*") if d.is_dir()], key=lambda p: p.name)


def _mean(x: list[float]) -> float | None:
    if not x:
        return None
    return float(statistics.fmean(x))


def _pearson(x: list[float], y: list[float]) -> float | None:
    if len(x) != len(y) or len(x) < 2:
        return None
    mx = statistics.fmean(x)
    my = statistics.fmean(y)
    num = sum((a - mx) * (b - my) for a, b in zip(x, y))
    denx = sum((a - mx) ** 2 for a in x)
    deny = sum((b - my) ** 2 for b in y)
    den = math.sqrt(denx * deny)
    if den == 0:
        return None
    return float(num / den)


def _policy_metric_mean_from_sweep_summary(summary: dict[str, Any], policy: str, metric: str) -> float | None:
    try:
        return float(summary["systems"][policy]["metrics"][metric]["mean"])
    except Exception:
        return None


def _policy_metric_ci_from_sweep_summary(summary: dict[str, Any], policy: str, metric: str) -> tuple[float | None, float | None]:
    try:
        lo = summary["systems"][policy]["metrics"][metric]["ci_low"]
        hi = summary["systems"][policy]["metrics"][metric]["ci_high"]
        return (None if lo is None else float(lo), None if hi is None else float(hi))
    except Exception:
        return (None, None)


def collect_seedset(
    *,
    artifacts_dir: Path,
    sweep_prefix: str,
    policies: list[str],
) -> dict[str, Any]:
    points: dict[str, dict[str, Any]] = {}
    included = 0

    for sweep_dir in _iter_sweep_dirs(artifacts_dir, sweep_prefix):
        sm_path = sweep_dir / "sweep_manifest.json"
        if not sm_path.exists():
            continue
        sp_path = sweep_dir / "sweep_progress.json"
        if not sp_path.exists():
            continue
        try:
            sp = _load_json(sp_path)
        except Exception:
            continue
        if sp.get("last_run_id") != "FINALIZED":
            continue

        ss_path = sweep_dir / "sweep_summary.json"
        if not ss_path.exists():
            # summary is cheap to generate but we keep the script pure-file; run exp-suite summarize-sweep separately
            continue
        summary = _load_json(ss_path)
        sid = str(summary.get("sweep_id") or "")
        pk = _extract_point_key(sid, sweep_prefix)
        if not pk:
            continue

        row = {"sweep_dir": str(sweep_dir), "sweep_id": sid, "policies": {}}
        ok = True
        for pol in policies:
            m = _policy_metric_mean_from_sweep_summary(summary, pol, PRIMARY_METRIC)
            if m is None:
                ok = False
                break
            lo, hi = _policy_metric_ci_from_sweep_summary(summary, pol, PRIMARY_METRIC)
            row["policies"][pol] = {"mean": m, "ci_low": lo, "ci_high": hi}
        if not ok:
            continue

        # Winner (lowest mean)
        best_pol = min(policies, key=lambda p: float(row["policies"][p]["mean"]))
        row["winner"] = best_pol
        points[pk] = row
        included += 1

    # Win counts
    win_counts = {p: 0 for p in policies}
    for pk, r in points.items():
        win_counts[str(r.get("winner"))] = win_counts.get(str(r.get("winner")), 0) + 1

    # Per-policy deltas vs always_act (if present)
    deltas_vs_act = {p: {} for p in policies}
    if "always_act" in policies:
        for pk, r in points.items():
            base = float(r["policies"]["always_act"]["mean"])
            for pol in policies:
                deltas_vs_act[pol][pk] = float(r["policies"][pol]["mean"]) - base

    return {
        "artifacts_dir": str(artifacts_dir),
        "sweep_prefix": sweep_prefix,
        "policies": policies,
        "points": points,
        "points_count": len(points),
        "win_counts": win_counts,
        "deltas_vs_always_act_by_policy": deltas_vs_act,
    }


def render_md(a: dict[str, Any], b: dict[str, Any]) -> str:
    policies = a["policies"]
    common_points = sorted(set(a["points"].keys()) & set(b["points"].keys()))

    # Holdout stability per-policy (delta vs always_act across points)
    corrs = {}
    for pol in policies:
        if pol == "always_act":
            continue
        xa = a["deltas_vs_always_act_by_policy"].get(pol, {})
        xb = b["deltas_vs_always_act_by_policy"].get(pol, {})
        keys = sorted(set(xa.keys()) & set(xb.keys()))
        x = [float(xa[k]) for k in keys]
        y = [float(xb[k]) for k in keys]
        corrs[pol] = {"n_points": len(keys), "pearson": _pearson(x, y)}

    lines: list[str] = []
    lines.append("### Experiment 2 — Policy Sweep Summary (THESIS: fixed semantics, policy varies)")
    lines.append("")
    lines.append("This report summarizes **Exp2 Policy v1** sweeps (fixed state semantics; policy varies) from sweep summaries.")
    lines.append("")
    lines.append("## Inputs (artifact anchors)")
    lines.append(f"- Seed Set A artifacts: `{a['artifacts_dir']}` (prefix `{a['sweep_prefix']}`)")
    lines.append(f"- Holdout Seed Set B artifacts: `{b['artifacts_dir']}` (prefix `{b['sweep_prefix']}`)")
    lines.append("")
    lines.append("## Primary outcome")
    lines.append(f"- **Primary metric**: `{PRIMARY_METRIC}` (lower is better)")
    lines.append(f"- **Policies**: {', '.join(f'`{p}`' for p in policies)}")
    lines.append("")
    lines.append("## Completeness")
    lines.append(f"- **Seed Set A points included**: **{a['points_count']}**")
    lines.append(f"- **Seed Set B points included**: **{b['points_count']}**")
    lines.append(f"- **Common points (A∩B)**: **{len(common_points)}**")
    lines.append("")
    lines.append("## Win counts (per-point winner by mean cost)")
    lines.append("### Seed Set A")
    for p in policies:
        lines.append(f"- **{p}**: {a['win_counts'].get(p, 0)} wins")
    lines.append("")
    lines.append("### Seed Set B (holdout)")
    for p in policies:
        lines.append(f"- **{p}**: {b['win_counts'].get(p, 0)} wins")
    lines.append("")
    lines.append("## Holdout stability (delta vs `always_act` per point)")
    for pol, info in sorted(corrs.items(), key=lambda kv: kv[0]):
        lines.append(f"- **{pol}**: n_points={info['n_points']}, pearson={info['pearson']}")
    lines.append("")
    lines.append("## Point-level winners (A and B)")
    lines.append("| point_key | winner_A | winner_B |")
    lines.append("|---|---|---|")
    for pk in common_points:
        lines.append(f"| `{pk}` | `{a['points'][pk]['winner']}` | `{b['points'][pk]['winner']}` |")
    lines.append("")
    lines.append("## Notes")
    lines.append("- This summary requires `sweep_summary.json` per sweep. If missing, run:")
    lines.append("  - `exp-suite summarize-sweep --sweep-dir <sweep_dir>`")
    lines.append("")
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate thesis-defensible Exp2 policy sweep summary from sweep_summary.json files.")
    ap.add_argument("--artifacts-a", type=Path, default=Path(r"C:\exp2_policy_artifacts"))
    ap.add_argument("--artifacts-b", type=Path, default=Path(r"C:\exp2_policy_artifacts"))
    ap.add_argument("--sweep-prefix-a", type=str, default="exp2_policy_v1__A")
    ap.add_argument("--sweep-prefix-b", type=str, default="exp2_policy_v1__B")
    ap.add_argument("--policy", action="append", default=[], help="Repeat to set policy set (default includes 4 policies).")
    ap.add_argument("--out-md", type=Path, default=Path("docs/experiment_2_policy_summary.md"))
    args = ap.parse_args()

    policies = list(args.policy) if args.policy else list(DEFAULT_POLICIES)

    a = collect_seedset(artifacts_dir=args.artifacts_a, sweep_prefix=args.sweep_prefix_a, policies=policies)
    b = collect_seedset(artifacts_dir=args.artifacts_b, sweep_prefix=args.sweep_prefix_b, policies=policies)

    md = render_md(a, b)
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.write_text(md, encoding="utf-8")
    print(f"Wrote: {args.out_md}")


if __name__ == "__main__":
    main()


