# thesis_EADL — Experiment Suite (Repo Entry Point)

This repository is the **implementation scaffold** for an experimental suite studying **decision-making under delayed reconciliation** with competing state semantics (overwrite / eventual / exception-aware).

It intentionally separates:

- **Protocol (what we commit to measure)**: `readme_baseline.md`
- **Code (how we run and materialize artifacts)**: `src/exp_suite/`

No results live in this README.

---

## What to read first

- **Experimental protocol & preregistration**: `readme_baseline.md`
- **Dependency rationale**: `docs/dependencies.md`
- **Setup instructions (Windows/PowerShell)**: `docs/README_setup.md`

---

## Repository structure (high-level)

- **`src/exp_suite/`**: Python package + CLI (`exp-suite`) for reproducible runs
  - `cli.py`: CLI entrypoint (`exp-suite version`, `exp-suite run`, etc.)
  - `config.py`: TOML config loading + validation
  - `schemas.py`: Arrow/Parquet schemas for canonical artifacts
  - `artifacts.py`: artifact writing + checksums helpers
  - `manifest.py`: `run_manifest.json` creation (written last by design)
- **`configs/`**: example configurations (pre-execution)
- **`artifacts/`**: run outputs (gitignored)
- **`docs/`**: supporting documentation

---

## Artifact contract (what every run writes)

Each `exp-suite run` creates a unique run directory under `artifacts/` containing:

- `events.parquet`
- `decisions.parquet`
- `reconciliation.parquet`
- `metrics.json`
- `run_manifest.json` (**written last**) with config + seed + checksums

This is the foundation for the reproducibility contract described in `readme_baseline.md`.

---

## Quick start (stub run)

After setup (see `docs/README_setup.md`):

```powershell
exp-suite version
exp-suite run --config .\configs\example.toml --seed 0 --out .\artifacts
```

This run is a **contract test**: it validates config/schema handling and writes placeholder artifacts with declared schemas before we implement experiment semantics.

---

## Contributing / operating principles

- **CLI-first**: primary runs must be reproducible from the command line.
- **Artifact-first**: metrics/figures must be derivable from persisted artifacts.
- **Pre-registered definitions**: correctness/cost/overhead are defined in `readme_baseline.md` before results exist.
