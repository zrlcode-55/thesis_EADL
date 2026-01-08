## Guardrails (Anti-Overfitting / Anti-“Hammer the Tests”)

This project explicitly separates **building correctness** from **optimizing outcomes**.

### Two-phase workflow

- **DEV phase**: used to validate mechanics
  - schemas, determinism, artifact integrity, baseline fairness
  - small configs, quick runs
  - allowed to change code/config freely

- **EVAL phase**: used to measure outcomes
  - uses **locked configs** (predeclared)
  - requires clean artifact generation from CLI
  - results are derived from artifacts only

### Locked config convention

- Store evaluation configs under `configs/locked/`.
- A locked config should not be edited after running evaluation sweeps. If it must change, create a new file with a new ID and record why.

### Run integrity rules (enforced)

- Every run writes to a **unique run directory**.
- A run fails if the output directory already exists (prevents accidental overwrite).
- `run_manifest.json` is written **last**; its presence implies completeness.
- The manifest records a **config hash** so the exact config is identifiable even if a file is renamed.

### Journal requirement (human discipline)

- Maintain `post_runner.md` as a running log of:
  - hypotheses before runs
  - observations after runs (with run IDs + artifact pointers)
  - any assumption/config/code changes (with rationale)
  - what remained fixed

### What we do *not* do

- No manual “fixing” of artifacts.
- No changing the evaluation config grid after seeing outcomes without explicitly bumping the sweep ID and documenting the change.

### Metric recomputation rule (versioned, no overwrite)

If metric code changes after runs exist, recompute by writing **versioned** metrics files (e.g., `metrics_recomputed.json`) rather than overwriting `metrics.json`. Summaries must record which metrics file they used.


