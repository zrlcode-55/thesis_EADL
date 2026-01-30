from __future__ import annotations

import argparse
import json
import math
import statistics
from pathlib import Path
from typing import Any


PRIMARY_METRIC = "M3_avg_cost"  # lower is better
DEFAULT_POLICIES = ["always_act", "always_wait", "wait_on_conflict", "risk_threshold"]
DEFAULT_REPORT_METRICS = [
    # Primary outcome
    "M3_avg_cost",
    # Tradeoff context
    "M5_deferral_rate",
    "M2_mean_wait_seconds_when_wait",
    "M4_p95_cost",
    "M4_p99_cost",
    # Policy correctness / decision-theoretic sanity
    "M1_correctness_rate",
    "M3b_avg_regret_vs_oracle",
]


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
    report_metrics: list[str],
    sweep_summary_filename: str = "sweep_summary.json",
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

        ss_path = sweep_dir / sweep_summary_filename
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
            pol_row: dict[str, Any] = {"metrics": {}}
            for metric in report_metrics:
                m = _policy_metric_mean_from_sweep_summary(summary, pol, metric)
                if m is None:
                    ok = False
                    break
                lo, hi = _policy_metric_ci_from_sweep_summary(summary, pol, metric)
                pol_row["metrics"][metric] = {"mean": m, "ci_low": lo, "ci_high": hi}
            if not ok:
                break
            row["policies"][pol] = pol_row
        if not ok:
            continue

        # Winner (lowest mean)
        best_pol = min(policies, key=lambda p: float(row["policies"][p]["metrics"][PRIMARY_METRIC]["mean"]))
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
            base = float(r["policies"]["always_act"]["metrics"][PRIMARY_METRIC]["mean"])
            for pol in policies:
                deltas_vs_act[pol][pk] = float(r["policies"][pol]["metrics"][PRIMARY_METRIC]["mean"]) - base

    return {
        "artifacts_dir": str(artifacts_dir),
        "sweep_prefix": sweep_prefix,
        "policies": policies,
        "report_metrics": report_metrics,
        "sweep_summary_filename": sweep_summary_filename,
        "points": points,
        "points_count": len(points),
        "win_counts": win_counts,
        "deltas_vs_always_act_by_policy": deltas_vs_act,
    }


def render_md(a: dict[str, Any], b: dict[str, Any]) -> str:
    policies = a["policies"]
    report_metrics = a.get("report_metrics", [])
    common_points = sorted(set(a["points"].keys()) & set(b["points"].keys()))

    def _mean_over_points(seedset: dict[str, Any], pol: str, metric: str) -> float | None:
        vals: list[float] = []
        for pk in sorted(seedset["points"].keys()):
            try:
                vals.append(float(seedset["points"][pk]["policies"][pol]["metrics"][metric]["mean"]))
            except Exception:
                continue
        return _mean(vals)

    def _fmt(x: float | None, *, nd: int = 6) -> str:
        if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))):
            return "NA"
        return f"{x:.{nd}f}"

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
    lines.append("This report summarizes Exp2 policy sweeps (fixed state semantics; policy varies) from sweep summaries.")
    lines.append(f"- Sweep prefix A: `{a.get('sweep_prefix')}`")
    lines.append(f"- Sweep prefix B: `{b.get('sweep_prefix')}`")
    lines.append("")
    lines.append("## Inputs (artifact anchors)")
    lines.append(f"- Seed Set A artifacts: `{a['artifacts_dir']}` (prefix `{a['sweep_prefix']}`)")
    lines.append(f"- Holdout Seed Set B artifacts: `{b['artifacts_dir']}` (prefix `{b['sweep_prefix']}`)")
    lines.append("")
    lines.append("## Primary outcome")
    lines.append(f"- **Primary metric**: `{PRIMARY_METRIC}` (lower is better)")
    lines.append(f"- **Policies**: {', '.join(f'`{p}`' for p in policies)}")
    if report_metrics:
        lines.append(f"- **Reported metrics**: {', '.join(f'`{m}`' for m in report_metrics)}")
    lines.append("")
    lines.append("## Metric definitions (thesis-safe)")
    lines.append("- **`M3_avg_cost`**: mean realized loss per labeled decision (lower is better).")
    lines.append("- **`M5_deferral_rate`**: fraction of labeled decisions where action is `WAIT`.")
    lines.append("- **`M2_mean_wait_seconds_when_wait`**: mean of `(reconciliation_arrival_time - decision_time)` over labeled decisions where action is `WAIT` (clipped at 0).")
    lines.append("- **`M1_correctness_rate`**: decision-theoretic correctness rate: a decision is “correct” if its realized loss is within `correctness_epsilon` of the minimum realized loss among `{ACT, WAIT}` under the observed outcome and realized wait duration.")
    lines.append("- **`M3b_avg_regret_vs_oracle`**: mean `(chosen_loss - oracle_loss)` where `oracle_loss = min(loss(ACT), loss(WAIT))` under the observed outcome and realized wait duration.")
    lines.append("- **Note**: these are **artifact-derived** and do **not** claim inference accuracy or representation quality; they evaluate timing decisions under the specified loss model.")
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
    key_metrics = [
        "M3_avg_cost",
        "M1_correctness_rate",
        "M3b_avg_regret_vs_oracle",
        "M5_deferral_rate",
        "M2_mean_wait_seconds_when_wait",
    ]

    lines.append("## Policy correctness + tradeoff summary (mean of per-point means)")
    lines.append("- These are descriptive aggregates across regime points; they are **not** the primary win/loss analysis.")
    lines.append("")

    def _render_seedset_table(label: str, seedset: dict[str, Any]) -> None:
        lines.append(f"### {label}")
        cols = ["policy"] + key_metrics
        lines.append("| " + " | ".join(cols) + " |")
        lines.append("|" + "|".join(["---"] * len(cols)) + "|")
        for pol in policies:
            row = [f"`{pol}`"]
            for m in key_metrics:
                row.append(_fmt(_mean_over_points(seedset, pol, m)))
            lines.append("| " + " | ".join(row) + " |")
        lines.append("")

        aa = _mean_over_points(seedset, "always_act", "M5_deferral_rate") if "always_act" in policies else None
        aw = _mean_over_points(seedset, "always_wait", "M5_deferral_rate") if "always_wait" in policies else None
        lines.append("#### Sanity checks (policy-implementation correctness)")
        lines.append(f"- **always_act deferral_rate** (expected ~0): {_fmt(aa)}")
        lines.append(f"- **always_wait deferral_rate** (expected ~1): {_fmt(aw)}")
        lines.append("")

    _render_seedset_table("Seed Set A", a)
    _render_seedset_table("Seed Set B (holdout)", b)

    lines.append("## Point-level primary metric (`M3_avg_cost`) by policy")
    lines.append("- Shows the per-point **mean** (from sweep summaries) for each policy on A and B.")
    lines.append("")
    lines.append("| point_key | policy | mean_A | mean_B | delta_B_minus_A |")
    lines.append("|---|---|---:|---:|---:|")
    for pk in common_points:
        for pol in policies:
            try:
                ma = float(a["points"][pk]["policies"][pol]["metrics"][PRIMARY_METRIC]["mean"])
                mb = float(b["points"][pk]["policies"][pol]["metrics"][PRIMARY_METRIC]["mean"])
                lines.append(f"| `{pk}` | `{pol}` | {_fmt(ma, nd=6)} | {_fmt(mb, nd=6)} | {_fmt(mb - ma, nd=6)} |")
            except Exception:
                continue
    lines.append("")

    lines.append("## Notes")
    lines.append(f"- This summary requires `{a.get('sweep_summary_filename','sweep_summary.json')}` per sweep. If missing, run:")
    lines.append("  - `exp-suite summarize-sweep --sweep-dir <sweep_dir>` (or `summarize-sweep-metrics` if using recomputed metrics)")
    lines.append("")
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate thesis-defensible Exp2 policy sweep summary from sweep_summary.json files.")
    ap.add_argument("--artifacts-a", type=Path, default=Path(r"C:\exp2_policy_artifacts"))
    ap.add_argument("--artifacts-b", type=Path, default=Path(r"C:\exp2_policy_artifacts"))
    ap.add_argument("--sweep-prefix-a", type=str, default="exp2_policy_v1__A")
    ap.add_argument("--sweep-prefix-b", type=str, default="exp2_policy_v1__B")
    ap.add_argument("--policy", action="append", default=[], help="Repeat to set policy set (default includes 4 policies).")
    ap.add_argument(
        "--report-metric",
        action="append",
        default=[],
        help="Repeat to choose which metrics to include (default includes cost + deferral + correctness/regret).",
    )
    ap.add_argument(
        "--sweep-summary-file",
        type=str,
        default="sweep_summary.json",
        help="Which sweep summary filename to read (e.g., sweep_summary.json or sweep_summary__metrics_recomputed.json).",
    )
    ap.add_argument("--out-md", type=Path, default=Path("docs/experiment_2_policy_summary.md"))
    args = ap.parse_args()

    policies = list(args.policy) if args.policy else list(DEFAULT_POLICIES)
    report_metrics = list(args.report_metric) if args.report_metric else list(DEFAULT_REPORT_METRICS)

    a = collect_seedset(
        artifacts_dir=args.artifacts_a,
        sweep_prefix=args.sweep_prefix_a,
        policies=policies,
        report_metrics=report_metrics,
        sweep_summary_filename=str(args.sweep_summary_file),
    )
    b = collect_seedset(
        artifacts_dir=args.artifacts_b,
        sweep_prefix=args.sweep_prefix_b,
        policies=policies,
        report_metrics=report_metrics,
        sweep_summary_filename=str(args.sweep_summary_file),
    )

    md = render_md(a, b)
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.write_text(md, encoding="utf-8")
    print(f"Wrote: {args.out_md}")


if __name__ == "__main__":
    main()


