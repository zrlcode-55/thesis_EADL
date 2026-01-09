from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import typer

from exp_suite import __version__
from exp_suite.artifacts import write_json
from exp_suite.grid import generate_grid_configs, summarize_grid_from_summaries
from exp_suite.manifest import try_git_rev, utc_now_iso
from exp_suite.runner import execute_run
from exp_suite.sweep import summarize_sweep

app = typer.Typer(no_args_is_help=True, add_completion=False)

@app.callback()
def main() -> None:
    """Experiment suite CLI (reproducible, CLI-first runs)."""


@app.command()
def version() -> None:
    """Print the installed experiment suite version."""
    typer.echo(__version__)


@app.command()
def run(
    config: Path = typer.Option(..., "--config", exists=True, file_okay=True, dir_okay=False),
    seed: int = typer.Option(0, "--seed", min=0, help="Deterministic seed recorded in the run manifest."),
    out_dir: Path = typer.Option(
        Path("artifacts"),
        "--out",
        help="Root artifacts directory (a unique run subdirectory will be created).",
    ),
    run_id: str | None = typer.Option(
        None,
        "--run-id",
        help="Optional explicit run id (otherwise generated).",
    ),
) -> None:
    """Run a single configuration and materialize artifacts."""
    rid = run_id or _default_run_id()
    manifest = execute_run(config_path=config, seed=seed, out_dir=out_dir, run_id=rid)
    typer.echo(f"Wrote run artifacts to: {Path(manifest['artifacts']['manifest']).parent}")

@app.command(name="grid-generate")
def grid_generate_cmd(
    out_dir: Path = typer.Option(
        Path("configs/locked/exp1_grid_v1"),
        "--out-dir",
        help="Output directory for generated locked grid configs.",
    ),
    base_config: Path = typer.Option(
        Path("configs/locked/exp1_eval_v2_overhead_baseline_a.toml"),
        "--base-config",
        exists=True,
        file_okay=True,
        dir_okay=False,
        help="Base locked exp1 config used as a template (will be overridden per system + regime axes).",
    ),
    experiment_id: str = typer.Option(
        "exp1_grid_v1",
        "--experiment-id",
        help="Experiment id to write into generated configs (also used in filenames).",
    ),
    systems: list[str] = typer.Option(
        ["baseline_a", "baseline_b", "proposed"],
        "--system",
        help="Systems to generate configs for. Repeat --system to override defaults.",
    ),
    conflict_rates: list[float] = typer.Option(
        [0.01, 0.10, 0.20],
        "--conflict-rate",
        help="Conflict rate axis values. Repeat --conflict-rate to override defaults.",
    ),
    delay_sigmas: list[float] = typer.Option(
        [0.25, 0.50, 1.00],
        "--delay-sigma",
        help="Lognormal sigma axis values. Repeat --delay-sigma to override defaults.",
    ),
    cost_false_acts: list[float] = typer.Option(
        [5.0, 10.0, 20.0],
        "--cost-false-act",
        help="Axis values for cost_false_act. Repeat to override defaults.",
    ),
    cost_wait_per_seconds: list[float] = typer.Option(
        [0.05, 0.10],
        "--cost-wait-per-second",
        help="Axis values for cost_wait_per_second. Repeat to override defaults.",
    ),
) -> None:
    """Generate a preregistered regime grid of locked Exp1 eval configs (grid_v1)."""
    written = generate_grid_configs(
        base_config_path=base_config,
        out_dir=out_dir,
        experiment_id=experiment_id,
        systems=systems,
        conflict_rates=conflict_rates,
        delay_sigmas=delay_sigmas,
        cost_false_acts=cost_false_acts,
        cost_wait_per_seconds=cost_wait_per_seconds,
    )
    typer.echo(f"Wrote {len(written)} config files to: {out_dir}")


@app.command(name="grid-summarize")
def grid_summarize_cmd(
    artifacts_dir: Path = typer.Option(
        Path("artifacts"),
        "--artifacts-dir",
        exists=True,
        file_okay=False,
        dir_okay=True,
        help="Artifacts root directory containing sweep_* dirs.",
    ),
    sweep_prefix: str = typer.Option(
        ...,
        "--sweep-prefix",
        help='Sweep id prefix to aggregate, e.g. "exp1_grid_v1__A" or "exp1_grid_v1__B".',
    ),
    out_json: Path = typer.Option(
        Path("artifacts/exp1_grid_v1_summary.json"),
        "--out-json",
        help="Output JSON file path for the grid summary artifact.",
    ),
    primary_metric: str = typer.Option(
        "M3b_avg_regret_vs_oracle",
        "--primary-metric",
        help="Primary metric used for win/loss counting (lower is better).",
    ),
) -> None:
    """Aggregate many sweep summaries into a single grid-level summary artifact."""
    summary = summarize_grid_from_summaries(
        artifacts_dir=artifacts_dir,
        sweep_prefix=sweep_prefix,
        out_json=out_json,
        primary_metric=primary_metric,
    )
    typer.echo(f"Wrote grid summary to: {out_json} (rows={len(summary.get('rows', []))})")


@app.command()
def sweep(
    configs: list[Path] = typer.Option(
        ...,
        "--config",
        exists=True,
        file_okay=True,
        dir_okay=False,
        help="Config file path. Repeat --config for multiple systems.",
    ),
    seeds: list[int] = typer.Option(
        [],
        "--seed",
        min=0,
        help="Seed value. Repeat --seed to build a matched-seed sweep (optional if using --seed-start/--seed-end).",
    ),
    seed_start: int | None = typer.Option(
        None,
        "--seed-start",
        min=0,
        help="Optional start of inclusive seed range (use with --seed-end).",
    ),
    seed_end: int | None = typer.Option(
        None,
        "--seed-end",
        min=0,
        help="Optional end of inclusive seed range (use with --seed-start).",
    ),
    out_dir: Path = typer.Option(Path("artifacts"), "--out", help="Artifacts root directory."),
    sweep_id: str | None = typer.Option(None, "--sweep-id", help="Optional explicit sweep id."),
    resume: bool = typer.Option(
        False,
        "--resume",
        help="Resume an existing sweep directory if present (skips completed run subdirs).",
    ),
    progress_every: int = typer.Option(
        10,
        "--progress-every",
        min=1,
        help="Write sweep_progress.json every N runs (and at the end).",
    ),
) -> None:
    """Run a matched-seed sweep across multiple configs and write sweep_manifest.json."""
    sid = sweep_id or _default_sweep_id()
    sweep_root = out_dir / f"sweep_{sid}"
    if sweep_root.exists():
        if not resume:
            raise typer.BadParameter(f"Sweep directory already exists: {sweep_root} (use --resume)")
        if (sweep_root / "sweep_manifest.json").exists():
            raise typer.BadParameter(f"Sweep already finalized (sweep_manifest.json exists): {sweep_root}")
    else:
        sweep_root.mkdir(parents=True, exist_ok=False)

    if seed_start is not None or seed_end is not None:
        if seed_start is None or seed_end is None:
            raise typer.BadParameter("Both --seed-start and --seed-end must be provided together.")
        if seed_end < seed_start:
            raise typer.BadParameter("--seed-end must be >= --seed-start.")
        seeds = list(range(int(seed_start), int(seed_end) + 1))

    if not seeds:
        raise typer.BadParameter("Provide at least one --seed or a --seed-start/--seed-end range.")

    run_entries = []
    completed = 0
    total = len(configs) * len(seeds)

    def write_progress(last_run_id: str | None = None) -> None:
        write_json(
            sweep_root / "sweep_progress.json",
            {
                "sweep_id": sid,
                "created_utc": utc_now_iso(),
                "git_rev": try_git_rev(Path(".").resolve()),
                "configs": [str(p.as_posix()) for p in configs],
                "seeds": seeds,
                "completed": completed,
                "total": total,
                "last_run_id": last_run_id,
            },
        )

    for cfg_path in configs:
        for seed in seeds:
            run_id = f"sweep_{sid}__{cfg_path.stem}__seed{seed}"
            run_dir = sweep_root / run_id
            if run_dir.exists():
                # Resume mode: only skip if the run manifest exists (completeness signal).
                if (run_dir / "run_manifest.json").exists():
                    completed += 1
                    if completed % progress_every == 0:
                        write_progress(last_run_id=run_id)
                    continue
                else:
                    raise typer.BadParameter(
                        f"Found incomplete run directory (missing run_manifest.json): {run_dir}. "
                        "Delete it or choose a new sweep id."
                    )

            manifest = execute_run(config_path=cfg_path, seed=seed, out_dir=sweep_root, run_id=run_id)
            run_entries.append(
                {
                    "run_id": manifest["run_id"],
                    "system": manifest["config"].get("system"),
                    "seed": manifest["seed"],
                    "config_sha256": manifest.get("config_sha256"),
                    "manifest_path": manifest["artifacts"]["manifest"],
                    "metrics_path": manifest["artifacts"]["metrics"],
                }
            )
            completed += 1
            if completed % progress_every == 0:
                write_progress(last_run_id=run_id)

    sweep_manifest = {
        "sweep_id": sid,
        "created_utc": utc_now_iso(),
        "git_rev": try_git_rev(Path(".").resolve()),
        "configs": [str(p.as_posix()) for p in configs],
        "seeds": seeds,
        "runs": run_entries,
    }
    write_json(sweep_root / "sweep_manifest.json", sweep_manifest)
    write_progress(last_run_id="FINALIZED")
    typer.echo(f"Wrote sweep to: {sweep_root}")


@app.command(name="summarize-sweep")
def summarize_sweep_cmd(
    sweep_dir: Path = typer.Option(
        ...,
        "--sweep-dir",
        exists=True,
        file_okay=False,
        dir_okay=True,
        help="Sweep directory containing sweep_manifest.json.",
    )
) -> None:
    """Summarize a sweep into sweep_summary.json (artifact-derived, no manual collation)."""
    summary = summarize_sweep(sweep_dir)
    out_path = sweep_dir / "sweep_summary.json"
    write_json(out_path, summary)
    typer.echo(f"Wrote sweep summary to: {out_path}")


@app.command(name="summarize-sweep-metrics")
def summarize_sweep_metrics_cmd(
    sweep_dir: Path = typer.Option(
        ...,
        "--sweep-dir",
        exists=True,
        file_okay=False,
        dir_okay=True,
        help="Sweep directory containing sweep_manifest.json.",
    ),
    metrics_file: str = typer.Option(
        "metrics.json",
        "--metrics-file",
        help="Metrics filename within each run directory (e.g., metrics_recomputed.json).",
    ),
) -> None:
    """Summarize a sweep using a specific per-run metrics filename."""
    summary = summarize_sweep(sweep_dir, metrics_filename=metrics_file)
    out_path = sweep_dir / f"sweep_summary__{metrics_file.replace('.json','')}.json"
    write_json(out_path, summary)
    typer.echo(f"Wrote sweep summary to: {out_path}")


@app.command(name="recompute-sweep-metrics")
def recompute_sweep_metrics_cmd(
    sweep_dir: Path = typer.Option(
        ...,
        "--sweep-dir",
        exists=True,
        file_okay=False,
        dir_okay=True,
        help="Sweep directory containing sweep_manifest.json.",
    ),
    out_metrics_file: str = typer.Option(
        "metrics_recomputed.json",
        "--out-metrics-file",
        help="Filename to write in each run directory (will not overwrite if already exists).",
    ),
) -> None:
    """Recompute per-run metrics from artifacts and write a versioned metrics file (no overwrite)."""
    import pyarrow.parquet as pq
    from pydantic import TypeAdapter

    from exp_suite.config import ExperimentConfig
    from exp_suite.metrics import compute_exp1_metrics

    sweep_manifest_path = sweep_dir / "sweep_manifest.json"
    if not sweep_manifest_path.exists():
        raise typer.BadParameter(f"Missing sweep_manifest.json at: {sweep_manifest_path}")

    sweep_manifest = json.loads(sweep_manifest_path.read_text(encoding="utf-8"))
    runs = list(sweep_manifest.get("runs", []))

    updated = 0
    skipped = 0
    failed = 0
    failures: list[dict[str, str]] = []

    for r in runs:
        run_id = r.get("run_id")
        if not run_id:
            continue
        run_dir = sweep_dir / run_id
        manifest_path = run_dir / "run_manifest.json"
        if not manifest_path.exists():
            failed += 1
            failures.append({"run_id": str(run_id), "reason": "missing run_manifest.json"})
            continue

        out_path = run_dir / out_metrics_file
        if out_path.exists():
            skipped += 1
            continue

        try:
            man = json.loads(manifest_path.read_text(encoding="utf-8"))
            cfg = TypeAdapter(ExperimentConfig).validate_python(man["config"])
            if getattr(cfg, "kind", None) != "exp1":
                skipped += 1
                continue

            decisions = pq.read_table(run_dir / "decisions.parquet")
            evidence_sets = pq.read_table(run_dir / "evidence_sets.parquet")
            reconciliation = pq.read_table(run_dir / "reconciliation.parquet")

            metrics = compute_exp1_metrics(
                decisions=decisions,
                evidence_sets=evidence_sets,
                reconciliation=reconciliation,
                cfg=cfg,
            )
            write_json(out_path, metrics)
            updated += 1
        except Exception as e:
            failed += 1
            failures.append({"run_id": str(run_id), "reason": str(e)})

    report = {
        "sweep_id": sweep_manifest.get("sweep_id"),
        "out_metrics_file": out_metrics_file,
        "updated": updated,
        "skipped": skipped,
        "failed": failed,
        "failures": failures[:20],
    }
    write_json(sweep_dir / "metrics_recompute_manifest.json", report)
    typer.echo(f"Recomputed metrics: updated={updated} skipped={skipped} failed={failed}")



def _default_run_id() -> str:
    # Timestamp prefix is human sortable; UUID keeps uniqueness without relying on randomness for semantics.
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{ts}_{uuid.uuid4().hex[:8]}"


def _default_sweep_id() -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{ts}_{uuid.uuid4().hex[:6]}"


