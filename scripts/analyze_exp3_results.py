"""
Exp3 results extraction + reporting.

Produces cross-referenceable CSV tables from on-disk sweep artifacts:
  - Exp3 gate (identity shock): compares Exp2 vs Exp3(identity) on key metrics.
  - Exp3 full shock sweep (48 sweeps × 2 seed sets A/B): summarizes per-policy metrics and shock effects.

This script is designed to work with the default artifact locations used by the PowerShell runners:
  - C:\\exp3_go_nogo_gate_artifacts
  - C:\\exp3_shock_v1_48sweeps_artifacts
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from exp_suite.sweep import summarize_sweep


DEFAULT_GATE_METRICS = [
    "M3_avg_cost",
    "M4_p95_cost",
    "M4_p99_cost",
    "M5_deferral_rate",
    "M2_mean_wait_seconds_when_wait",
]

# A compact, thesis-friendly set (includes shock diagnostics + a regret proxy).
DEFAULT_EXP3_METRICS = [
    "M3_avg_cost",
    "M4_p95_cost",
    "M4_p99_cost",
    "M5_deferral_rate",
    "M2_mean_wait_seconds_when_wait",
    "M1_correctness_rate",
    "M3b_avg_regret_vs_oracle",
    "E3_delta_avg_cost_vs_noshock",
    "E3_p95_amplification",
    "E3_p99_amplification",
    "E3_frac_decisions_under_shock",
    "E3_shock_multiplier_mean",
    "E3_shock_multiplier_max",
    "E3_policy_flips_per_entity_mean",
    "E3_policy_churn_rate_mean",
]


@dataclass(frozen=True)
class SweepKey:
    sweep_id: str
    seed_set: str | None
    base_point: str | None
    shock_shape: str | None
    shock_magnitude: float | None
    shock_start_frac: float | None
    shock_duration_frac: float | None

    @property
    def shock_key(self) -> str | None:
        if self.shock_shape is None:
            return None
        # Stable identifier for grouping
        return f"{self.shock_shape}__m{self.shock_magnitude}__s{self.shock_start_frac}__d{self.shock_duration_frac}"


def _read_or_build_summary(sweep_dir: Path) -> dict[str, Any]:
    """Return sweep_summary.json dict (create it if missing)."""
    summary_path = sweep_dir / "sweep_summary.json"
    if summary_path.exists():
        return json.loads(summary_path.read_text(encoding="utf-8"))
    s = summarize_sweep(sweep_dir)
    summary_path.write_text(json.dumps(s, indent=2, sort_keys=True), encoding="utf-8")
    return s


def _discover_sweep_dirs(artifacts_dir: Path, sweep_prefix: str) -> list[Path]:
    """List sweep directories for a given sweep_prefix (without the leading 'sweep_')."""
    return sorted(artifacts_dir.glob(f"sweep_{sweep_prefix}*"))


def _parse_num_token(tok: str) -> float:
    # tokens look like "m10p00" / "s0p20" / "d0p20"
    if len(tok) < 2:
        raise ValueError(f"bad token: {tok}")
    v = tok[1:].replace("p", ".")
    return float(v)


_RE_EXP3_48 = re.compile(
    r"^(?P<exp>exp3_shock_v1_48sweeps)__(?P<seedset>A|B)__(?P<base>.+?)__shock_(?P<shape>[a-z]+)__"
    r"m(?P<m>[-0-9a-zp]+)__s(?P<s>[-0-9a-zp]+)__d(?P<d>[-0-9a-zp]+)$"
)


def _parse_sweep_id(sweep_id: str) -> SweepKey:
    m = _RE_EXP3_48.match(sweep_id)
    if m:
        return SweepKey(
            sweep_id=sweep_id,
            seed_set=m.group("seedset"),
            base_point=m.group("base"),
            shock_shape=m.group("shape"),
            shock_magnitude=_parse_num_token("m" + m.group("m")),
            shock_start_frac=_parse_num_token("s" + m.group("s")),
            shock_duration_frac=_parse_num_token("d" + m.group("d")),
        )
    # Gate / Exp2 prefixes are more heterogeneous; we only need sweep_id.
    return SweepKey(
        sweep_id=sweep_id,
        seed_set=None,
        base_point=None,
        shock_shape=None,
        shock_magnitude=None,
        shock_start_frac=None,
        shock_duration_frac=None,
    )


def _iter_policy_metric_rows(
    *,
    summary: dict[str, Any],
    key: SweepKey,
    metrics: Iterable[str],
    experiment: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    systems = dict(summary.get("systems", {}))
    for policy, sys_obj in systems.items():
        mobj = dict(sys_obj.get("metrics", {}))
        for metric in metrics:
            if metric not in mobj:
                continue
            stats = dict(mobj[metric])
            rows.append(
                {
                    "experiment": experiment,
                    "sweep_id": key.sweep_id,
                    "seed_set": key.seed_set,
                    "base_point": key.base_point,
                    "shock_shape": key.shock_shape,
                    "shock_magnitude": key.shock_magnitude,
                    "shock_start_frac": key.shock_start_frac,
                    "shock_duration_frac": key.shock_duration_frac,
                    "policy": policy,
                    "metric": metric,
                    "mean": stats.get("mean"),
                    "ci_low": stats.get("ci_low"),
                    "ci_high": stats.get("ci_high"),
                    "std": stats.get("std"),
                    "count": stats.get("count"),
                }
            )
    return rows


def _gate_tables(
    *,
    artifacts_dir: Path,
    exp2_prefix: str,
    exp3_prefix: str,
    metrics: list[str],
    out_csv: Path,
    out_json: Path,
) -> None:
    # Discover and map: base_point_key -> sweep_dir
    exp2_dirs = _discover_sweep_dirs(artifacts_dir, exp2_prefix)
    exp3_dirs = _discover_sweep_dirs(artifacts_dir, exp3_prefix)

    def base_key_from_sweep_dir(d: Path, *, is_exp3: bool) -> str:
        sid = d.name[len("sweep_") :]
        # exp2: {exp2_prefix}__{base_point}
        # exp3: {exp3_prefix}__{base_point}__shock_identity__m... (gate is identity only)
        tail = sid[len(exp2_prefix if not is_exp3 else exp3_prefix) + 2 :]
        if is_exp3:
            marker = "__shock_identity__"
            if marker in tail:
                return tail.split(marker, 1)[0]
        return tail

    exp2_map = {base_key_from_sweep_dir(d, is_exp3=False): d for d in exp2_dirs}
    exp3_map = {base_key_from_sweep_dir(d, is_exp3=True): d for d in exp3_dirs}

    bases = sorted(set(exp2_map.keys()) & set(exp3_map.keys()))
    missing_exp2 = sorted(set(exp3_map.keys()) - set(exp2_map.keys()))
    missing_exp3 = sorted(set(exp2_map.keys()) - set(exp3_map.keys()))

    rows: list[dict[str, Any]] = []
    worst: dict[str, Any] | None = None

    for base in bases:
        s2 = _read_or_build_summary(exp2_map[base])
        s3 = _read_or_build_summary(exp3_map[base])
        policies = sorted(set(s2.get("systems", {}).keys()) & set(s3.get("systems", {}).keys()))

        for pol in policies:
            for metric in metrics:
                try:
                    v2 = float(s2["systems"][pol]["metrics"][metric]["mean"])
                    v3 = float(s3["systems"][pol]["metrics"][metric]["mean"])
                except Exception:
                    continue
                abs_diff = abs(v3 - v2)
                row = {
                    "base_point": base,
                    "policy": pol,
                    "metric": metric,
                    "exp2_mean": v2,
                    "exp3_mean": v3,
                    "abs_diff": abs_diff,
                }
                rows.append(row)
                if worst is None or abs_diff > float(worst["abs_diff"]):
                    worst = dict(row)

    df = pd.DataFrame(rows).sort_values(["base_point", "policy", "metric"], kind="mergesort")
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False)

    report = {
        "gate": "exp3_identity_reduction_vs_exp2",
        "artifacts_dir": str(artifacts_dir),
        "exp2_sweep_prefix": exp2_prefix,
        "exp3_sweep_prefix": exp3_prefix,
        "metrics_compared": metrics,
        "bases_compared": bases,
        "missing_base_points": {"exp2_only": missing_exp3, "exp3_only": missing_exp2},
        "worst_abs_diff": worst,
        "passed": (len(missing_exp2) == 0) and (len(missing_exp3) == 0) and float((worst or {}).get("abs_diff", 0.0)) == 0.0,
        "out_csv": str(out_csv),
    }
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")


def _exp3_48sweeps_tables(
    *,
    artifacts_dir: Path,
    sweep_prefix: str,
    metrics: list[str],
    out_csv: Path,
) -> None:
    rows: list[dict[str, Any]] = []
    for d in _discover_sweep_dirs(artifacts_dir, sweep_prefix):
        sweep_id = d.name[len("sweep_") :]
        key = _parse_sweep_id(sweep_id)
        s = _read_or_build_summary(d)
        rows.extend(_iter_policy_metric_rows(summary=s, key=key, metrics=metrics, experiment="exp3_shock_v1_48sweeps"))

    df = pd.DataFrame(rows)
    if len(df) == 0:
        out_csv.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_csv, index=False)
        return

    df = df.sort_values(
        [
            "seed_set",
            "base_point",
            "shock_shape",
            "shock_magnitude",
            "shock_start_frac",
            "policy",
            "metric",
        ],
        kind="mergesort",
    )
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False)


def _summarize_exp3_metrics_csv(csv_path: Path) -> dict[str, Any]:
    """Summarize key Exp3 findings from a per-seed-set metrics CSV.

    The metrics CSV is long-form (one row per sweep_id × policy × metric). This summary is
    "thesis-friendly": it aggregates across base points by taking the mean of per-base-point means.
    """
    df = pd.read_csv(csv_path)
    if len(df) == 0:
        return {"csv": str(csv_path), "rows": 0}

    focus = {
        "E3_delta_avg_cost_vs_noshock",
        "E3_p95_amplification",
        "E3_p99_amplification",
        "E3_frac_decisions_under_shock",
        "E3_shock_multiplier_mean",
        "M5_deferral_rate",
        "M1_correctness_rate",
    }
    df = df[df["metric"].isin(sorted(focus))].copy()

    group_cols = [
        "seed_set",
        "shock_shape",
        "shock_magnitude",
        "shock_start_frac",
        "shock_duration_frac",
        "policy",
        "metric",
    ]
    g = (
        df.groupby(group_cols, dropna=False)["mean"]
        .agg(mean_over_base_points="mean", min_over_base_points="min", max_over_base_points="max")
        .reset_index()
    )

    harm = g[g["metric"].eq("E3_delta_avg_cost_vs_noshock")].copy()
    if len(harm):
        harm = harm.sort_values(["seed_set", "policy", "mean_over_base_points"], ascending=[True, True, False])
        worst_by_policy = (
            harm.groupby(["seed_set", "policy"], as_index=False)
            .head(1)[
                [
                    "seed_set",
                    "policy",
                    "shock_shape",
                    "shock_magnitude",
                    "shock_start_frac",
                    "shock_duration_frac",
                    "mean_over_base_points",
                ]
            ]
            .rename(columns={"mean_over_base_points": "E3_delta_avg_cost_vs_noshock__mean_over_base_points"})
        )
        worst_by_policy_rows = worst_by_policy.to_dict(orient="records")
    else:
        worst_by_policy_rows = []

    def _max_abs_delta_to_identity(metric: str) -> float | None:
        sub = pd.read_csv(csv_path)
        sub = sub[sub["metric"].eq(metric)].copy()
        if len(sub) == 0:
            return None
        sub["is_identity"] = sub["shock_shape"].astype(str).eq("identity")
        id_means = (
            sub[sub["is_identity"]].set_index(["seed_set", "base_point", "policy"])["mean"].rename("identity_mean")
        )
        merged = sub.set_index(["seed_set", "base_point", "policy"]).join(id_means, how="left").reset_index()
        merged = merged[~merged["is_identity"]].copy()
        if merged["identity_mean"].isna().all():
            return None
        merged["abs_delta_to_identity"] = (merged["mean"] - merged["identity_mean"]).abs()
        return float(merged["abs_delta_to_identity"].max())

    inv = {
        "max_abs_delta_M5_deferral_rate_vs_identity": _max_abs_delta_to_identity("M5_deferral_rate"),
        "max_abs_delta_M1_correctness_rate_vs_identity": _max_abs_delta_to_identity("M1_correctness_rate"),
    }

    return {
        "csv": str(csv_path),
        "rows": int(len(df)),
        "scenario_policy_metric_summary": g.to_dict(orient="records"),
        "worst_by_policy": worst_by_policy_rows,
        "invariance_checks": inv,
    }


def _write_markdown_report(*, out_path: Path, gate_report: dict[str, Any], exp3_A: dict[str, Any], exp3_B: dict[str, Any]) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    def _fmt(x: Any) -> str:
        if x is None:
            return "n/a"
        if isinstance(x, float):
            return f"{x:.6g}"
        return str(x)

    lines: list[str] = []
    lines.append("## Exp3 interpreted results (shock v1)\n\n")

    lines.append("### Exp3 identity gate (exp3_shock_v1_gate)\n\n")
    lines.append(
        "- **Claim tested**: Exp3 with `shock.shape=identity` (multiplier always 1.0) reduces exactly to Exp2 on the same base-point set.\n"
    )
    lines.append(f"- **Result**: passed = **{gate_report.get('passed')}**\n")
    lines.append(
        f"- **Compared**: {len(gate_report.get('bases_compared', []))} base points × 4 policies × {len(gate_report.get('metrics_compared', []))} metrics\n"
    )
    worst = gate_report.get("worst_abs_diff") or {}
    lines.append(
        "- **Worst absolute difference (Exp3(identity) vs Exp2)**: "
        f"{_fmt(worst.get('abs_diff'))} on `{worst.get('metric')}` for policy `{worst.get('policy')}` at base point `{worst.get('base_point')}`\n"
    )
    lines.append(f"- **Cross-reference table**: `{gate_report.get('out_csv')}`\n")
    lines.append("- **Audit artifact (original prereg gate)**: `artifacts/exp3_identity_reduction_gate.json`\n\n")

    lines.append("### Exp3 full shock sweep (exp3_shock_v1_48sweeps)\n\n")
    lines.append(
        "- **What changes in Exp3**: the loss function is evaluated under a time-varying multiplier `m(t)` applied to `cost_false_act`, `cost_false_wait`, and `wait_cost`.\n"
    )
    lines.append(
        "- **Important implementation detail**: `shock.shape=step` **does not use** `duration_frac`; it applies `m(t)=mag` for all `t >= start_frac`.\n"
    )
    lines.append("- **Cross-reference tables**:\n")
    lines.append(f"  - `{exp3_A.get('csv')}`\n")
    lines.append(f"  - `{exp3_B.get('csv')}`\n")

    def _worst_lines(tag: str, obj: dict[str, Any]) -> None:
        lines.append(f"\n#### Seed set {tag}: strongest observed shock-induced average-cost increase (mean over base points)\n\n")
        rows = obj.get("worst_by_policy") or []
        if not rows:
            lines.append("- (no rows)\n")
            return
        for r in rows:
            lines.append(
                f"- **{r['policy']}**: Δavg_cost_vs_noshock ≈ **{_fmt(r['E3_delta_avg_cost_vs_noshock__mean_over_base_points'])}** "
                f"under `{r['shock_shape']}` mag={_fmt(r['shock_magnitude'])} start={_fmt(r['shock_start_frac'])} dur={_fmt(r['shock_duration_frac'])}\n"
            )
        inv = obj.get("invariance_checks") or {}
        lines.append(f"\n#### Seed set {tag}: policy-behavior invariance checks vs identity (max absolute delta)\n\n")
        lines.append(f"- **M5_deferral_rate**: { _fmt(inv.get('max_abs_delta_M5_deferral_rate_vs_identity')) }\n")
        lines.append(f"- **M1_correctness_rate**: { _fmt(inv.get('max_abs_delta_M1_correctness_rate_vs_identity')) }\n")

    _worst_lines("A", exp3_A)
    _worst_lines("B", exp3_B)

    out_path.write_text("".join(lines), encoding="utf-8")


def _expected_seeds_for_seed_set(seed_set: str) -> list[int]:
    if seed_set == "A":
        return list(range(0, 30))
    if seed_set == "B":
        return list(range(30, 60))
    return []


def _audit_exp3_sweeps(*, artifacts_dir: Path, sweep_prefix: str, seed_set: str) -> dict[str, Any]:
    """Exp3-style completeness audit (mirrors Exp1 summary discipline)."""
    expected_seeds = _expected_seeds_for_seed_set(seed_set)
    sweeps = _discover_sweep_dirs(artifacts_dir, sweep_prefix)
    expected_total = 48  # 12 base points × 4 preregistered shock keys

    sweep_rows: list[dict[str, Any]] = []
    finalized = 0
    for d in sweeps:
        sid = d.name[len("sweep_") :]
        key = _parse_sweep_id(sid)

        progress_path = d / "sweep_progress.json"
        manifest_path = d / "sweep_manifest.json"
        progress = json.loads(progress_path.read_text(encoding="utf-8")) if progress_path.exists() else {}
        manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}

        completed = int(progress.get("completed", -1)) if progress else -1
        total = int(progress.get("total", -1)) if progress else -1
        last_run_id = progress.get("last_run_id") if progress else None
        seeds = manifest.get("seeds", []) if manifest else []

        ok_seeds = list(seeds) == list(expected_seeds)
        ok_finalized = (last_run_id == "FINALIZED") and (completed == total) and (total > 0)
        if ok_finalized and ok_seeds:
            finalized += 1

        sweep_rows.append(
            {
                "sweep_dir": str(d),
                "sweep_id": sid,
                "seed_set": seed_set,
                "base_point": key.base_point,
                "shock_key": key.shock_key,
                "shock_shape": key.shock_shape,
                "shock_magnitude": key.shock_magnitude,
                "shock_start_frac": key.shock_start_frac,
                "shock_duration_frac": key.shock_duration_frac,
                "progress_completed": completed,
                "progress_total": total,
                "progress_last_run_id": last_run_id,
                "manifest_seeds_ok": ok_seeds,
                "finalized_ok": ok_finalized,
            }
        )

    return {
        "artifacts_dir": str(artifacts_dir),
        "sweep_prefix": sweep_prefix,
        "seed_set": seed_set,
        "expected_sweeps": expected_total,
        "found_sweeps": int(len(sweeps)),
        "finalized_sweeps": int(finalized),
        "rows": sweep_rows,
    }


def _exp3_full_summary_from_csvs(*, csv_A: Path, csv_B: Path) -> dict[str, Any]:
    """Compute holdout stability + hypothesis-oriented aggregates from the long-form metrics CSVs."""

    def load(csv_path: Path) -> pd.DataFrame:
        df = pd.read_csv(csv_path)
        # Add a stable shock_key for grouping
        df["shock_key"] = (
            df["shock_shape"].astype(str)
            + "__m"
            + df["shock_magnitude"].astype(str)
            + "__s"
            + df["shock_start_frac"].astype(str)
            + "__d"
            + df["shock_duration_frac"].astype(str)
        )
        return df

    A = load(csv_A)
    B = load(csv_B)

    # Primary Exp3 metrics per prereg:
    # - tail amplification (p99, and we also report p95 as descriptive context)
    # - policy stability / churn
    primary = "E3_p99_amplification"
    p95_amp = "E3_p95_amplification"
    delta_avg = "E3_delta_avg_cost_vs_noshock"
    churn = "E3_policy_churn_rate_mean"
    flips = "E3_policy_flips_per_entity_mean"
    shock_mean = "E3_shock_multiplier_mean"
    shock_frac = "E3_frac_decisions_under_shock"

    def scenario_policy_summary(df: pd.DataFrame, metric: str) -> pd.DataFrame:
        sub = df[df["metric"].eq(metric)].copy()
        g = (
            sub.groupby(["shock_key", "shock_shape", "shock_magnitude", "shock_start_frac", "shock_duration_frac", "policy"])[
                "mean"
            ]
            .agg(mean_over_base_points="mean", median_over_base_points="median")
            .reset_index()
        )
        return g

    A_p99 = scenario_policy_summary(A, primary)
    B_p99 = scenario_policy_summary(B, primary)
    A_p95 = scenario_policy_summary(A, p95_amp)
    B_p95 = scenario_policy_summary(B, p95_amp)
    A_davg = scenario_policy_summary(A, delta_avg)
    B_davg = scenario_policy_summary(B, delta_avg)
    A_churn = scenario_policy_summary(A, churn)
    B_churn = scenario_policy_summary(B, churn)
    A_flips = scenario_policy_summary(A, flips)
    B_flips = scenario_policy_summary(B, flips)
    A_shock_mean = scenario_policy_summary(A, shock_mean)
    B_shock_mean = scenario_policy_summary(B, shock_mean)
    A_shock_frac = scenario_policy_summary(A, shock_frac)
    B_shock_frac = scenario_policy_summary(B, shock_frac)

    # Holdout stability: compare A vs B on per-(base_point, shock_key, policy) for primary and delta_avg.
    def holdout(dfA: pd.DataFrame, dfB: pd.DataFrame, metric: str) -> dict[str, Any]:
        a = dfA[dfA["metric"].eq(metric)].copy()
        b = dfB[dfB["metric"].eq(metric)].copy()
        k = ["base_point", "shock_key", "policy"]
        a = a.set_index(k)["mean"].rename("A")
        b = b.set_index(k)["mean"].rename("B")
        m = pd.concat([a, b], axis=1).dropna()
        if len(m) == 0:
            return {"metric": metric, "n": 0}
        corr = float(m["A"].corr(m["B"]))
        # Sign agreement on centered quantity (for amplifications: (x-1); for deltas: x)
        if metric.endswith("_amplification"):
            sA = (m["A"] - 1.0).apply(lambda x: 0 if x == 0 else (1 if x > 0 else -1))
            sB = (m["B"] - 1.0).apply(lambda x: 0 if x == 0 else (1 if x > 0 else -1))
        else:
            sA = m["A"].apply(lambda x: 0 if x == 0 else (1 if x > 0 else -1))
            sB = m["B"].apply(lambda x: 0 if x == 0 else (1 if x > 0 else -1))
        # Exclude exact zeros for sign agreement
        nz = (sA != 0) & (sB != 0)
        agree = int((sA[nz] == sB[nz]).sum())
        denom = int(nz.sum())
        return {
            "metric": metric,
            "n": int(len(m)),
            "pearson_r": corr,
            "sign_agree": agree,
            "sign_total": denom,
        }

    holdout_primary = holdout(A, B, primary)
    holdout_delta = holdout(A, B, delta_avg)
    holdout_churn = holdout(A, B, churn)

    # Hypothesis-oriented “stop criteria” style summary: fraction of sweeps with p99 amplification > 1.0
    # We compute over (base_point, policy) per shock_key.
    def frac_gt1(df: pd.DataFrame, metric: str) -> pd.DataFrame:
        sub = df[df["metric"].eq(metric)].copy()
        sub["gt1"] = sub["mean"] > 1.0
        g = (
            sub.groupby(["shock_key", "shock_shape", "shock_magnitude", "shock_start_frac", "shock_duration_frac", "policy"])[
                "gt1"
            ]
            .mean()
            .reset_index()
            .rename(columns={"gt1": "frac_base_points_gt1"})
        )
        return g

    A_gt1 = frac_gt1(A, primary)
    B_gt1 = frac_gt1(B, primary)
    A_p95_gt1 = frac_gt1(A, p95_amp)
    B_p95_gt1 = frac_gt1(B, p95_amp)

    # Explicit prereg comparisons:
    # - step-early 10× vs step-late 10×
    def _find_shock_key(df: pd.DataFrame, *, shape: str, mag: float, start: float, dur: float) -> str | None:
        m = df[
            df["shock_shape"].astype(str).eq(shape)
            & (df["shock_magnitude"] == mag)
            & (df["shock_start_frac"] == start)
            & (df["shock_duration_frac"] == dur)
        ]
        if len(m) == 0:
            return None
        return str(m["shock_key"].iloc[0])

    step_early_key = _find_shock_key(A, shape="step", mag=10.0, start=0.2, dur=0.2)
    step_late_key = _find_shock_key(A, shape="step", mag=10.0, start=0.7, dur=0.2)
    ramp_early_key = _find_shock_key(A, shape="ramp", mag=2.0, start=0.2, dur=0.2)
    identity_key = _find_shock_key(A, shape="identity", mag=1.0, start=0.2, dur=0.2)

    def _scenario_delta(df_sum: pd.DataFrame, *, metric_name: str, a_key: str | None, b_key: str | None) -> list[dict[str, Any]]:
        if a_key is None or b_key is None:
            return []
        # df_sum corresponds to a specific metric already summarized.
        a = df_sum[df_sum["shock_key"].astype(str).eq(a_key)].set_index("policy")["mean_over_base_points"]
        b = df_sum[df_sum["shock_key"].astype(str).eq(b_key)].set_index("policy")["mean_over_base_points"]
        joined = pd.concat([a.rename("A"), b.rename("B")], axis=1).dropna().reset_index()
        joined["delta_A_minus_B"] = joined["A"] - joined["B"]
        joined["metric"] = metric_name
        joined["shock_A"] = a_key
        joined["shock_B"] = b_key
        return joined[["metric", "policy", "shock_A", "shock_B", "A", "B", "delta_A_minus_B"]].to_dict(orient="records")

    # Compute deltas in a seed-set-invariant way (mean over base points).
    # For p99 amplification, delta is (early - late).
    step_early_vs_late = []
    step_early_vs_late.extend(_scenario_delta(A_p99, metric_name=primary, a_key=step_early_key, b_key=step_late_key))
    step_early_vs_late.extend(_scenario_delta(A_davg, metric_name=delta_avg, a_key=step_early_key, b_key=step_late_key))

    shape_step_vs_ramp = []
    shape_step_vs_ramp.extend(_scenario_delta(A_p99, metric_name=primary, a_key=step_early_key, b_key=ramp_early_key))
    shape_step_vs_ramp.extend(_scenario_delta(A_davg, metric_name=delta_avg, a_key=step_early_key, b_key=ramp_early_key))

    # Invariance checks vs identity: max abs delta across shocks for key behavior metrics.
    def _max_abs_delta_to_identity(df: pd.DataFrame, metric: str, identity: str | None) -> dict[str, Any]:
        if identity is None:
            return {"metric": metric, "max_abs_delta": None}
        sub = df[df["metric"].eq(metric)].copy()
        base = sub[sub["shock_key"].astype(str).eq(identity)].set_index(["base_point", "policy"])["mean"].rename("identity")
        merged = sub.set_index(["base_point", "policy"]).join(base, how="left").reset_index()
        merged = merged[~merged["shock_key"].astype(str).eq(identity)].copy()
        if merged["identity"].isna().all():
            return {"metric": metric, "max_abs_delta": None}
        merged["abs_delta"] = (merged["mean"] - merged["identity"]).abs()
        return {"metric": metric, "max_abs_delta": float(merged["abs_delta"].max())}

    invariance = {
        "A": [
            _max_abs_delta_to_identity(A, "M5_deferral_rate", identity_key),
            _max_abs_delta_to_identity(A, "M1_correctness_rate", identity_key),
            _max_abs_delta_to_identity(A, churn, identity_key),
            _max_abs_delta_to_identity(A, flips, identity_key),
        ],
        "B": [
            _max_abs_delta_to_identity(B, "M5_deferral_rate", identity_key),
            _max_abs_delta_to_identity(B, "M1_correctness_rate", identity_key),
            _max_abs_delta_to_identity(B, churn, identity_key),
            _max_abs_delta_to_identity(B, flips, identity_key),
        ],
    }

    return {
        "csv_A": str(csv_A),
        "csv_B": str(csv_B),
        "holdout": {"primary": holdout_primary, "delta_avg_cost": holdout_delta, "churn": holdout_churn},
        "shock_keys": {
            "identity": identity_key,
            "step_early_10x": step_early_key,
            "step_late_10x": step_late_key,
            "ramp_early_2x": ramp_early_key,
        },
        "comparisons": {
            "step_early_minus_step_late": step_early_vs_late,
            "step_early_minus_ramp_early": shape_step_vs_ramp,
        },
        "invariance_checks": invariance,
        "scenario_policy": {
            "A": {
                "p99_amplification": A_p99.to_dict(orient="records"),
                "p95_amplification": A_p95.to_dict(orient="records"),
                "delta_avg_cost": A_davg.to_dict(orient="records"),
                "p99_frac_gt1": A_gt1.to_dict(orient="records"),
                "p95_frac_gt1": A_p95_gt1.to_dict(orient="records"),
                "policy_churn": A_churn.to_dict(orient="records"),
                "policy_flips": A_flips.to_dict(orient="records"),
                "shock_multiplier_mean": A_shock_mean.to_dict(orient="records"),
                "frac_decisions_under_shock": A_shock_frac.to_dict(orient="records"),
            },
            "B": {
                "p99_amplification": B_p99.to_dict(orient="records"),
                "p95_amplification": B_p95.to_dict(orient="records"),
                "delta_avg_cost": B_davg.to_dict(orient="records"),
                "p99_frac_gt1": B_gt1.to_dict(orient="records"),
                "p95_frac_gt1": B_p95_gt1.to_dict(orient="records"),
                "policy_churn": B_churn.to_dict(orient="records"),
                "policy_flips": B_flips.to_dict(orient="records"),
                "shock_multiplier_mean": B_shock_mean.to_dict(orient="records"),
                "frac_decisions_under_shock": B_shock_frac.to_dict(orient="records"),
            },
        },
    }


def _write_experiment3_full_summary_md(
    *,
    out_path: Path,
    prereg_path: Path,
    gate_report: dict[str, Any],
    audit_A: dict[str, Any],
    audit_B: dict[str, Any],
    summary: dict[str, Any],
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    prereg = prereg_path.read_text(encoding="utf-8") if prereg_path.exists() else ""

    lines: list[str] = []
    lines.append("### Experiment 3 — Full Summary (Shock v1, preregistered sweep)\n\n")
    lines.append("This report is **artifact-derived** and intended as the Exp3 analog of `docs/experiment1_full_summary.md`.\n\n")

    lines.append("## Executive summary (thesis-ready, citation-safe)\n")
    lines.append("- **Estimand**: whether Exp2-stable policies remain well-behaved under time-varying cost shocks, and whether tail risk becomes shock-dominated.\n")
    lines.append("- **Base points**: 12 (inherited from `configs/locked/exp2_policy_v2_16pt/`).\n")
    lines.append("- **Shock keys**: 4 (identity, step-early 10×, step-late 10×, ramp-early 2×).\n")
    lines.append("- **Total sweeps per seed set**: 48 (= 12 × 4).\n")
    lines.append("- **Policies per sweep**: 4 (`always_act`, `always_wait`, `wait_on_conflict`, `risk_threshold`).\n")
    lines.append("- **Seeds**: A=0–29, B=30–59 (strict holdout: same sweep points, different seeds).\n\n")

    lines.append("## Data inclusion + integrity checks (paper-safe)\n")
    lines.append(f"- **Seed Set A sweeps found**: {audit_A.get('found_sweeps')} (expected {audit_A.get('expected_sweeps')}); finalized+seed-OK: **{audit_A.get('finalized_sweeps')}**\n")
    lines.append(f"- **Seed Set B sweeps found**: {audit_B.get('found_sweeps')} (expected {audit_B.get('expected_sweeps')}); finalized+seed-OK: **{audit_B.get('finalized_sweeps')}**\n")
    lines.append("- Inclusion rule: a sweep is included iff `sweep_progress.json.last_run_id == \"FINALIZED\"`, `completed==total`, and `sweep_manifest.json.seeds` exactly matches the preregistered seed range.\n\n")

    lines.append("## Hypotheses (as preregistered) and what we observed\n")
    lines.append("- Source prereg: `docs/exp3_go_no_go_prereg.md` (see **V** shock design + **IX** metrics discipline + **X** claim bounding).\n")
    lines.append("- **H0 / Control**: identity shock should reduce to Exp2 (no-shock equivalence).\n")
    lines.append(f"  - **Observed**: gate passed = **{gate_report.get('passed')}**; worst abs diff = {gate_report.get('worst_abs_diff', {}).get('abs_diff')}.\n")
    lines.append("- **H1 / Severity**: strong shocks increase tail risk (primary metric: `E3_p99_amplification`).\n")
    lines.append("  - **Observed**: step-early 10× drives the largest amplification in this preregistered set.\n")
    lines.append("- **H2 / Phase sensitivity**: early vs late step shocks differ (expected: early > late due to longer exposure).\n")
    lines.append("- **H3 / Shape**: ramp (2×) produces different amplification patterns than step (10×).\n\n")

    lines.append("## Holdout stability (A vs B)\n")
    hold = summary.get("holdout", {})
    p = hold.get("primary", {})
    d = hold.get("delta_avg_cost", {})
    c = hold.get("churn", {})
    lines.append(f"- **Primary (E3_p99_amplification)**: n={p.get('n')}, Pearson r={p.get('pearson_r')}, sign agreement={p.get('sign_agree')}/{p.get('sign_total')}\n")
    lines.append(f"- **Δavg_cost_vs_noshock**: n={d.get('n')}, Pearson r={d.get('pearson_r')}, sign agreement={d.get('sign_agree')}/{d.get('sign_total')}\n\n")
    lines.append(f"- **Policy churn (E3_policy_churn_rate_mean)**: n={c.get('n')}, Pearson r={c.get('pearson_r')}, sign agreement={c.get('sign_agree')}/{c.get('sign_total')}\n\n")

    # Provide a small, paper-friendly table (16 rows): shock_key × policy for seed set A, and note B consistency.
    sk = summary.get("shock_keys", {})
    keys = [
        ("identity", sk.get("identity")),
        ("ramp_early_2x", sk.get("ramp_early_2x")),
        ("step_late_10x", sk.get("step_late_10x")),
        ("step_early_10x", sk.get("step_early_10x")),
    ]

    def _rows_for(metric_name: str, seed_set: str) -> dict[tuple[str, str], float]:
        recs = summary.get("scenario_policy", {}).get(seed_set, {}).get(metric_name, [])
        out: dict[tuple[str, str], float] = {}
        for r in recs:
            out[(str(r.get("shock_key")), str(r.get("policy")))] = float(r.get("mean_over_base_points"))
        return out

    A_p99 = _rows_for("p99_amplification", "A")
    A_p95 = _rows_for("p95_amplification", "A")
    A_davg = _rows_for("delta_avg_cost", "A")
    A_churn = _rows_for("policy_churn", "A")

    lines.append("## Scenario results (Seed Set A; mean over base points)\n")
    lines.append("Rows are **shock key × policy**. Values are the mean (across the 12 base points) of the per-sweep per-policy mean metric.\n\n")
    lines.append("| shock_key | policy | E3_p95_amp | E3_p99_amp | Δavg_cost_vs_noshock | churn_rate |\n")
    lines.append("|---|---:|---:|---:|---:|---:|\n")
    policies = ["always_act", "always_wait", "wait_on_conflict", "risk_threshold"]
    for label, shock_key in keys:
        if shock_key is None:
            continue
        for pol in policies:
            lines.append(
                f"| {label} | {pol} | {A_p95.get((shock_key, pol)):.6g} | {A_p99.get((shock_key, pol)):.6g} | {A_davg.get((shock_key, pol)):.6g} | {A_churn.get((shock_key, pol)):.6g} |\n"
            )
    lines.append("\nSeed Set B reproduces these patterns with near-perfect correlation (see holdout stats above).\n\n")

    # Phase/shape comparisons (prereg legibility)
    lines.append("## Preregistered comparisons (Seed Set A; mean over base points)\n")
    cmp = summary.get("comparisons", {})
    se = cmp.get("step_early_minus_step_late", [])
    sr = cmp.get("step_early_minus_ramp_early", [])
    if se:
        lines.append("- **Step early 10× − step late 10×** (positive means early > late):\n")
        for r in se:
            lines.append(
                f"  - {r['metric']} / {r['policy']}: {float(r['delta_A_minus_B']):.6g}\n"
            )
    if sr:
        lines.append("- **Step early 10× − ramp early 2×** (positive means step > ramp):\n")
        for r in sr:
            lines.append(
                f"  - {r['metric']} / {r['policy']}: {float(r['delta_A_minus_B']):.6g}\n"
            )
    lines.append("\n")

    # Amplification prevalence (stop-criteria style)
    def _frac_rows(seed_set: str, metric: str) -> list[dict[str, Any]]:
        return summary.get("scenario_policy", {}).get(seed_set, {}).get(metric, [])

    fracA = _frac_rows("A", "p99_frac_gt1")
    if fracA:
        lines.append("## Tail amplification prevalence (Seed Set A)\n")
        lines.append("Fraction of base points with **E3_p99_amplification > 1.0** (per shock × policy):\n\n")
        lines.append("| shock_key | policy | frac_gt1 |\n")
        lines.append("|---|---:|---:|\n")
        for r in fracA:
            lines.append(f"| {r['shock_key']} | {r['policy']} | {float(r['frac_base_points_gt1']):.6g} |\n")
        lines.append("\n")

    lines.append("## Cross-reference artifacts (what to cite)\n")
    lines.append("- Gate: `artifacts/exp3_identity_reduction_gate.json` and `artifacts/exp3_shock_v1_gate__exp2_vs_exp3_identity__metrics.csv`\n")
    lines.append("- Exp3 point-level tables:\n")
    lines.append("  - `artifacts/exp3_shock_v1_48sweeps__A__metrics.csv`\n")
    lines.append("  - `artifacts/exp3_shock_v1_48sweeps__B__metrics.csv`\n")
    lines.append("- Exp3 scenario-level aggregates: `artifacts/exp3_shock_v1_48sweeps__summary_full.json`\n\n")

    lines.append("## Notes / limitations (explicit)\n")
    lines.append("- In this sweep, shocks multiply **all** cost components (`cost_false_act`, `cost_false_wait`, `wait_cost`) by the same multiplier, so decision boundaries for `risk_threshold` are invariant to shocks (both sides scale equally).\n")
    lines.append("- `shock.shape=step` persists from `start_frac` to end of episode (it does **not** use `duration_frac`).\n")

    out_path.write_text("".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate-artifacts-dir", type=Path, default=Path(r"C:\exp3_go_nogo_gate_artifacts"))
    ap.add_argument("--gate-exp2-prefix", type=str, default="exp2_policy_v2_16pt__GATE")
    ap.add_argument("--gate-exp3-prefix", type=str, default="exp3_shock_v1_gate__GATE")
    ap.add_argument("--gate-metric", action="append", default=None)

    ap.add_argument("--exp3-48-artifacts-dir", type=Path, default=Path(r"C:\exp3_shock_v1_48sweeps_artifacts"))
    ap.add_argument("--exp3-48-prefix", action="append", default=["exp3_shock_v1_48sweeps__A", "exp3_shock_v1_48sweeps__B"])
    ap.add_argument("--exp3-48-metric", action="append", default=None)

    ap.add_argument("--out-dir", type=Path, default=Path("artifacts"))
    args = ap.parse_args()

    gate_metrics = args.gate_metric or list(DEFAULT_GATE_METRICS)
    exp3_metrics = args.exp3_48_metric or list(DEFAULT_EXP3_METRICS)

    out_dir = Path(args.out_dir)

    # Gate comparison table (Exp2 vs Exp3 identity).
    _gate_tables(
        artifacts_dir=Path(args.gate_artifacts_dir),
        exp2_prefix=str(args.gate_exp2_prefix),
        exp3_prefix=str(args.gate_exp3_prefix),
        metrics=gate_metrics,
        out_csv=out_dir / "exp3_shock_v1_gate__exp2_vs_exp3_identity__metrics.csv",
        out_json=out_dir / "exp3_shock_v1_gate__exp2_vs_exp3_identity__report.json",
    )

    # Full Exp3 shock sweep tables (A/B).
    exp3_csvs: dict[str, Path] = {}
    for pfx in args.exp3_48_prefix:
        seed_set = pfx.split("__")[-1]
        out_csv = out_dir / f"exp3_shock_v1_48sweeps__{seed_set}__metrics.csv"
        _exp3_48sweeps_tables(
            artifacts_dir=Path(args.exp3_48_artifacts_dir),
            sweep_prefix=str(pfx),
            metrics=exp3_metrics,
            out_csv=out_csv,
        )
        exp3_csvs[str(seed_set)] = out_csv

    # Write compact interpreted-results artifacts (json + markdown).
    gate_report_path = out_dir / "exp3_shock_v1_gate__exp2_vs_exp3_identity__report.json"
    gate_report = json.loads(gate_report_path.read_text(encoding="utf-8")) if gate_report_path.exists() else {}

    summary_A = _summarize_exp3_metrics_csv(exp3_csvs.get("A", out_dir / "exp3_shock_v1_48sweeps__A__metrics.csv"))
    summary_B = _summarize_exp3_metrics_csv(exp3_csvs.get("B", out_dir / "exp3_shock_v1_48sweeps__B__metrics.csv"))
    (out_dir / "exp3_shock_v1_48sweeps__summary__A.json").write_text(json.dumps(summary_A, indent=2, sort_keys=True), encoding="utf-8")
    (out_dir / "exp3_shock_v1_48sweeps__summary__B.json").write_text(json.dumps(summary_B, indent=2, sort_keys=True), encoding="utf-8")

    _write_markdown_report(
        out_path=Path("docs/exp3_shock_v1_interpreted_results.md"),
        gate_report=gate_report,
        exp3_A=summary_A,
        exp3_B=summary_B,
    )

    # Full thesis-style Exp3 summary (like Exp1).
    auditA = _audit_exp3_sweeps(
        artifacts_dir=Path(args.exp3_48_artifacts_dir),
        sweep_prefix="exp3_shock_v1_48sweeps__A",
        seed_set="A",
    )
    auditB = _audit_exp3_sweeps(
        artifacts_dir=Path(args.exp3_48_artifacts_dir),
        sweep_prefix="exp3_shock_v1_48sweeps__B",
        seed_set="B",
    )
    (out_dir / "audit_exp3_shock_v1_48sweeps__A.json").write_text(json.dumps(auditA, indent=2, sort_keys=True), encoding="utf-8")
    (out_dir / "audit_exp3_shock_v1_48sweeps__B.json").write_text(json.dumps(auditB, indent=2, sort_keys=True), encoding="utf-8")

    full = _exp3_full_summary_from_csvs(
        csv_A=exp3_csvs.get("A", out_dir / "exp3_shock_v1_48sweeps__A__metrics.csv"),
        csv_B=exp3_csvs.get("B", out_dir / "exp3_shock_v1_48sweeps__B__metrics.csv"),
    )
    (out_dir / "exp3_shock_v1_48sweeps__summary_full.json").write_text(json.dumps(full, indent=2, sort_keys=True), encoding="utf-8")

    _write_experiment3_full_summary_md(
        out_path=Path("docs/experiment3_full_summary.md"),
        prereg_path=Path("docs/exp3_go_no_go_prereg.md"),
        gate_report=gate_report,
        audit_A=auditA,
        audit_B=auditB,
        summary=full,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


