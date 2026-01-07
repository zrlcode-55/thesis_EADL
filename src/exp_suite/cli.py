from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

import typer

from exp_suite import __version__
from exp_suite.artifacts import ensure_dir, sha256_file, write_empty_parquet, write_json
from exp_suite.config import load_config_toml
from exp_suite.manifest import build_run_manifest
from exp_suite.schemas import decision_schema, event_schema, reconciliation_schema

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
    """Run a single configuration and materialize artifacts (stub: writes empty Parquet with schemas)."""
    cfg = load_config_toml(config)

    rid = run_id or _default_run_id()
    run_root = out_dir / rid
    ensure_dir(run_root)

    # Artifact paths
    paths = {
        "events": str((run_root / "events.parquet").as_posix()),
        "decisions": str((run_root / "decisions.parquet").as_posix()),
        "reconciliation": str((run_root / "reconciliation.parquet").as_posix()),
        "metrics": str((run_root / "metrics.json").as_posix()),
        "manifest": str((run_root / "run_manifest.json").as_posix()),
    }

    # Write core artifacts first (manifest is written last by design).
    write_empty_parquet(Path(paths["events"]), event_schema())
    write_empty_parquet(Path(paths["decisions"]), decision_schema())
    write_empty_parquet(Path(paths["reconciliation"]), reconciliation_schema())
    write_json(Path(paths["metrics"]), {"status": "stub", "metrics": {}})

    checksums = {
        "events.parquet": sha256_file(Path(paths["events"])),
        "decisions.parquet": sha256_file(Path(paths["decisions"])),
        "reconciliation.parquet": sha256_file(Path(paths["reconciliation"])),
        "metrics.json": sha256_file(Path(paths["metrics"])),
    }

    manifest = build_run_manifest(
        run_id=rid,
        config=cfg.model_dump(),
        seed=seed,
        artifacts=paths,
        checksums=checksums,
        repo_root=Path(".").resolve(),
    )

    # Write manifest last: its presence implies artifact completeness.
    write_json(Path(paths["manifest"]), manifest)
    typer.echo(f"Wrote run artifacts to: {run_root}")


def _default_run_id() -> str:
    # Timestamp prefix is human sortable; UUID keeps uniqueness without relying on randomness for semantics.
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{ts}_{uuid.uuid4().hex[:8]}"


