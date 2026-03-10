from __future__ import annotations

from pathlib import Path
from typing import Any

import typer

from exp_suite.artifacts import (
    ensure_dir,
    sha256_file,
    write_empty_parquet,
    write_json,
    write_parquet_table,
)
import json
import hashlib

from exp_suite.config import Exp1Config, Exp2Config, Exp3Config, load_config_toml
from exp_suite.decisions import generate_exp1_decisions
from exp_suite.manifest import build_run_manifest
from exp_suite.metrics import compute_exp1_metrics, compute_exp2_metrics, compute_exp3_metrics
from exp_suite.reconciliation import generate_exp1_reconciliation
from exp_suite.schemas import decision_schema, evidence_set_schema, event_schema, reconciliation_schema
from exp_suite.state import summarize_state
from exp_suite.workload import generate_exp1_events


def execute_run(
    *,
    config_path: Path,
    seed: int,
    out_dir: Path,
    run_id: str,
) -> dict[str, Any]:
    """Execute one run and return the run manifest dict.

    This is the single source of truth used by both `exp-suite run` and `exp-suite sweep`.
    """
    cfg = load_config_toml(config_path)

    run_root = out_dir / run_id
    if run_root.exists():
        raise typer.BadParameter(f"Run directory already exists (refusing to overwrite): {run_root}")
    ensure_dir(run_root)

    # Guardrail: evaluation configs must live under configs/locked/
    if getattr(cfg, "phase", "dev") == "eval":
        config_str = str(config_path).replace("\\", "/")
        if "/configs/locked/" not in f"/{config_str}":
            raise typer.BadParameter(
                "EVAL phase requires configs under configs/locked/ (predeclared, not edited after runs)."
            )

    paths = {
        "events": str((run_root / "events.parquet").as_posix()),
        "decisions": str((run_root / "decisions.parquet").as_posix()),
        "evidence_sets": str((run_root / "evidence_sets.parquet").as_posix()),
        "reconciliation": str((run_root / "reconciliation.parquet").as_posix()),
        "metrics": str((run_root / "metrics.json").as_posix()),
        "state_summary": str((run_root / "state_summary.json").as_posix()),
        "manifest": str((run_root / "run_manifest.json").as_posix()),
    }

    def _canonical_sha256(d: dict[str, Any]) -> str:
        b = json.dumps(d, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(b).hexdigest()

    if isinstance(cfg, Exp1Config):
        events = generate_exp1_events(cfg, seed=seed)
        write_parquet_table(Path(paths["events"]), events)

        reconciliation = generate_exp1_reconciliation(events, cfg, seed=seed)
        write_parquet_table(Path(paths["reconciliation"]), reconciliation)

        events_df = events.to_pandas()
        summary = summarize_state(events_df, semantics=cfg.system)
        write_json(Path(paths["state_summary"]), summary.__dict__)

        dec = generate_exp1_decisions(events, cfg, seed=seed, policy=cfg.policy)
        write_parquet_table(Path(paths["decisions"]), dec.decisions)
        write_parquet_table(Path(paths["evidence_sets"]), dec.evidence_sets)

        metrics = compute_exp1_metrics(
            decisions=dec.decisions,
            evidence_sets=dec.evidence_sets,
            reconciliation=reconciliation,
            cfg=cfg,
        )
        write_json(Path(paths["metrics"]), metrics)
    elif isinstance(cfg, Exp3Config):
        # Optional inheritance enforcement: ensures Exp3 config is explicitly tied to an Exp2 base.
        if getattr(cfg, "enforce_inheritance", False) and cfg.inherits_from_exp2_config_path and cfg.inherits_from_exp2_config_sha256:
            base_path = Path(cfg.inherits_from_exp2_config_path)
            if not base_path.is_absolute():
                # Interpret relative paths as relative to the repo working directory, not the config directory.
                base_path = (Path.cwd() / base_path).resolve()
            base_cfg = load_config_toml(base_path)
            if not isinstance(base_cfg, Exp2Config):
                raise typer.BadParameter(f"Exp3 inheritance expects an Exp2 config at: {base_path}")
            got = _canonical_sha256(base_cfg.model_dump())
            want = str(cfg.inherits_from_exp2_config_sha256)
            if got != want:
                raise typer.BadParameter(f"Exp3 inheritance mismatch: want {want}, got {got} (base={base_path})")

            # Stronger guardrail: ensure the Exp3 apparatus matches the inherited Exp2 config on all
            # shared fields (Exp3 is allowed to differ only in kind/experiment_id/notes and its shock/metadata).
            base_d = base_cfg.model_dump()
            cfg_d = cfg.model_dump()
            for k, v in base_d.items():
                if k in {"kind", "experiment_id", "notes"}:
                    continue
                if cfg_d.get(k) != v:
                    raise typer.BadParameter(
                        f"Exp3 inheritance violation on field '{k}': exp3={cfg_d.get(k)!r}, exp2={v!r} (base={base_path})"
                    )

        events = generate_exp1_events(cfg, seed=seed)  # type: ignore[arg-type]
        write_parquet_table(Path(paths["events"]), events)

        reconciliation = generate_exp1_reconciliation(events, cfg, seed=seed)  # type: ignore[arg-type]
        write_parquet_table(Path(paths["reconciliation"]), reconciliation)

        events_df = events.to_pandas()
        summary = summarize_state(events_df, semantics=cfg.system)
        write_json(Path(paths["state_summary"]), summary.__dict__)

        dec = generate_exp1_decisions(events, cfg, seed=seed, policy=cfg.policy)
        write_parquet_table(Path(paths["decisions"]), dec.decisions)
        write_parquet_table(Path(paths["evidence_sets"]), dec.evidence_sets)

        metrics = compute_exp3_metrics(
            decisions=dec.decisions,
            evidence_sets=dec.evidence_sets,
            reconciliation=reconciliation,
            cfg=cfg,
        )
        write_json(Path(paths["metrics"]), metrics)
    elif isinstance(cfg, Exp2Config):
        events = generate_exp1_events(cfg, seed=seed)  # type: ignore[arg-type]
        write_parquet_table(Path(paths["events"]), events)

        reconciliation = generate_exp1_reconciliation(events, cfg, seed=seed)  # type: ignore[arg-type]
        write_parquet_table(Path(paths["reconciliation"]), reconciliation)

        events_df = events.to_pandas()
        summary = summarize_state(events_df, semantics=cfg.system)
        write_json(Path(paths["state_summary"]), summary.__dict__)

        dec = generate_exp1_decisions(events, cfg, seed=seed, policy=cfg.policy)
        write_parquet_table(Path(paths["decisions"]), dec.decisions)
        write_parquet_table(Path(paths["evidence_sets"]), dec.evidence_sets)

        metrics = compute_exp2_metrics(
            decisions=dec.decisions,
            evidence_sets=dec.evidence_sets,
            reconciliation=reconciliation,
            cfg=cfg,
        )
        write_json(Path(paths["metrics"]), metrics)
    else:
        write_empty_parquet(Path(paths["events"]), event_schema())
        write_empty_parquet(Path(paths["reconciliation"]), reconciliation_schema())
        write_empty_parquet(Path(paths["decisions"]), decision_schema())
        write_empty_parquet(Path(paths["evidence_sets"]), evidence_set_schema())
        write_json(Path(paths["state_summary"]), {"status": "stub"})
        write_json(Path(paths["metrics"]), {"status": "stub", "metrics": {}})

    checksums = {
        "events.parquet": sha256_file(Path(paths["events"])),
        "decisions.parquet": sha256_file(Path(paths["decisions"])),
        "evidence_sets.parquet": sha256_file(Path(paths["evidence_sets"])),
        "reconciliation.parquet": sha256_file(Path(paths["reconciliation"])),
        "metrics.json": sha256_file(Path(paths["metrics"])),
        "state_summary.json": sha256_file(Path(paths["state_summary"])),
    }

    manifest = build_run_manifest(
        run_id=run_id,
        config=cfg.model_dump(),
        seed=seed,
        artifacts=paths,
        checksums=checksums,
        repo_root=Path(".").resolve(),
    )

    # Write manifest last: its presence implies artifact completeness.
    write_json(Path(paths["manifest"]), manifest)
    return manifest


