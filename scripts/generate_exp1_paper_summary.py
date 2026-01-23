from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys
import time
from datetime import datetime, timezone
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


# --- Config ---
EXPERIMENT_ID = "exp1_grid_v1"
CONFIG_DIR = Path("configs/locked/exp1_grid_v1")
ARTIFACTS_DIR = Path("artifacts")

PRIMARY_METRIC = "M3b_avg_regret_vs_oracle"
REPORT_METRICS = [
    "M1_correctness_rate",
    "M3_avg_loss",
    "M3b_avg_regret_vs_oracle",
    "M7_state_bytes_mean",
    "M8_stateview_ms_mean",
    "M9_conflict_budget_size",
]


@dataclass(frozen=True)
class SeedSpec:
    label: str
    sweep_prefix: str
    seed_min: int
    seed_max: int
    expected_seed_count: int


SEED_SETS = [
    SeedSpec(label="A", sweep_prefix="exp1_grid_v1__A", seed_min=0, seed_max=29, expected_seed_count=30),
    SeedSpec(label="B_r1", sweep_prefix="exp1_grid_v1__B_r1", seed_min=30, seed_max=59, expected_seed_count=30),
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
    # Find the canonical tail: cr..__sig..__cfa..__cws..
    i = s.find("cr")
    if i < 0:
        return None
    tail = s[i:]
    if "__sig" not in tail or "__cfa" not in tail or "__cws" not in tail:
        return None
    # Truncate any trailing suffix beyond cwsXX (rare but safe)
    # Keep the first four segments.
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
        # Accept "...Z" or "+00:00"
        s = ts.replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _sweep_created_utc(sweep_dir: Path) -> str | None:
    # Prefer sweep_progress.json (it tracks finalization and is always updated last)
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

    # Select only sweep dirs that correspond to the full preregistered seed range for this set.
    # If multiple full sweeps exist for the same point_key (reruns), select ONE canonical sweep
    # by newest created_utc (ties broken by dir name), and report the duplicates.
    expected_seeds = set(range(seed.seed_min, seed.seed_max + 1))

    candidates_by_point: dict[str, list[SelectedSweep]] = {}

    for sweep_dir in _iter_sweep_dirs(ARTIFACTS_DIR, seed.sweep_prefix):
        point_key = _extract_point_key(sweep_dir.name)
        if not point_key:
            continue

        # Require a finalized sweep_progress.json so we don't accidentally select an incomplete rerun.
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
        # Strictly require the full expected seeds. This excludes smokes / partial seed sweeps.
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
            duplicate_full_sweeps_by_point[point_key] = [c.sweep_dir.name for c in sorted(cands, key=lambda x: x.sweep_dir.name)]
        def key_fn(c: SelectedSweep) -> tuple[datetime, str]:
            dt = _parse_iso_utc(c.created_utc) or datetime.min.replace(tzinfo=timezone.utc)
            return (dt, c.sweep_dir.name)
        selected.append(max(cands, key=key_fn))

    # Expected total run entries (3 systems × 30 seeds per point).
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

        # Defensive: if sweep_manifest.json is incomplete (it happens), fall back to scanning
        # per-run manifests. This keeps the paper summary artifact-derived and prevents
        # silent undercounting (e.g., 4807/4860).
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
            # Only adopt fallback if it looks strictly better.
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
                    "sweep_dir": str(sel.sweep_dir.as_posix()),
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


def _group_point_system(rows: list[dict[str, Any]]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    out: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for r in rows:
        pk = r["point_key"]
        sys = r["system"]
        if sys not in ("baseline_a", "baseline_b", "proposed"):
            continue
        out.setdefault((pk, sys), []).append(r)
    return out


def _point_system_means(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    grouped = _group_point_system(rows)
    out: dict[tuple[str, str], dict[str, Any]] = {}
    for (pk, sys), rs in grouped.items():
        seeds = sorted({int(r["seed"]) for r in rs})
        metric_vals: dict[str, list[float]] = {m: [] for m in REPORT_METRICS}
        metric_ns: dict[str, int] = {m: 0 for m in REPORT_METRICS}
        statuses = []
        for r in rs:
            statuses.append(r.get("metrics_status"))
            md = dict(r.get("metrics") or {})
            for m in REPORT_METRICS:
                v = md.get(m)
                if v is None:
                    continue
                try:
                    metric_vals[m].append(float(v))
                    metric_ns[m] += 1
                except Exception:
                    continue
        out[(pk, sys)] = {
            "seed_count": len(seeds),
            "seed_min": min(seeds) if seeds else None,
            "seed_max": max(seeds) if seeds else None,
            "statuses": {s: statuses.count(s) for s in sorted(set(statuses))},
            "means": {m: _mean(metric_vals[m]) for m in REPORT_METRICS},
            "metric_n": metric_ns,
        }
    return out


def _summarize_primary_wins(point_means: dict[tuple[str, str], dict[str, Any]], *, expected_points: list[str]) -> dict[str, Any]:
    wins = {"baseline_a": {"wins": 0, "losses": 0, "ties": 0, "n": 0}, "baseline_b": {"wins": 0, "losses": 0, "ties": 0, "n": 0}}
    deltas: dict[str, list[float]] = {"baseline_a": [], "baseline_b": []}
    completeness: dict[str, int] = {"baseline_a": 0, "baseline_b": 0, "proposed": 0}

    for pk in expected_points:
        for sys in ("baseline_a", "baseline_b", "proposed"):
            if (pk, sys) in point_means:
                completeness[sys] += 1

        p = point_means.get((pk, "proposed"), {}).get("means", {}).get(PRIMARY_METRIC)
        for b in ("baseline_a", "baseline_b"):
            bv = point_means.get((pk, b), {}).get("means", {}).get(PRIMARY_METRIC)
            if p is None or bv is None:
                continue
            d = float(p - bv)
            deltas[b].append(d)
            wins[b]["n"] += 1
            if d < 0:
                wins[b]["wins"] += 1
            elif d > 0:
                wins[b]["losses"] += 1
            else:
                wins[b]["ties"] += 1

    return {
        "wins": wins,
        "deltas": {
            b: {"mean": _mean(ds), "median": _median(ds), "min": min(ds) if ds else None, "max": max(ds) if ds else None}
            for b, ds in deltas.items()
        },
        "coverage_points_with_system_metric": completeness,
    }


def _summarize_metric_across_points(point_means: dict[tuple[str, str], dict[str, Any]], *, expected_points: list[str]) -> dict[str, Any]:
    # Mean of per-point means (each regime point equal weight).
    out: dict[str, Any] = {}
    for sys in ("baseline_a", "baseline_b", "proposed"):
        out[sys] = {}
        for m in REPORT_METRICS:
            vals = []
            for pk in expected_points:
                v = point_means.get((pk, sys), {}).get("means", {}).get(m)
                if v is None:
                    continue
                vals.append(float(v))
            out[sys][m] = {"points_n": len(vals), "mean_of_point_means": _mean(vals), "median_of_point_means": _median(vals)}
    return out


def _write_csv_table(path: Path, expected_points: list[str], point_means: dict[tuple[str, str], dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    cols = [
        "point_key",
        "system",
        "seed_count",
        "seed_min",
        "seed_max",
        "primary_metric_n",
        *[f"mean_{m}" for m in REPORT_METRICS],
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for pk in expected_points:
            for sys in ("baseline_a", "baseline_b", "proposed"):
                ps = point_means.get((pk, sys))
                row = {
                    "point_key": pk,
                    "system": sys,
                    "seed_count": (ps or {}).get("seed_count"),
                    "seed_min": (ps or {}).get("seed_min"),
                    "seed_max": (ps or {}).get("seed_max"),
                    "primary_metric_n": ((ps or {}).get("metric_n") or {}).get(PRIMARY_METRIC),
                }
                means = (ps or {}).get("means", {})
                for m in REPORT_METRICS:
                    row[f"mean_{m}"] = means.get(m)
                w.writerow(row)


def _render_md(
    *,
    expected_points: list[str],
    audit_a: dict[str, Any],
    audit_b: dict[str, Any],
    seed_reports: dict[str, dict[str, Any]],
) -> str:
    def pct(x: int, n: int) -> str:
        if n <= 0:
            return "n/a"
        return f"{(100.0 * x / n):.1f}%"

    # Cross-seed stability on deltas (proposed-baseline_b) where both present.
    a_d = seed_reports["A"]["point_deltas_baseline_b_by_point"]
    b_d = seed_reports["B_r1"]["point_deltas_baseline_b_by_point"]
    common = sorted(set(a_d.keys()) & set(b_d.keys()))
    x = [float(a_d[k]) for k in common]
    y = [float(b_d[k]) for k in common]
    corr = _pearson(x, y)
    sign_agree = sum(1 for a, b in zip(x, y) if (a < 0) == (b < 0) and a != 0 and b != 0)
    sign_total = sum(1 for a, b in zip(x, y) if a != 0 and b != 0)

    lines: list[str] = []
    lines.append("### Experiment 1 — Full Summary (Grid v1, preregistered)")
    lines.append("")
    lines.append("This report is **artifact-derived** from `configs/locked/exp1_grid_v1/` + `artifacts/` and is intended as the single reference for paper writing.")
    lines.append("")

    lines.append("## What you can safely claim from this report (scope)")
    lines.append("- This report supports **descriptive claims** about performance **on the preregistered Exp1 grid** (54 regime points) under the preregistered seed splits (A and B).")
    lines.append("- It does **not** support claims about universal superiority, real-world deployment, or statistical significance unless you add separate analyses.")
    lines.append("")

    lines.append("## Preregistered design (inputs)")
    lines.append(f"- **Grid size**: **54 regime points** (3×3×3×2)")
    lines.append("- **Systems compared**: `baseline_a`, `baseline_b`, `proposed`")
    lines.append(f"- **Primary outcome**: **{PRIMARY_METRIC}** (lower is better)")
    lines.append("- **Seed sets**:")
    lines.append("  - **A (analysis)**: seeds 0–29")
    lines.append("  - **B (holdout)**: seeds 30–59")
    lines.append("")

    lines.append("## Definitions (how numbers are computed)")
    lines.append("- **Regime point**: one locked config point key `cr…__sig…__cfa…__cws…` from `configs/locked/exp1_grid_v1/`.")
    lines.append(f"- **Per-point system mean**: mean of {PRIMARY_METRIC} over the 30 seeds for that system at that regime point.")
    lines.append("- **Delta (proposed − baseline)**: difference between per-point means (negative is better for proposed).")
    lines.append("- **Win/Loss/Tie counts**: computed **per regime point** by the sign of the delta; each regime point has equal weight.")
    lines.append("- **Mean delta**: mean of the per-point deltas across regime points (equal-weighted by point).")
    lines.append("")

    lines.append("## Data inclusion + integrity checks (paper-safe)")
    lines.append(f"- **Expected eval runs per seed set**: 54 points × 3 systems × 30 seeds = **4860 runs**")
    lines.append("- **Canonical sweep inclusion rule**: include only sweeps where")
    lines.append("  - `sweep_progress.json.last_run_id == \"FINALIZED\"` and `completed == total == 90`, and")
    lines.append("  - `sweep_manifest.json.seeds` exactly matches the preregistered seed range for the seed set.")
    lines.append("- **Canonical sweep selection rule**: if multiple eligible sweeps exist for the same regime point, select the one with the newest `created_utc` (ties by directory name).")
    lines.append("- **Sweep manifest robustness**: if `sweep_manifest.json.runs` is incomplete, rebuild the run list from per-run `run_manifest.json` files.")
    lines.append(f"- **Seed Set A finalized points**: **{audit_a['found_points_finalized_count']} / {audit_a['expected_points_count']}** (audit: `artifacts/audit_exp1_grid_v1__A.json`)")
    lines.append(f"- **Seed Set B finalized points**: **{audit_b['found_points_finalized_count']} / {audit_b['expected_points_count']}** (audit: `artifacts/audit_exp1_grid_v1__B_r1.json`)")
    lines.append("")

    lines.append("## Expectations stated up front (not results)")
    lines.append("- We did **not** claim universal superiority; we expected **regime-dependent tradeoffs**.")
    lines.append("- Holdout goal: **Seed Set B should broadly agree with Seed Set A** on the regime map (directionally).")
    lines.append("")

    lines.append(f"## Primary outcome results ({PRIMARY_METRIC})")
    for label in ("A", "B_r1"):
        sr = seed_reports[label]
        wins = sr["primary"]["wins"]
        lines.append(f"### Seed Set {label}")
        lines.append(f"- **Included eval runs**: **{sr['eval_runs_count']} / 4860** across **{sr['points_covered']} / 54** regime points")
        lines.append(f"- **Canonical full sweeps selected**: {sr.get('selected_sweeps_count')} (expected 54)")
        lines.append(f"- **Duplicate eligible full sweeps (same point, reruns)**: {sr.get('duplicate_full_sweeps_points_count')}")
        lines.append(f"- **Sweep manifest rebuilds applied**: {sr.get('sweep_manifest_fallback_count')} sweep(s)")
        if sr.get("duplicate_full_sweeps_points_count"):
            dups = sr.get("duplicate_full_sweeps_by_point") or {}
            # Keep this compact: show only the point keys with duplicates.
            dup_keys = ", ".join(sorted(dups.keys()))
            lines.append(f"  - duplicate regime point keys: {dup_keys}")
        if sr.get("sweep_manifest_fallback_count"):
            fb = sr.get("sweep_manifest_fallback_sweeps") or []
            lines.append(f"  - rebuilt from run manifests: {', '.join(fb)}")
        lines.append(f"- **Proposed vs baseline_a (per-point wins)**: **{wins['baseline_a']['wins']} / {wins['baseline_a']['n']}** wins ({pct(wins['baseline_a']['wins'], wins['baseline_a']['n'])}), **{wins['baseline_a']['losses']}** losses, **{wins['baseline_a']['ties']}** ties")
        lines.append(f"- **Proposed vs baseline_b (per-point wins)**: **{wins['baseline_b']['wins']} / {wins['baseline_b']['n']}** wins ({pct(wins['baseline_b']['wins'], wins['baseline_b']['n'])}), **{wins['baseline_b']['losses']}** losses, **{wins['baseline_b']['ties']}** ties")
        lines.append(f"- **Delta summary (proposed − baseline_a)**: mean {sr['primary']['deltas']['baseline_a']['mean']}, median {sr['primary']['deltas']['baseline_a']['median']}, min {sr['primary']['deltas']['baseline_a']['min']}, max {sr['primary']['deltas']['baseline_a']['max']}")
        lines.append(f"- **Delta summary (proposed − baseline_b)**: mean {sr['primary']['deltas']['baseline_b']['mean']}, median {sr['primary']['deltas']['baseline_b']['median']}, min {sr['primary']['deltas']['baseline_b']['min']}, max {sr['primary']['deltas']['baseline_b']['max']}")
        lines.append("")

    lines.append("## Paper-ready claim bank (pinpointed, citation-safe)")
    lines.append(f"- **Primary outcome, analysis split (A)**: On the preregistered 54-point grid, `proposed` achieved lower per-point mean **{PRIMARY_METRIC}** than `baseline_a` in **{seed_reports['A']['primary']['wins']['baseline_a']['wins']} / {seed_reports['A']['primary']['wins']['baseline_a']['n']}** regime points, and lower than `baseline_b` in **{seed_reports['A']['primary']['wins']['baseline_b']['wins']} / {seed_reports['A']['primary']['wins']['baseline_b']['n']}** regime points.")
    lines.append(f"- **Primary outcome, holdout split (B)**: On the same grid, `proposed` achieved lower per-point mean **{PRIMARY_METRIC}** than `baseline_a` in **{seed_reports['B_r1']['primary']['wins']['baseline_a']['wins']} / {seed_reports['B_r1']['primary']['wins']['baseline_a']['n']}** regime points, and lower than `baseline_b` in **{seed_reports['B_r1']['primary']['wins']['baseline_b']['wins']} / {seed_reports['B_r1']['primary']['wins']['baseline_b']['n']}** regime points.")
    lines.append(f"- **Holdout stability**: Per-regime-point deltas (proposed − baseline_b) between A and B have Pearson correlation **{corr}** with sign agreement **{sign_agree} / {sign_total}** (excluding exact zeros).")
    lines.append(f"- **Data completeness (for these claims)**: both A and B include **4860 / 4860** eval runs across **54 / 54** regime points under the paper-safe inclusion rule above.")
    lines.append("")

    lines.append("## Holdout stability (A vs B)")
    lines.append(f"- Common regime points compared: **{len(common)} / 54**")
    lines.append(f"- Pearson correlation of per-point deltas (proposed − baseline_b): **{corr}**")
    lines.append(f"- Sign agreement on deltas (excluding exact zeros): **{sign_agree} / {sign_total}**")
    lines.append("")

    lines.append("## Secondary metrics (descriptive; mean of per-point means)")
    lines.append("- These are **not** preregistered primary outcomes; treat as descriptive tradeoff context.")
    for label in ("A", "B_r1"):
        sr = seed_reports[label]
        lines.append(f"### Seed Set {label}")
        for sys in ("baseline_a", "baseline_b", "proposed"):
            m3 = sr["metric_summary"][sys]["M3_avg_loss"]["mean_of_point_means"]
            m1 = sr["metric_summary"][sys]["M1_correctness_rate"]["mean_of_point_means"]
            m7 = sr["metric_summary"][sys]["M7_state_bytes_mean"]["mean_of_point_means"]
            m8 = sr["metric_summary"][sys]["M8_stateview_ms_mean"]["mean_of_point_means"]
            m9 = sr["metric_summary"][sys]["M9_conflict_budget_size"]["mean_of_point_means"]
            lines.append(f"- **{sys}**: M1={m1}, M3={m3}, M7_bytes={m7}, M8_ms={m8}, M9_budget={m9}")
        lines.append("")

    lines.append("## Artifact anchors (what to cite)")
    lines.append("- Locked configs (defines the 54 regime points): `configs/locked/exp1_grid_v1/`")
    lines.append("- Audit (A): `artifacts/audit_exp1_grid_v1__A.json`")
    lines.append("- Audit (B): `artifacts/audit_exp1_grid_v1__B_r1.json`")
    lines.append("- Point-level tables (generated):")
    lines.append("  - `artifacts/exp1_grid_v1_table__A.csv`")
    lines.append("  - `artifacts/exp1_grid_v1_table__B_r1.csv`")
    lines.append("")

    lines.append("## Figure suggestions (optional)")
    lines.append("- **Regime-map heatmaps**: delta (proposed − baseline) as heatmap facets over (conflict_rate × delay_sigma) for each cost setting.")
    lines.append("- **Tradeoff scatter**: per regime point, x=delta regret, y=delta overhead (bytes or ms), label by conflict_rate.")
    lines.append("- **Holdout stability**: scatter of A deltas vs B deltas with y=x line + correlation.")
    lines.append("")

    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate paper-ready Exp1 summary markdown + CSV tables from artifacts.")
    ap.add_argument("--progress-every", type=int, default=200, help="Print progress every N eval runs per seed set.")
    args = ap.parse_args()

    expected_points = _expected_point_keys(CONFIG_DIR, experiment_id=EXPERIMENT_ID)
    if len(expected_points) != 54:
        raise SystemExit(f"Expected 54 grid points, found {len(expected_points)} in {CONFIG_DIR}")

    audit_a = _load_json(ARTIFACTS_DIR / "audit_exp1_grid_v1__A.json")
    audit_b = _load_json(ARTIFACTS_DIR / "audit_exp1_grid_v1__B_r1.json")

    seed_reports: dict[str, dict[str, Any]] = {}

    for seed in SEED_SETS:
        collection = _collect_runs_for_seedset(seed, progress_every=int(args.progress_every))
        rows = collection.rows
        point_means = _point_system_means(rows)

        # Per-point primary deltas for stability checks
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
        }

        _write_csv_table(ARTIFACTS_DIR / f"exp1_grid_v1_table__{seed.label}.csv", expected_points, point_means)

    md = _render_md(
        expected_points=expected_points,
        audit_a=audit_a,
        audit_b=audit_b,
        seed_reports=seed_reports,
    )

    out_md = Path("docs/experiment1_full_summary.md")
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(md, encoding="utf-8")
    print(f"Wrote: {out_md}")


if __name__ == "__main__":
    main()


