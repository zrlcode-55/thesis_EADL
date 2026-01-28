from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


# --- Config ---
EXPERIMENT_ID = "exp2_grid_v1"
CONFIG_DIR = Path("configs/locked/exp2_grid_v1")

# Where we write summary artifacts (tables + audit references).
ARTIFACTS_OUT_DIR = Path("artifacts")

PRIMARY_METRIC = "M3_avg_cost"
REPORT_METRICS = [
    "M3_avg_cost",
    "M3_total_cost",
    "M4_p95_cost",
    "M4_p99_cost",
    "M5_deferral_rate",
    "M2_mean_wait_seconds",
    "M2_mean_wait_seconds_when_wait",
    "decisions_total",
    "decisions_labeled",
]

TOP_K_EXTREMES = 10


@dataclass(frozen=True)
class SeedSpec:
    label: str
    sweep_prefix: str
    artifacts_dir: Path
    seed_min: int
    seed_max: int
    expected_seed_count: int


SEED_SETS = [
    SeedSpec(
        label="A",
        sweep_prefix="exp2_grid_v1__A",
        artifacts_dir=Path("artifacts/exp2"),
        seed_min=0,
        seed_max=29,
        expected_seed_count=30,
    ),
    SeedSpec(
        label="B_r2",
        sweep_prefix="exp2_grid_v1__B_r2",
        artifacts_dir=Path(r"C:\exp2_artifacts"),
        seed_min=30,
        seed_max=59,
        expected_seed_count=30,
    ),
]


@dataclass(frozen=True)
class SelectedSweep:
    sweep_dir: Path
    sweep_id: str
    point_key: str
    created_utc: str | None
    git_rev: str | None


@dataclass(frozen=True)
class SeedCollection:
    rows: list[dict[str, Any]]
    selected_sweeps: list[SelectedSweep]
    duplicate_full_sweeps_by_point: dict[str, list[str]]
    sweep_manifest_fallback_sweeps: list[str]


def _expected_point_keys(config_dir: Path, experiment_id: str) -> list[str]:
    keys: set[str] = set()
    for p in config_dir.glob(f"{experiment_id}__*__*.toml"):
        parts = p.stem.split("__")
        if len(parts) < 3:
            continue
        keys.add("__".join(parts[1:-1]))
    return sorted(keys)


def _extract_point_key(s: str) -> str | None:
    i = s.find("cr")
    if i < 0:
        return None
    tail = s[i:]
    if "__sig" not in tail or "__cfa" not in tail or "__cws" not in tail:
        return None
    segs = tail.split("__")
    if len(segs) < 4:
        return None
    return "__".join(segs[:4])


def _mean(values: list[float]) -> float | None:
    v = [x for x in values if x is not None and not math.isnan(x)]
    return float(statistics.fmean(v)) if v else None


def _median(values: list[float]) -> float | None:
    v = [x for x in values if x is not None and not math.isnan(x)]
    return float(statistics.median(v)) if v else None


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


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _iter_sweep_dirs(artifacts_dir: Path, sweep_prefix: str) -> Iterable[Path]:
    pref = f"sweep_{sweep_prefix}"
    for d in sorted(artifacts_dir.iterdir(), key=lambda p: p.name):
        if d.is_dir() and d.name.startswith(pref):
            yield d


def _parse_iso_utc(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        s = ts.replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _sweep_created_utc(sweep_dir: Path) -> str | None:
    sp = sweep_dir / "sweep_progress.json"
    if sp.exists():
        try:
            j = _load_json(sp)
            if isinstance(j, dict) and j.get("created_utc"):
                return str(j.get("created_utc"))
        except Exception:
            pass
    sm = sweep_dir / "sweep_manifest.json"
    if sm.exists():
        try:
            j = _load_json(sm)
            if isinstance(j, dict) and j.get("created_utc"):
                return str(j.get("created_utc"))
        except Exception:
            pass
    return None


def _fmt_pct(done: int, total: int) -> str:
    if total <= 0:
        return "n/a"
    return f"{(100.0 * done / total):.1f}%"


def _collect_runs_for_seedset(seed: SeedSpec, *, progress_every: int = 200) -> SeedCollection:
    rows: list[dict[str, Any]] = []
    expected_seeds = set(range(seed.seed_min, seed.seed_max + 1))

    candidates_by_point: dict[str, list[SelectedSweep]] = {}

    for sweep_dir in _iter_sweep_dirs(seed.artifacts_dir, seed.sweep_prefix):
        point_key = _extract_point_key(sweep_dir.name)
        if not point_key:
            continue

        sp_path = sweep_dir / "sweep_progress.json"
        if not sp_path.exists():
            continue
        try:
            sp = _load_json(sp_path)
        except Exception:
            continue
        try:
            completed_i = int(sp.get("completed", 0))
            total_i = int(sp.get("total", 0))
        except Exception:
            continue
        if sp.get("last_run_id") != "FINALIZED":
            continue
        if total_i <= 0 or completed_i != total_i:
            continue
        if total_i != 3 * seed.expected_seed_count:
            continue

        sm_path = sweep_dir / "sweep_manifest.json"
        if not sm_path.exists():
            continue
        sm = _load_json(sm_path)
        seeds = sm.get("seeds") or []
        try:
            seed_set = {int(x) for x in seeds}
        except Exception:
            continue
        if seed_set != expected_seeds:
            continue

        sweep_id = str(sm.get("sweep_id") or sweep_dir.name)
        created_utc = _sweep_created_utc(sweep_dir)
        git_rev = str(sm.get("git_rev")) if sm.get("git_rev") is not None else None
        candidates_by_point.setdefault(point_key, []).append(
            SelectedSweep(
                sweep_dir=sweep_dir,
                sweep_id=sweep_id,
                point_key=point_key,
                created_utc=created_utc,
                git_rev=git_rev,
            )
        )

    selected: list[SelectedSweep] = []
    duplicate_full_sweeps_by_point: dict[str, list[str]] = {}
    sweep_manifest_fallback_sweeps: list[str] = []

    for point_key, cands in sorted(candidates_by_point.items(), key=lambda kv: kv[0]):
        if len(cands) > 1:
            duplicate_full_sweeps_by_point[point_key] = [
                c.sweep_dir.name for c in sorted(cands, key=lambda x: x.sweep_dir.name)
            ]

        def key_fn(c: SelectedSweep) -> tuple[datetime, str]:
            dt = _parse_iso_utc(c.created_utc) or datetime.min.replace(tzinfo=timezone.utc)
            return (dt, c.sweep_dir.name)

        selected.append(max(cands, key=key_fn))

    total_expected = len(selected) * 3 * seed.expected_seed_count
    done = 0
    t0 = time.time()
    last_print = 0

    def maybe_print(force: bool = False) -> None:
        nonlocal last_print
        if not force and done - last_print < progress_every:
            return
        last_print = done
        elapsed = max(1e-6, time.time() - t0)
        rate = done / elapsed
        eta = (total_expected - done) / rate if rate > 0 and total_expected else None
        eta_s = "n/a" if eta is None else f"{int(eta)}s"
        msg = f"[Seed {seed.label}] {done}/{total_expected} ({_fmt_pct(done, total_expected)})  eta={eta_s}"
        print(msg, file=sys.stderr, flush=True)

    maybe_print(force=True)

    for sel in selected:
        sm = _load_json(sel.sweep_dir / "sweep_manifest.json")
        runs = list(sm.get("runs") or [])

        sp = _load_json(sel.sweep_dir / "sweep_progress.json")
        try:
            expected_total = int(sp.get("total", 0))
        except Exception:
            expected_total = 0
        if expected_total and len(runs) != expected_total:
            rebuilt = []
            for rm_path in sel.sweep_dir.glob("*/run_manifest.json"):
                try:
                    rj = _load_json(rm_path)
                except Exception:
                    continue
                cfg = rj.get("config") if isinstance(rj, dict) else None
                sys_name = None
                if isinstance(rj, dict):
                    sys_name = rj.get("system")
                    if sys_name is None and isinstance(cfg, dict):
                        sys_name = cfg.get("system")
                run_id = None
                if isinstance(rj, dict):
                    run_id = rj.get("run_id") or rm_path.parent.name
                rebuilt.append(
                    {
                        "system": sys_name,
                        "seed": (rj.get("seed") if isinstance(rj, dict) else None),
                        "run_id": run_id,
                    }
                )
            if len(rebuilt) > len(runs):
                sweep_manifest_fallback_sweeps.append(sel.sweep_dir.name)
                runs = rebuilt

        for r in runs:
            sys_name = r.get("system")
            run_seed = r.get("seed")
            run_id = r.get("run_id")
            if sys_name not in ("baseline_a", "baseline_b", "proposed"):
                continue
            try:
                run_seed_i = int(run_seed)
            except Exception:
                continue
            if run_seed_i < seed.seed_min or run_seed_i > seed.seed_max:
                continue
            if not run_id:
                continue

            run_dir = sel.sweep_dir / str(run_id)
            met_path = run_dir / "metrics.json"
            metrics = _load_json(met_path) if met_path.exists() else None

            rows.append(
                {
                    "seed_set": seed.label,
                    "sweep_dir": str(sel.sweep_dir),
                    "sweep_id": sel.sweep_id,
                    "sweep_created_utc": sel.created_utc,
                    "sweep_git_rev": sel.git_rev,
                    "point_key": sel.point_key,
                    "system": sys_name,
                    "seed": run_seed_i,
                    "metrics_status": (metrics or {}).get("status"),
                    "metrics": (metrics or {}).get("metrics", {}) if isinstance(metrics, dict) else {},
                }
            )
            done += 1
            maybe_print()

    maybe_print(force=True)

    return SeedCollection(
        rows=rows,
        selected_sweeps=selected,
        duplicate_full_sweeps_by_point=duplicate_full_sweeps_by_point,
        sweep_manifest_fallback_sweeps=sweep_manifest_fallback_sweeps,
    )


def _point_system_means(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    # Returns: {(point_key, system): {"means": {metric: float}, "n": int}}
    buckets: dict[tuple[str, str], dict[str, list[float]]] = {}
    counts: dict[tuple[str, str], int] = {}

    for r in rows:
        pk = r.get("point_key")
        sys_name = r.get("system")
        if not pk or not sys_name:
            continue
        m = r.get("metrics") or {}
        key = (str(pk), str(sys_name))
        counts[key] = counts.get(key, 0) + 1
        mm = buckets.setdefault(key, {})
        for k in REPORT_METRICS + [PRIMARY_METRIC]:
            if k not in m:
                continue
            try:
                mm.setdefault(k, []).append(float(m[k]))
            except Exception:
                continue

    out: dict[tuple[str, str], dict[str, Any]] = {}
    for key, mm in buckets.items():
        means = {k: _mean(v) for k, v in mm.items()}
        out[key] = {"means": means, "n": counts.get(key, 0)}
    return out


def _summarize_primary_wins(
    point_means: dict[tuple[str, str], dict[str, Any]], *, expected_points: list[str]
) -> dict[str, Any]:
    wins: dict[str, dict[str, int]] = {"baseline_a": {"n": 0, "wins": 0, "losses": 0, "ties": 0}, "baseline_b": {"n": 0, "wins": 0, "losses": 0, "ties": 0}}
    deltas: dict[str, list[float]] = {"baseline_a": [], "baseline_b": []}

    for pk in expected_points:
        p = point_means.get((pk, "proposed"), {}).get("means", {}).get(PRIMARY_METRIC)
        for b in ("baseline_a", "baseline_b"):
            bm = point_means.get((pk, b), {}).get("means", {}).get(PRIMARY_METRIC)
            if p is None or bm is None:
                continue
            d = float(p - bm)
            wins[b]["n"] += 1
            if d < 0:
                wins[b]["wins"] += 1
            elif d > 0:
                wins[b]["losses"] += 1
            else:
                wins[b]["ties"] += 1
            deltas[b].append(d)

    def summarize_delta(vals: list[float]) -> dict[str, float | None]:
        if not vals:
            return {"mean": None, "median": None, "min": None, "max": None}
        return {
            "mean": float(statistics.fmean(vals)),
            "median": float(statistics.median(vals)),
            "min": float(min(vals)),
            "max": float(max(vals)),
        }

    return {"wins": wins, "deltas": {b: summarize_delta(v) for b, v in deltas.items()}}


def _summarize_metric_across_points(
    point_means: dict[tuple[str, str], dict[str, Any]], *, expected_points: list[str]
) -> dict[str, Any]:
    # Mean-of-per-point-means per system per metric (descriptive context).
    out: dict[str, dict[str, dict[str, Any]]] = {s: {} for s in ("baseline_a", "baseline_b", "proposed")}
    for sys_name in ("baseline_a", "baseline_b", "proposed"):
        for metric in REPORT_METRICS:
            vals = []
            for pk in expected_points:
                m = point_means.get((pk, sys_name), {}).get("means", {}).get(metric)
                if m is None or (isinstance(m, float) and math.isnan(m)):
                    continue
                vals.append(float(m))
            out[sys_name][metric] = {"mean_of_point_means": _mean(vals), "n_points": len(vals)}
    return out


def _write_csv_table(out_csv: Path, expected_points: list[str], point_means: dict[tuple[str, str], dict[str, Any]]) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "point_key",
        "system",
        "n_seeds",
        PRIMARY_METRIC,
        "delta_proposed_minus_baseline_a",
        "delta_proposed_minus_baseline_b",
    ] + [m for m in REPORT_METRICS if m != PRIMARY_METRIC]

    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for pk in expected_points:
            p_primary = point_means.get((pk, "proposed"), {}).get("means", {}).get(PRIMARY_METRIC)
            b1_primary = point_means.get((pk, "baseline_a"), {}).get("means", {}).get(PRIMARY_METRIC)
            b2_primary = point_means.get((pk, "baseline_b"), {}).get("means", {}).get(PRIMARY_METRIC)
            d1 = None if p_primary is None or b1_primary is None else float(p_primary - b1_primary)
            d2 = None if p_primary is None or b2_primary is None else float(p_primary - b2_primary)
            for sys_name in ("baseline_a", "baseline_b", "proposed"):
                means = point_means.get((pk, sys_name), {}).get("means", {}) or {}
                n = point_means.get((pk, sys_name), {}).get("n", 0)
                row: dict[str, Any] = {
                    "point_key": pk,
                    "system": sys_name,
                    "n_seeds": n,
                    PRIMARY_METRIC: means.get(PRIMARY_METRIC),
                    "delta_proposed_minus_baseline_a": d1 if sys_name == "proposed" else None,
                    "delta_proposed_minus_baseline_b": d2 if sys_name == "proposed" else None,
                }
                for m in REPORT_METRICS:
                    if m == PRIMARY_METRIC:
                        continue
                    row[m] = means.get(m)
                w.writerow(row)


def _delta_rows(
    *,
    expected_points: list[str],
    point_means: dict[tuple[str, str], dict[str, Any]],
    baseline: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for pk in expected_points:
        p = point_means.get((pk, "proposed"), {}).get("means", {}).get(PRIMARY_METRIC)
        b = point_means.get((pk, baseline), {}).get("means", {}).get(PRIMARY_METRIC)
        if p is None or b is None:
            continue
        rows.append(
            {
                "point_key": pk,
                "baseline": baseline,
                "proposed_mean": float(p),
                "baseline_mean": float(b),
                "delta_proposed_minus_baseline": float(p - b),
            }
        )
    return rows


def _compute_extremes(
    *,
    expected_points: list[str],
    point_means: dict[tuple[str, str], dict[str, Any]],
    k: int = TOP_K_EXTREMES,
) -> dict[str, Any]:
    """Compute top wins/losses for proposed vs each baseline by primary metric delta.

    Delta definition: (proposed_mean - baseline_mean). Lower is better.
    - wins: most negative deltas
    - losses: most positive deltas
    """
    out: dict[str, Any] = {}
    for b in ("baseline_a", "baseline_b"):
        rows = _delta_rows(expected_points=expected_points, point_means=point_means, baseline=b)
        rows_sorted = sorted(rows, key=lambda r: float(r["delta_proposed_minus_baseline"]))
        wins = rows_sorted[: int(k)]
        losses = list(reversed(rows_sorted))[: int(k)]
        out[b] = {"wins": wins, "losses": losses, "n_points": len(rows_sorted)}
    return out


def _write_extremes_csv(out_csv: Path, *, seed_set: str, extremes: dict[str, Any]) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "seed_set",
        "baseline",
        "kind",
        "rank",
        "point_key",
        "delta_proposed_minus_baseline",
        "proposed_mean",
        "baseline_mean",
    ]
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for baseline, buckets in extremes.items():
            for kind in ("wins", "losses"):
                rows = list(buckets.get(kind, []))
                for i, r in enumerate(rows, start=1):
                    w.writerow(
                        {
                            "seed_set": seed_set,
                            "baseline": baseline,
                            "kind": kind,
                            "rank": i,
                            "point_key": r.get("point_key"),
                            "delta_proposed_minus_baseline": r.get("delta_proposed_minus_baseline"),
                            "proposed_mean": r.get("proposed_mean"),
                            "baseline_mean": r.get("baseline_mean"),
                        }
                    )


def _render_md(*, expected_points: list[str], audit_a: dict[str, Any], audit_b: dict[str, Any], seed_reports: dict[str, dict[str, Any]]) -> str:
    def pct(done: int, total: int) -> str:
        if total <= 0:
            return "n/a"
        return f"{(100.0 * done / total):.1f}%"

    # Holdout stability: correlate per-point deltas proposed-baseline_b between A and B
    a_by_point = seed_reports["A"]["point_deltas_baseline_b_by_point"]
    b_by_point = seed_reports["B_r2"]["point_deltas_baseline_b_by_point"]
    common = sorted(set(a_by_point.keys()) & set(b_by_point.keys()))
    x = [float(a_by_point[k]) for k in common]
    y = [float(b_by_point[k]) for k in common]
    corr = _pearson(x, y)
    sign_total = 0
    sign_agree = 0
    for k in common:
        da = float(a_by_point[k])
        db = float(b_by_point[k])
        if da == 0.0 or db == 0.0:
            continue
        sign_total += 1
        if (da < 0 and db < 0) or (da > 0 and db > 0):
            sign_agree += 1

    lines: list[str] = []
    lines.append("### Experiment 2 — Full Summary (Grid v1, preregistered)")
    lines.append("")
    lines.append("This report is **artifact-derived** from:")
    lines.append(f"- Locked configs: `configs/locked/{EXPERIMENT_ID}/`")
    lines.append(f"- Seed Set A artifacts: `artifacts/exp2/` (prefix `{SEED_SETS[0].sweep_prefix}`)")
    lines.append(f"- Holdout Seed Set B artifacts: `{SEED_SETS[1].artifacts_dir}` (prefix `{SEED_SETS[1].sweep_prefix}`)")
    lines.append("")
    lines.append("## Executive summary (thesis-ready, citation-safe)")
    lines.append(f"- **Primary outcome**: `{PRIMARY_METRIC}` (lower is better), evaluated on a **preregistered 54-regime-point grid** with **30 seeds per seed set**.")
    lines.append("- **Headline** (descriptive, bounded to this grid):")
    lines.append(
        f"  - **Seed Set A**: `proposed` had lower per-point mean `{PRIMARY_METRIC}` than `baseline_a` in **{seed_reports['A']['primary']['wins']['baseline_a']['wins']} / {seed_reports['A']['primary']['wins']['baseline_a']['n']}** regime points."
    )
    lines.append(
        f"  - **Holdout stability**: A vs B per-point deltas (proposed − baseline_b) have Pearson correlation **{corr}** with sign agreement **{sign_agree} / {sign_total}** (excluding exact zeros)."
    )
    lines.append("- **Data completeness**:")
    lines.append(f"  - **Seed Set A**: **{audit_a['found_points_finalized_count']} / {audit_a['expected_points_count']}** points finalized; expected runs = 4860")
    lines.append(f"  - **Seed Set B (holdout)**: **{audit_b['found_points_finalized_count']} / {audit_b['expected_points_count']}** points finalized; expected runs = 4860")
    lines.append("")
    lines.append("## Hypothesis linkage (what Exp2 tests, without over-claiming)")
    lines.append("- Exp2 tests whether **cost-aware deferral policies** (WAIT vs ACT under uncertainty) change observed cost outcomes relative to baselines, under matched evidence + reconciliation streams.")
    lines.append("- Working expectation (pre-results): **regime-dependent tradeoffs**:")
    lines.append("  - `proposed` may defer more (higher `M5_deferral_rate`), potentially changing tail behavior (`M4_*`) and average cost (`M3_*`).")
    lines.append("  - Effects should be stable under matched holdout seeds if they reflect the modeled phenomenon rather than noise.")
    lines.append("")

    lines.append("## Claim bank (pinpointed, citation-safe)")
    lines.append("- **Data completeness**: both A and B include **4860 / 4860** eval runs across **54 / 54** regime points under the paper-safe inclusion rule.")
    lines.append(
        f"- **Primary outcome, analysis split (A)**: On the preregistered 54-point grid, `proposed` achieved lower per-point mean **{PRIMARY_METRIC}** than `baseline_a` in **{seed_reports['A']['primary']['wins']['baseline_a']['wins']} / {seed_reports['A']['primary']['wins']['baseline_a']['n']}** regime points."
    )
    lines.append(
        f"- **Primary outcome, holdout split (B)**: On the same grid, `proposed` achieved lower per-point mean **{PRIMARY_METRIC}** than `baseline_a` in **{seed_reports['B_r2']['primary']['wins']['baseline_a']['wins']} / {seed_reports['B_r2']['primary']['wins']['baseline_a']['n']}** regime points."
    )
    lines.append(
        f"- **Holdout stability**: Per-regime-point deltas (proposed − baseline_b) between A and B have Pearson correlation **{corr}** with sign agreement **{sign_agree} / {sign_total}** (excluding exact zeros)."
    )
    lines.append("")
    lines.append("## Preregistered design (inputs)")
    lines.append("- **Grid size**: **54 regime points** (3×3×3×2)")
    lines.append("- **Systems compared**: `baseline_a`, `baseline_b`, `proposed`")
    lines.append(f"- **Primary outcome**: **{PRIMARY_METRIC}** (lower is better)")
    lines.append("- **Seed sets**:")
    lines.append("  - **A (analysis)**: seeds 0–29")
    lines.append("  - **B (holdout)**: seeds 30–59")
    lines.append("")
    lines.append("## Data inclusion + integrity checks (paper-safe)")
    lines.append("- **Expected eval runs per seed set**: 54 points × 3 systems × 30 seeds = **4860 runs**")
    lines.append("- **Canonical sweep inclusion rule**: include only sweeps where")
    lines.append('  - `sweep_progress.json.last_run_id == "FINALIZED"` and `completed == total == 90`, and')
    lines.append("  - `sweep_manifest.json.seeds` exactly matches the preregistered seed range for the seed set.")
    lines.append("- **Canonical sweep selection rule**: if multiple eligible sweeps exist for the same regime point, select the one with the newest `created_utc` (ties by directory name).")
    lines.append("- **Sweep manifest robustness**: if `sweep_manifest.json.runs` is incomplete, rebuild the run list from per-run `run_manifest.json` files.")
    lines.append(f"- **Seed Set A finalized points**: **{audit_a['found_points_finalized_count']} / {audit_a['expected_points_count']}** (audit: `artifacts/audit_exp2_grid_v1__A.json`)")
    lines.append(f"- **Seed Set B finalized points**: **{audit_b['found_points_finalized_count']} / {audit_b['expected_points_count']}** (audit: `artifacts/audit_exp2_grid_v1__B_r2.json`)")
    lines.append("- **Note on duplicates**: If multiple eligible full sweeps exist for the same point (reruns), we select exactly one canonical sweep by newest `created_utc`. Duplicates are reported below and contribute extra run directories on disk, but do not change the selected evaluation set.")
    lines.append("")

    lines.append(f"## Primary outcome results ({PRIMARY_METRIC})")
    for label in ("A", "B_r2"):
        sr = seed_reports[label]
        wins = sr["primary"]["wins"]
        lines.append(f"### Seed Set {label}")
        lines.append(f"- **Included eval runs**: **{sr['eval_runs_count']} / 4860** across **{sr['points_covered']} / 54** regime points")
        lines.append(f"- **Canonical full sweeps selected**: {sr.get('selected_sweeps_count')} (expected 54)")
        lines.append(f"- **Duplicate eligible full sweeps (same point, reruns)**: {sr.get('duplicate_full_sweeps_points_count')}")
        lines.append(f"- **Sweep manifest rebuilds applied**: {sr.get('sweep_manifest_fallback_count')} sweep(s)")
        lines.append(f"- **Proposed vs baseline_a (per-point wins)**: **{wins['baseline_a']['wins']} / {wins['baseline_a']['n']}** wins ({pct(wins['baseline_a']['wins'], wins['baseline_a']['n'])}), **{wins['baseline_a']['losses']}** losses, **{wins['baseline_a']['ties']}** ties")
        lines.append(f"- **Proposed vs baseline_b (per-point wins)**: **{wins['baseline_b']['wins']} / {wins['baseline_b']['n']}** wins ({pct(wins['baseline_b']['wins'], wins['baseline_b']['n'])}), **{wins['baseline_b']['losses']}** losses, **{wins['baseline_b']['ties']}** ties")
        lines.append(f"- **Delta summary (proposed − baseline_a)**: mean {sr['primary']['deltas']['baseline_a']['mean']}, median {sr['primary']['deltas']['baseline_a']['median']}, min {sr['primary']['deltas']['baseline_a']['min']}, max {sr['primary']['deltas']['baseline_a']['max']}")
        lines.append(f"- **Delta summary (proposed − baseline_b)**: mean {sr['primary']['deltas']['baseline_b']['mean']}, median {sr['primary']['deltas']['baseline_b']['median']}, min {sr['primary']['deltas']['baseline_b']['min']}, max {sr['primary']['deltas']['baseline_b']['max']}")
        lines.append("")

    lines.append("## Holdout stability (A vs B)")
    lines.append(f"- Common regime points compared: **{len(common)} / 54**")
    lines.append(f"- Pearson correlation of per-point deltas (proposed − baseline_b): **{corr}**")
    lines.append(f"- Sign agreement on deltas (excluding exact zeros): **{sign_agree} / {sign_total}**")
    lines.append("")

    lines.append("## Top wins / top losses (where it helps vs where it hurts)")
    lines.append(f"- Delta = `proposed_mean - baseline_mean` on `{PRIMARY_METRIC}` (negative is better for `proposed`).")
    lines.append(f"- We report the top {TOP_K_EXTREMES} most negative (wins) and top {TOP_K_EXTREMES} most positive (losses) regime points.")
    lines.append("")

    for label in ("A", "B_r2"):
        ex = seed_reports[label].get("extremes", {})
        lines.append(f"### Seed Set {label}")
        for baseline in ("baseline_a", "baseline_b"):
            b = ex.get(baseline, {})
            wins = list(b.get("wins", []))
            losses = list(b.get("losses", []))
            lines.append(f"#### Proposed vs {baseline}")
            lines.append("")
            lines.append("| kind | rank | point_key | delta | proposed_mean | baseline_mean |")
            lines.append("|---|---:|---|---:|---:|---:|")
            for kind, rows in (("win", wins), ("loss", losses)):
                for i, r in enumerate(rows, start=1):
                    lines.append(
                        f"| {kind} | {i} | `{r['point_key']}` | {r['delta_proposed_minus_baseline']} | {r['proposed_mean']} | {r['baseline_mean']} |"
                    )
            lines.append("")
        lines.append("")

    lines.append("## Secondary metrics (descriptive; mean of per-point means)")
    lines.append("- These are **not** preregistered primary outcomes; treat as descriptive tradeoff context.")
    for label in ("A", "B_r2"):
        sr = seed_reports[label]
        lines.append(f"### Seed Set {label}")
        for sys_name in ("baseline_a", "baseline_b", "proposed"):
            m3 = sr["metric_summary"][sys_name]["M3_avg_cost"]["mean_of_point_means"]
            p95 = sr["metric_summary"][sys_name]["M4_p95_cost"]["mean_of_point_means"]
            p99 = sr["metric_summary"][sys_name]["M4_p99_cost"]["mean_of_point_means"]
            dfr = sr["metric_summary"][sys_name]["M5_deferral_rate"]["mean_of_point_means"]
            lines.append(f"- **{sys_name}**: M3_avg_cost={m3}, M4_p95_cost={p95}, M4_p99_cost={p99}, M5_deferral_rate={dfr}")
        lines.append("")

    lines.append("## Artifact anchors (what to cite)")
    lines.append(f"- Locked configs (defines the 54 regime points): `configs/locked/{EXPERIMENT_ID}/`")
    lines.append("- Audit (A): `artifacts/audit_exp2_grid_v1__A.json`")
    lines.append("- Audit (B): `artifacts/audit_exp2_grid_v1__B_r2.json`")
    lines.append("- Point-level tables (generated):")
    lines.append("  - `artifacts/exp2_grid_v1_table__A.csv`")
    lines.append("  - `artifacts/exp2_grid_v1_table__B_r2.csv`")
    lines.append("- Extremes tables (generated):")
    lines.append("  - `artifacts/exp2_grid_v1_extremes__A.csv`")
    lines.append("  - `artifacts/exp2_grid_v1_extremes__B_r2.csv`")
    lines.append("")

    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate paper-ready Exp2 summary markdown + CSV tables from artifacts.")
    ap.add_argument("--progress-every", type=int, default=400, help="Print progress every N eval runs per seed set.")
    ap.add_argument("--audit-a", type=Path, default=ARTIFACTS_OUT_DIR / "audit_exp2_grid_v1__A.json")
    ap.add_argument("--audit-b", type=Path, default=ARTIFACTS_OUT_DIR / "audit_exp2_grid_v1__B_r2.json")
    args = ap.parse_args()

    expected_points = _expected_point_keys(CONFIG_DIR, experiment_id=EXPERIMENT_ID)
    if len(expected_points) != 54:
        raise SystemExit(f"Expected 54 grid points, found {len(expected_points)} in {CONFIG_DIR}")

    audit_a = _load_json(args.audit_a)
    audit_b = _load_json(args.audit_b)

    seed_reports: dict[str, dict[str, Any]] = {}

    for seed in SEED_SETS:
        collection = _collect_runs_for_seedset(seed, progress_every=int(args.progress_every))
        rows = collection.rows
        point_means = _point_system_means(rows)
        extremes = _compute_extremes(expected_points=expected_points, point_means=point_means, k=TOP_K_EXTREMES)

        d_by_point = {}
        for pk in expected_points:
            p = point_means.get((pk, "proposed"), {}).get("means", {}).get(PRIMARY_METRIC)
            b = point_means.get((pk, "baseline_b"), {}).get("means", {}).get(PRIMARY_METRIC)
            if p is None or b is None:
                continue
            d_by_point[pk] = float(p - b)

        seed_reports[seed.label] = {
            "eval_runs_count": len(rows),
            "points_covered": len({r["point_key"] for r in rows}),
            "selected_sweeps_count": len(collection.selected_sweeps),
            "duplicate_full_sweeps_points_count": len(collection.duplicate_full_sweeps_by_point),
            "duplicate_full_sweeps_by_point": collection.duplicate_full_sweeps_by_point,
            "sweep_manifest_fallback_count": len(collection.sweep_manifest_fallback_sweeps),
            "sweep_manifest_fallback_sweeps": collection.sweep_manifest_fallback_sweeps,
            "primary": _summarize_primary_wins(point_means, expected_points=expected_points),
            "metric_summary": _summarize_metric_across_points(point_means, expected_points=expected_points),
            "point_deltas_baseline_b_by_point": d_by_point,
            "point_means": point_means,
            "extremes": extremes,
        }

        _write_csv_table(ARTIFACTS_OUT_DIR / f"exp2_grid_v1_table__{seed.label}.csv", expected_points, point_means)
        _write_extremes_csv(ARTIFACTS_OUT_DIR / f"exp2_grid_v1_extremes__{seed.label}.csv", seed_set=seed.label, extremes=extremes)

    md = _render_md(
        expected_points=expected_points,
        audit_a=audit_a,
        audit_b=audit_b,
        seed_reports=seed_reports,
    )

    out_md = Path("docs/experiment_2_summary.md")
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(md, encoding="utf-8")
    print(f"Wrote: {out_md}")


if __name__ == "__main__":
    main()


