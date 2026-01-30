from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import typer

from exp_suite import __version__
from exp_suite.artifacts import write_json
from exp_suite.grid import (
    generate_grid_configs,
    generate_exp2_grid_configs,
    generate_exp2_policy_sweep_configs,
    generate_exp3_shock_sweep_configs,
    group_grid_configs_by_point,
    group_exp2_policy_configs_by_point,
    group_exp3_shock_configs_by_point,
    summarize_grid_from_multiple_prefixes,
    summarize_grid_from_summaries,
)
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


@app.command(name="exp2-grid-generate")
def exp2_grid_generate_cmd(
    out_dir: Path = typer.Option(
        Path("configs/locked/exp2_grid_v1"),
        "--out-dir",
        help="Output directory for generated locked Exp2 grid configs.",
    ),
    base_config: Path = typer.Option(
        Path("configs/locked/exp2_eval_v1_baseline_a.toml"),
        "--base-config",
        exists=True,
        file_okay=True,
        dir_okay=False,
        help="Base locked exp2 config used as a template (will be overridden per system + regime axes).",
    ),
    experiment_id: str = typer.Option(
        "exp2_grid_v1",
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
    wait_cost_per_seconds: list[float] = typer.Option(
        [0.05, 0.10],
        "--wait-cost-per-second",
        help="Axis values for linear wait cost per second. Repeat to override defaults.",
    ),
) -> None:
    """Generate a preregistered regime grid of locked Exp2 eval configs (grid_v1)."""
    written = generate_exp2_grid_configs(
        base_config_path=base_config,
        out_dir=out_dir,
        experiment_id=experiment_id,
        systems=systems,
        conflict_rates=conflict_rates,
        delay_sigmas=delay_sigmas,
        cost_false_acts=cost_false_acts,
        wait_cost_per_seconds=wait_cost_per_seconds,
    )
    typer.echo(f"Wrote {len(written)} config files to: {out_dir}")


@app.command(name="exp2-policy-generate")
def exp2_policy_generate_cmd(
    out_dir: Path = typer.Option(
        Path("configs/locked/exp2_policy_v1"),
        "--out-dir",
        help="Output directory for generated locked Exp2 policy-sweep configs.",
    ),
    base_config: Path = typer.Option(
        Path("configs/locked/exp2_policy_v1_base.toml"),
        "--base-config",
        exists=True,
        file_okay=True,
        dir_okay=False,
        help="Base locked exp2 config used as a template (semantics + evidence regime kept fixed).",
    ),
    experiment_id: str = typer.Option(
        "exp2_policy_v1",
        "--experiment-id",
        help="Experiment id to write into generated configs (also used in filenames).",
    ),
    fixed_system: str = typer.Option(
        "proposed",
        "--fixed-system",
        help="State semantics system to hold fixed across all policies (preregistered Exp2 contract).",
    ),
    policy: list[str] = typer.Option(
        ["always_act", "always_wait", "wait_on_conflict", "risk_threshold"],
        "--policy",
        help="Policy variants to generate. Repeat --policy to override defaults.",
    ),
    linear_per_second: list[float] = typer.Option(
        [0.01, 0.05],
        "--linear-per-second",
        help="Linear wait-cost per-second coefficients (curvature axis). Repeat to override defaults.",
    ),
    quadratic_k: list[float] = typer.Option(
        [0.001, 0.01],
        "--quadratic-k",
        help="Quadratic wait-cost k coefficients (curvature axis). Repeat to override defaults.",
    ),
    exponential: list[str] = typer.Option(
        ["0.5,0.1", "1.0,0.1"],
        "--exponential",
        help="Exponential wait-cost parameter pairs 'k,alpha'. Repeat to override defaults.",
    ),
) -> None:
    """Generate locked Exp2 configs where state semantics are fixed and policy varies (plus wait-cost curvature)."""
    wait_cost_models = []
    for ps in linear_per_second:
        wait_cost_models.append({"family": "linear", "params": {"per_second": float(ps)}})
    for k in quadratic_k:
        wait_cost_models.append({"family": "quadratic", "params": {"k": float(k)}})
    for s in exponential:
        try:
            k_str, a_str = [x.strip() for x in str(s).split(",", maxsplit=1)]
            wait_cost_models.append({"family": "exponential", "params": {"k": float(k_str), "alpha": float(a_str)}})
        except Exception as e:
            raise typer.BadParameter(f"Invalid --exponential value '{s}'. Expected 'k,alpha'. Error: {e}") from e

    written = generate_exp2_policy_sweep_configs(
        base_config_path=base_config,
        out_dir=out_dir,
        experiment_id=experiment_id,
        fixed_system=fixed_system,
        policies=policy,
        wait_cost_models=wait_cost_models,
    )
    typer.echo(f"Wrote {len(written)} config files to: {out_dir}")


@app.command(name="exp3-shock-generate")
def exp3_shock_generate_cmd(
    out_dir: Path = typer.Option(
        Path("configs/locked/exp3_shock_v1"),
        "--out-dir",
        help="Output directory for generated locked Exp3 shock-sweep configs.",
    ),
    base_exp2_config: Path = typer.Option(
        Path("configs/locked/exp2_policy_v2_base.toml"),
        "--base-exp2-config",
        exists=True,
        file_okay=True,
        dir_okay=False,
        help="Base locked Exp2 config used as the inherited apparatus for Exp3 (default points to Exp2 policy v2 base).",
    ),
    exp2_policy_config_dir: Path | None = typer.Option(
        None,
        "--exp2-policy-config-dir",
        exists=True,
        file_okay=False,
        dir_okay=True,
        help=(
            "Optional directory of locked Exp2 policy-sweep configs to inherit regime points from "
            "(recommended for thesis lineage; e.g., configs/locked/exp2_policy_v2_16pt). "
            "If provided, Exp3 points become {exp2_point_key}__{shock_key}."
        ),
    ),
    exp2_policy_experiment_id: str | None = typer.Option(
        None,
        "--exp2-policy-experiment-id",
        help=(
            "Experiment id prefix for the Exp2 policy configs provided via --exp2-policy-config-dir "
            "(e.g., exp2_policy_v2_16pt). Required when --exp2-policy-config-dir is set."
        ),
    ),
    experiment_id: str = typer.Option(
        "exp3_shock_v1",
        "--experiment-id",
        help="Experiment id prefix used in generated config filenames.",
    ),
    fixed_system: str = typer.Option(
        "proposed",
        "--fixed-system",
        help="State semantics system to hold fixed across all policies (inherits Exp2 contract).",
    ),
    policy: list[str] = typer.Option(
        ["always_act", "always_wait", "wait_on_conflict", "risk_threshold"],
        "--policy",
        help="Policy variants to generate. Repeat --policy to override defaults.",
    ),
    shock_shape: list[str] = typer.Option(
        ["identity", "step", "impulse", "ramp"],
        "--shock-shape",
        help="Shock shapes to generate. Repeat to override defaults.",
    ),
    shock_magnitude: list[float] = typer.Option(
        [1.0, 2.0, 5.0, 10.0],
        "--shock-magnitude",
        help="Shock multipliers to generate. Repeat to override defaults.",
    ),
    shock_timing: list[str] = typer.Option(
        ["early", "late"],
        "--shock-timing",
        help="Timing labels mapped to start_frac. Allowed: early, late (repeatable).",
    ),
    shock_duration_frac: float = typer.Option(
        0.2,
        "--shock-duration-frac",
        min=0.0,
        max=1.0,
        help="Shock duration as a fraction of episode time in [0,1].",
    ),
    apply_to: list[str] = typer.Option(
        ["cost_false_act", "cost_false_wait", "wait_cost"],
        "--apply-to",
        help="Cost components to shock. Repeat to override defaults.",
    ),
    enforce_inheritance: bool = typer.Option(
        True,
        "--enforce-inheritance/--no-enforce-inheritance",
        help=(
            "If enabled, Exp3 runs will verify they inherit the exact Exp2 apparatus "
            "(base config hash pin + field equality on inherited fields)."
        ),
    ),
) -> None:
    """Generate locked Exp3 configs where Exp2 apparatus is inherited and only the shock schedule varies across points."""
    # Deterministic mapping for timing labels
    timing_map = {"early": 0.2, "late": 0.7}
    starts = []
    for t in shock_timing:
        if t not in timing_map:
            raise typer.BadParameter(f"Invalid --shock-timing '{t}'. Allowed: early, late.")
        starts.append(float(timing_map[t]))

    # Compute canonical sha256 of the base Exp2 config JSON (for optional inheritance enforcement).
    from exp_suite.config import load_config_toml, Exp2Config
    import hashlib
    import json

    base_cfg = load_config_toml(base_exp2_config)
    if not isinstance(base_cfg, Exp2Config):
        raise typer.BadParameter(f"--base-exp2-config must be kind=exp2: {base_exp2_config}")
    base_json = json.dumps(base_cfg.model_dump(), sort_keys=True, separators=(",", ":")).encode("utf-8")
    base_sha = hashlib.sha256(base_json).hexdigest()

    shock_models = []
    for shape in shock_shape:
        for mag in shock_magnitude:
            for start in starts:
                shock_models.append(
                    {
                        "shape": str(shape),
                        "magnitude": float(mag),
                        "start_frac": float(start),
                        "duration_frac": float(shock_duration_frac),
                        "apply_to": list(apply_to),
                    }
                )

    written = generate_exp3_shock_sweep_configs(
        base_exp2_config_path=base_exp2_config,
        out_dir=out_dir,
        experiment_id=experiment_id,
        fixed_system=fixed_system,
        policies=policy,
        shock_models=shock_models,
        exp2_policy_config_dir=exp2_policy_config_dir,
        exp2_policy_experiment_id=exp2_policy_experiment_id,
        inherits_from_path=str(base_exp2_config.as_posix()),
        inherits_from_sha256=str(base_sha),
        enforce_inheritance=bool(enforce_inheritance),
    )
    typer.echo(f"Wrote {len(written)} config files to: {out_dir}")


@app.command(name="exp3-verify-identity")
def exp3_verify_identity_cmd() -> None:
    """Gate: verify Exp3(identity shock) reduces exactly to Exp2 on key metrics.

    This is a fast, dependency-free check (no filesystem artifacts) intended to be run
    immediately before starting an official Exp3 sweep.
    """
    import json as _json

    import pyarrow as pa

    from exp_suite.config import DelayModel, Exp2Config, Exp3Config, ShockModel, WaitCostModel
    from exp_suite.metrics import compute_exp2_metrics, compute_exp3_metrics
    from exp_suite.schemas import decision_schema, evidence_set_schema, reconciliation_schema

    # Build tiny deterministic tables: 2 entities x 3 timepoints.
    evidence_rows = []
    decision_rows = []
    recon_rows = []
    for entity_id in ["e0", "e1"]:
        for t_idx in [0, 1, 2]:
            evid = f"es::{entity_id}::{t_idx}"
            decision_time = pa.scalar(1_700_000_000_000_000 + (t_idx * 1_000_000), type=pa.timestamp("us"))
            arrival_time = pa.scalar(1_700_000_000_000_000 + (t_idx * 1_000_000) + 30_000_000, type=pa.timestamp("us"))

            evidence_rows.append(
                {
                    "evidence_set_id": evid,
                    "entity_id": entity_id,
                    "t_idx": int(t_idx),
                    "decision_time": decision_time.as_py(),
                    "evidence_json": "[]",
                }
            )
            # Always ACT so deferral and churn are deterministic and easy to reason about.
            decision_rows.append(
                {
                    "decision_time": decision_time.as_py(),
                    "action_id": "ACT",
                    "evidence_set_id": evid,
                    "confidence": None,
                    "expected_cost": None,
                    "policy_id": "always_act",
                }
            )
            # Alternate outcomes so both false_act and false_wait are exercised.
            outcome = "ok" if (t_idx % 2 == 0) else "needs_act"
            recon_rows.append(
                {
                    "entity_id": entity_id,
                    "truth_window_start": decision_time.as_py(),
                    "truth_window_end": decision_time.as_py(),
                    "authoritative_outcome_json": _json.dumps({"outcome": outcome, "t_idx": int(t_idx)}),
                    "arrival_time": arrival_time.as_py(),
                }
            )

    decisions = pa.Table.from_pylist(decision_rows, schema=decision_schema())
    evidence_sets = pa.Table.from_pylist(evidence_rows, schema=evidence_set_schema())
    reconciliation = pa.Table.from_pylist(recon_rows, schema=reconciliation_schema())

    cfg2 = Exp2Config(
        phase="eval",
        experiment_id="exp3_verify_identity",
        system="proposed",
        variant="always_act",
        notes=None,
        entity_count=2,
        source_count=3,
        events_per_entity=3,
        conflict_rate=0.1,
        missingness=0.0,
        delay=DelayModel(family="fixed", params={"seconds": 0.0}),
        decision_lag_seconds=0.0,
        policy="always_act",
        cost_false_act=10.0,
        cost_false_wait=10.0,
        correctness_epsilon=0.0,
        wait_cost=WaitCostModel(family="linear", params={"per_second": 0.05}),
        reconciliation_lag_seconds=30.0,
        reconciliation_jitter=DelayModel(family="fixed", params={"seconds": 0.0}),
    )
    cfg3 = Exp3Config.model_validate(
        {
            **cfg2.model_dump(),
            "kind": "exp3",
            "shock": ShockModel(shape="identity", magnitude=1.0, start_frac=0.2, duration_frac=0.2).model_dump(),
        }
    )

    m2 = compute_exp2_metrics(decisions=decisions, evidence_sets=evidence_sets, reconciliation=reconciliation, cfg=cfg2)
    m3 = compute_exp3_metrics(decisions=decisions, evidence_sets=evidence_sets, reconciliation=reconciliation, cfg=cfg3)

    if m2.get("status") != "ok" or m3.get("status") != "ok":
        raise typer.BadParameter(f"Identity gate failed: statuses exp2={m2.get('status')} exp3={m3.get('status')}")

    keys = ["M3_avg_cost", "M4_p95_cost", "M4_p99_cost", "M5_deferral_rate", "M2_mean_wait_seconds_when_wait"]
    for k in keys:
        if m3["metrics"].get(k) != m2["metrics"].get(k):
            raise typer.BadParameter(f"Identity gate failed on {k}: exp3={m3['metrics'].get(k)} exp2={m2['metrics'].get(k)}")

    # Exp3 deltas under identity should be exactly baseline.
    if m3["metrics"].get("E3_delta_avg_cost_vs_noshock") != 0.0:
        raise typer.BadParameter(
            f"Identity gate failed: E3_delta_avg_cost_vs_noshock={m3['metrics'].get('E3_delta_avg_cost_vs_noshock')}"
        )
    if m3["metrics"].get("E3_p99_amplification") != 1.0:
        raise typer.BadParameter(
            f"Identity gate failed: E3_p99_amplification={m3['metrics'].get('E3_p99_amplification')}"
        )

    typer.echo("OK: Exp3 identity shock reduces to Exp2 on key metrics.")


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


@app.command(name="grid-summarize-multi")
def grid_summarize_multi_cmd(
    artifacts_dir: Path = typer.Option(
        Path("artifacts"),
        "--artifacts-dir",
        exists=True,
        file_okay=False,
        dir_okay=True,
        help="Artifacts root directory containing sweep_* dirs.",
    ),
    sweep_prefixes: list[str] = typer.Option(
        ...,
        "--sweep-prefix",
        help="Repeatable sweep-id prefix. Example: --sweep-prefix exp1_grid_v1__A_1h --sweep-prefix exp1_grid_v1__A_r3",
    ),
    out_json: Path = typer.Option(
        Path("artifacts/exp1_grid_v1_summary__A.json"),
        "--out-json",
        help="Output JSON file path for the combined grid summary artifact.",
    ),
    primary_metric: str = typer.Option(
        "M3b_avg_regret_vs_oracle",
        "--primary-metric",
        help="Primary metric used for win/loss counting (lower is better).",
    ),
) -> None:
    """Aggregate multiple sweep prefixes into one grid-level summary artifact (e.g., combine Seed Set A chunks)."""
    summary = summarize_grid_from_multiple_prefixes(
        artifacts_dir=artifacts_dir,
        sweep_prefixes=sweep_prefixes,
        out_json=out_json,
        primary_metric=primary_metric,
    )
    typer.echo(f"Wrote combined grid summary to: {out_json} (rows={len(summary.get('rows', []))})")


@app.command(name="grid-run")
def grid_run_cmd(
    config_dir: Path = typer.Option(
        Path("configs/locked/exp1_grid_v1"),
        "--config-dir",
        exists=True,
        file_okay=False,
        dir_okay=True,
        help="Directory containing generated grid_v1 configs.",
    ),
    experiment_id: str = typer.Option(
        "exp1_grid_v1",
        "--experiment-id",
        help="Experiment id prefix used in grid config filenames.",
    ),
    out_dir: Path = typer.Option(Path("artifacts"), "--out", help="Artifacts root directory."),
    sweep_prefix: str = typer.Option(
        "exp1_grid_v1__A",
        "--sweep-prefix",
        help='Sweep id prefix for per-point sweeps (e.g., "exp1_grid_v1__A" or "exp1_grid_v1__B").',
    ),
    seed_start: int = typer.Option(0, "--seed-start", min=0, help="Inclusive seed range start."),
    seed_end: int = typer.Option(29, "--seed-end", min=0, help="Inclusive seed range end."),
    start_index: int = typer.Option(
        0,
        "--start-index",
        min=0,
        help="Start index into the deterministically sorted regime-point list (for chunked execution).",
    ),
    limit_points: int | None = typer.Option(
        None,
        "--limit-points",
        min=1,
        help="Optional cap on number of regime points to run (for runtime-smoke).",
    ),
    resume: bool = typer.Option(
        True,
        "--resume/--no-resume",
        help="Resume-safe: skips only completed per-run dirs (requires run_manifest.json).",
    ),
    progress_every: int = typer.Option(10, "--progress-every", min=1, help="Write sweep_progress.json every N runs."),
) -> None:
    """Run the grid as a sequence of per-regime-point sweeps (baseline_a/baseline_b/proposed) with matched seeds."""
    groups = group_grid_configs_by_point(config_dir, experiment_id=experiment_id)
    if not groups:
        raise typer.BadParameter(f"No grid configs found under: {config_dir} (experiment_id={experiment_id})")

    point_keys = sorted(groups.keys())
    if start_index:
        if start_index >= len(point_keys):
            raise typer.BadParameter(f"--start-index {start_index} out of range (points={len(point_keys)})")
        point_keys = point_keys[int(start_index) :]
    if limit_points is not None:
        point_keys = point_keys[: int(limit_points)]

    seeds = list(range(int(seed_start), int(seed_end) + 1))
    if not seeds:
        raise typer.BadParameter("Empty seed set.")

    # For each regime point, run one sweep containing all systems.
    for point_key in point_keys:
        sys_map = groups[point_key]
        missing = [s for s in ("baseline_a", "baseline_b", "proposed") if s not in sys_map]
        if missing:
            raise typer.BadParameter(f"Regime point {point_key} missing systems: {missing}")

        sid = f"{sweep_prefix}__{point_key}"
        # Reuse the existing `sweep` command logic by invoking execute_run loop here would duplicate code;
        # instead, call `execute_run` directly to build a sweep dir identical to `sweep`.
        sweep_root = out_dir / f"sweep_{sid}"
        if sweep_root.exists():
            if not resume:
                raise typer.BadParameter(f"Sweep directory already exists: {sweep_root} (use --resume)")
            if (sweep_root / "sweep_manifest.json").exists():
                # Already finalized; skip.
                continue
        else:
            sweep_root.mkdir(parents=True, exist_ok=False)

        run_entries = []
        completed = 0
        total = 3 * len(seeds)

        def write_progress(last_run_id: str | None = None) -> None:
            write_json(
                sweep_root / "sweep_progress.json",
                {
                    "sweep_id": sid,
                    "created_utc": utc_now_iso(),
                    "git_rev": try_git_rev(Path(".").resolve()),
                    "configs": [str(sys_map[s].as_posix()) for s in ("baseline_a", "baseline_b", "proposed")],
                    "seeds": seeds,
                    "completed": completed,
                    "total": total,
                    "last_run_id": last_run_id,
                },
            )

        for sys_name in ("baseline_a", "baseline_b", "proposed"):
            cfg_path = sys_map[sys_name]
            for seed in seeds:
                run_id = f"sweep_{sid}__{cfg_path.stem}__seed{seed}"
                run_dir = sweep_root / run_id
                if run_dir.exists():
                    if (run_dir / "run_manifest.json").exists():
                        completed += 1
                        if completed % progress_every == 0:
                            write_progress(last_run_id=run_id)
                        continue
                    raise typer.BadParameter(
                        f"Found incomplete run directory (missing run_manifest.json): {run_dir}. "
                        "Delete it or choose a new sweep prefix."
                    )

                manifest = execute_run(config_path=cfg_path, seed=seed, out_dir=sweep_root, run_id=run_id)
                run_entries.append(
                    {
                        "run_id": manifest["run_id"],
                        "system": manifest["config"].get("variant") or manifest["config"].get("system"),
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
            "configs": [str(sys_map[s].as_posix()) for s in ("baseline_a", "baseline_b", "proposed")],
            "seeds": seeds,
            "runs": run_entries,
        }
        write_json(sweep_root / "sweep_manifest.json", sweep_manifest)
        write_progress(last_run_id="FINALIZED")
        typer.echo(f"Wrote sweep to: {sweep_root}")


@app.command(name="exp2-policy-run")
def exp2_policy_run_cmd(
    config_dir: Path = typer.Option(
        Path("configs/locked/exp2_policy_v1"),
        "--config-dir",
        exists=True,
        file_okay=False,
        dir_okay=True,
        help="Directory containing generated Exp2 policy-sweep configs.",
    ),
    experiment_id: str = typer.Option(
        "exp2_policy_v1",
        "--experiment-id",
        help="Experiment id prefix used in policy-sweep config filenames.",
    ),
    out_dir: Path = typer.Option(Path("artifacts/exp2_policy"), "--out", help="Artifacts root directory."),
    sweep_prefix: str = typer.Option(
        "exp2_policy_v1__A",
        "--sweep-prefix",
        help='Sweep id prefix for per-waitcost sweeps (e.g., "exp2_policy_v1__A" or "exp2_policy_v1__B").',
    ),
    seed_start: int = typer.Option(0, "--seed-start", min=0, help="Inclusive seed range start."),
    seed_end: int = typer.Option(29, "--seed-end", min=0, help="Inclusive seed range end."),
    start_index: int = typer.Option(
        0,
        "--start-index",
        min=0,
        help="Start index into the deterministically sorted wait-cost list (for chunked execution).",
    ),
    limit_points: int | None = typer.Option(
        None,
        "--limit-points",
        min=1,
        help="Optional cap on number of wait-cost points to run (for runtime-smoke).",
    ),
    policy: list[str] = typer.Option(
        ["always_act", "always_wait", "wait_on_conflict", "risk_threshold"],
        "--policy",
        help="Policy variants expected in each wait-cost point. Repeat to override defaults.",
    ),
    resume: bool = typer.Option(
        True,
        "--resume/--no-resume",
        help="Resume-safe: skips only completed per-run dirs (requires run_manifest.json).",
    ),
    progress_every: int = typer.Option(10, "--progress-every", min=1, help="Write sweep_progress.json every N runs."),
) -> None:
    """Run Exp2 as a sequence of per-waitcost sweeps with matched seeds across policy variants."""
    groups = group_exp2_policy_configs_by_point(config_dir, experiment_id=experiment_id)
    if not groups:
        raise typer.BadParameter(f"No policy configs found under: {config_dir} (experiment_id={experiment_id})")

    point_keys = sorted(groups.keys())
    if start_index:
        if start_index >= len(point_keys):
            raise typer.BadParameter(f"--start-index {start_index} out of range (points={len(point_keys)})")
        point_keys = point_keys[int(start_index) :]
    if limit_points is not None:
        point_keys = point_keys[: int(limit_points)]

    seeds = list(range(int(seed_start), int(seed_end) + 1))
    if not seeds:
        raise typer.BadParameter("Empty seed set.")

    for point_key in point_keys:
        pol_map = groups[point_key]
        missing = [p for p in policy if p not in pol_map]
        if missing:
            raise typer.BadParameter(f"Wait-cost point {point_key} missing policies: {missing}")

        sid = f"{sweep_prefix}__{point_key}"
        sweep_root = out_dir / f"sweep_{sid}"
        if sweep_root.exists():
            if not resume:
                raise typer.BadParameter(f"Sweep directory already exists: {sweep_root} (use --resume)")
            if (sweep_root / "sweep_manifest.json").exists():
                continue
        else:
            sweep_root.mkdir(parents=True, exist_ok=False)

        run_entries = []
        completed = 0
        total = len(policy) * len(seeds)

        def write_progress(last_run_id: str | None = None) -> None:
            write_json(
                sweep_root / "sweep_progress.json",
                {
                    "sweep_id": sid,
                    "created_utc": utc_now_iso(),
                    "git_rev": try_git_rev(Path(".").resolve()),
                    "configs": [str(pol_map[p].as_posix()) for p in policy],
                    "seeds": seeds,
                    "completed": completed,
                    "total": total,
                    "last_run_id": last_run_id,
                },
            )

        for pol in policy:
            cfg_path = pol_map[pol]
            for seed in seeds:
                run_id = f"sweep_{sid}__{cfg_path.stem}__seed{seed}"
                run_dir = sweep_root / run_id
                if run_dir.exists():
                    if (run_dir / "run_manifest.json").exists():
                        completed += 1
                        if completed % progress_every == 0:
                            write_progress(last_run_id=run_id)
                        continue
                    raise typer.BadParameter(
                        f"Found incomplete run directory (missing run_manifest.json): {run_dir}. "
                        "Delete it or choose a new sweep prefix."
                    )

                manifest = execute_run(config_path=cfg_path, seed=seed, out_dir=sweep_root, run_id=run_id)
                run_entries.append(
                    {
                        "run_id": manifest["run_id"],
                        "system": manifest["config"].get("variant") or manifest["config"].get("system"),
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
            "configs": [str(pol_map[p].as_posix()) for p in policy],
            "seeds": seeds,
            "runs": run_entries,
        }
        write_json(sweep_root / "sweep_manifest.json", sweep_manifest)
        write_progress(last_run_id="FINALIZED")
        typer.echo(f"Wrote sweep to: {sweep_root}")


@app.command(name="exp3-shock-run")
def exp3_shock_run_cmd(
    config_dir: Path = typer.Option(
        Path("configs/locked/exp3_shock_v1"),
        "--config-dir",
        exists=True,
        file_okay=False,
        dir_okay=True,
        help="Directory containing generated Exp3 shock-sweep configs.",
    ),
    experiment_id: str = typer.Option(
        "exp3_shock_v1",
        "--experiment-id",
        help="Experiment id prefix used in shock-sweep config filenames.",
    ),
    out_dir: Path = typer.Option(Path("artifacts/exp3_shock"), "--out", help="Artifacts root directory."),
    sweep_prefix: str = typer.Option(
        "exp3_shock_v1__A",
        "--sweep-prefix",
        help='Sweep id prefix for per-shock sweeps (e.g., "exp3_shock_v1__A" or "exp3_shock_v1__B").',
    ),
    seed_start: int = typer.Option(0, "--seed-start", min=0, help="Inclusive seed range start."),
    seed_end: int = typer.Option(29, "--seed-end", min=0, help="Inclusive seed range end."),
    start_index: int = typer.Option(
        0,
        "--start-index",
        min=0,
        help="Start index into the deterministically sorted shock point list (for chunked execution).",
    ),
    limit_points: int | None = typer.Option(
        None,
        "--limit-points",
        min=1,
        help="Optional cap on number of shock points to run (for runtime-smoke).",
    ),
    policy: list[str] = typer.Option(
        ["always_act", "always_wait", "wait_on_conflict", "risk_threshold"],
        "--policy",
        help="Policy variants expected in each shock point. Repeat to override defaults.",
    ),
    resume: bool = typer.Option(
        True,
        "--resume/--no-resume",
        help="Resume-safe: skips only completed per-run dirs (requires run_manifest.json).",
    ),
    progress_every: int = typer.Option(10, "--progress-every", min=1, help="Write sweep_progress.json every N runs."),
) -> None:
    """Run Exp3 as a sequence of per-shock sweeps with matched seeds across policy variants."""
    groups = group_exp3_shock_configs_by_point(config_dir, experiment_id=experiment_id)
    if not groups:
        raise typer.BadParameter(f"No Exp3 shock configs found under: {config_dir} (experiment_id={experiment_id})")

    point_keys = sorted(groups.keys())
    if start_index:
        if start_index >= len(point_keys):
            raise typer.BadParameter(f"--start-index {start_index} out of range (points={len(point_keys)})")
        point_keys = point_keys[int(start_index) :]
    if limit_points is not None:
        point_keys = point_keys[: int(limit_points)]

    seeds = list(range(int(seed_start), int(seed_end) + 1))
    if not seeds:
        raise typer.BadParameter("Empty seed set.")

    for point_key in point_keys:
        pol_map = groups[point_key]
        missing = [p for p in policy if p not in pol_map]
        if missing:
            raise typer.BadParameter(f"Shock point {point_key} missing policies: {missing}")

        sid = f"{sweep_prefix}__{point_key}"
        sweep_root = out_dir / f"sweep_{sid}"
        if sweep_root.exists():
            if not resume:
                raise typer.BadParameter(f"Sweep directory already exists: {sweep_root} (use --resume)")
            if (sweep_root / "sweep_manifest.json").exists():
                continue
        else:
            sweep_root.mkdir(parents=True, exist_ok=False)

        run_entries = []
        completed = 0
        total = len(policy) * len(seeds)

        def write_progress(last_run_id: str | None = None) -> None:
            write_json(
                sweep_root / "sweep_progress.json",
                {
                    "sweep_id": sid,
                    "created_utc": utc_now_iso(),
                    "git_rev": try_git_rev(Path(".").resolve()),
                    "configs": [str(pol_map[p].as_posix()) for p in policy],
                    "seeds": seeds,
                    "completed": completed,
                    "total": total,
                    "last_run_id": last_run_id,
                },
            )

        for pol in policy:
            cfg_path = pol_map[pol]
            for seed in seeds:
                run_id = f"sweep_{sid}__{cfg_path.stem}__seed{seed}"
                run_dir = sweep_root / run_id
                if run_dir.exists():
                    if (run_dir / "run_manifest.json").exists():
                        completed += 1
                        if completed % progress_every == 0:
                            write_progress(last_run_id=run_id)
                        continue
                    raise typer.BadParameter(
                        f"Found incomplete run directory (missing run_manifest.json): {run_dir}. "
                        "Delete it or choose a new sweep prefix."
                    )

                manifest = execute_run(config_path=cfg_path, seed=seed, out_dir=sweep_root, run_id=run_id)
                run_entries.append(
                    {
                        "run_id": manifest["run_id"],
                        "system": manifest["config"].get("variant") or manifest["config"].get("system"),
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
            "configs": [str(pol_map[p].as_posix()) for p in policy],
            "seeds": seeds,
            "runs": run_entries,
        }
        write_json(sweep_root / "sweep_manifest.json", sweep_manifest)
        write_progress(last_run_id="FINALIZED")
        typer.echo(f"Wrote sweep to: {sweep_root}")


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
                    "system": manifest["config"].get("variant") or manifest["config"].get("system"),
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
    from exp_suite.metrics import compute_exp1_metrics, compute_exp2_metrics

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
            kind = getattr(cfg, "kind", None)
            if kind not in {"exp1", "exp2"}:
                skipped += 1
                continue

            decisions = pq.read_table(run_dir / "decisions.parquet")
            evidence_sets = pq.read_table(run_dir / "evidence_sets.parquet")
            reconciliation = pq.read_table(run_dir / "reconciliation.parquet")

            if kind == "exp1":
                metrics = compute_exp1_metrics(
                    decisions=decisions,
                    evidence_sets=evidence_sets,
                    reconciliation=reconciliation,
                    cfg=cfg,  # type: ignore[arg-type]
                )
            else:
                metrics = compute_exp2_metrics(
                    decisions=decisions,
                    evidence_sets=evidence_sets,
                    reconciliation=reconciliation,
                    cfg=cfg,  # type: ignore[arg-type]
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


