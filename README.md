# Experiment Suite — Decision-Making Under Delayed Reconciliation

**Zachary Larkin** | Vanderbilt CS Master's Thesis


---

## What this is

This repo contains the full experimental apparatus for my thesis on timing decisions in distributed systems where evidence is conflicting and reconciliation arrives late. The central question: if multiple data sources disagree, and you know the ground truth will eventually arrive but not yet, when do you act versus wait?

I built three state-tracking semantics (two baselines, one proposed) and four decision policies, then ran them through controlled synthetic scenarios across three experiments measuring when waiting helps and when it doesn't.

The short answer: the proposed method wins about 2/3 of tested regimes and loses the other 1/3. That's the result. This repo has the code and artifacts to back it up — and to audit every number.

---

## For the committee

If you're here to evaluate the thesis, start with **`docs/final_claims.md`**. Every claim in the thesis (C1–C13) lives there, anchored to either an artifact file or a specific function in the source. The experiment summary docs (`docs/experiment1_full_summary.md`, `docs/experiment_2_policy_summary__v2_policy.md`, `docs/experiment3_full_summary.md`) are what fed into those claims — they were generated deterministically from on-disk sweep results via the scripts in `scripts/`.

To audit a specific claim: look up C1–C13 in `final_claims.md`, find the evidence anchor (artifact path or code path), and go there. For artifact files, check `artifacts/`. For code paths, check `src/exp_suite/`.

---

## The three experiments

**Experiment 1** (54 regime points, preregistered grid): Does conflict-aware state tracking reduce decision regret versus baselines that collapse to a single value? On 39/54 points (Seed Set A) and 36/54 (Seed Set B), yes. On the remaining 15/18 points, no — specifically in high-conflict, low-false-act-cost regimes where acting fast beats being careful. The result isn't cherry-picked; these are the preregistered 54-point grid results.

**Experiment 2** (12 wait-cost points × 4 policies): Which timing policy wins across different wait-cost regimes when semantics are fixed? `always_act` wins all 12 points on both seed sets. The other policies pay too much for deferring. This is important context for Exp1 — the semantics alone don't determine policy performance, the cost structure matters.

**Experiment 3** (48 sweeps = 12 base points × 4 shock types): Do policies hold up under time-varying cost shocks? Yes — holdout stability stays above r=0.999. The identity shock (no-op) reduces exactly to Exp2, which is the correctness gate. Step shocks at 10× produce the largest tail amplification. One known limitation: in this sweep, all cost components scale together, which makes `risk_threshold` boundaries invariant to shocks. That's a design choice, not a fundamental flaw, and it's documented in C12 of `final_claims.md`.

---

## Repository structure

```
configs/locked/          preregistered, immutable experiment configs (TOML)
  exp1_grid_v1/          162 configs (54 regime points × 3 systems)
  exp2_policy_v2_16pt/   48 configs (12 wait-cost points × 4 policies)
  exp3_shock_v1_48sweeps/ 192 configs (12 base × 4 shocks × 4 policies)

artifacts/               in-repo summaries and audit files (not raw sweep dirs)
  audit_*.json
  exp1_grid_v1_table__*.csv
  exp3_shock_v1_*

docs/
  final_claims.md                       ← single source of truth for all claims
  experiment1_full_summary.md
  experiment_2_policy_summary__v2_policy.md
  experiment3_full_summary.md
  dependencies.md

scripts/                 summary generators + PowerShell sweep runners
src/exp_suite/           the Python package (see below)
tests/                   sanity checks
```

The raw sweep directories for Exp2 and Exp3 are **not committed** — they're 10s of GB of Parquet files. They live at `C:\exp2_policy_v2_16pt_artifacts` and `C:\exp3_shock_v1_48sweeps_artifacts`. The in-repo `artifacts/` directory has the summary CSVs and JSONs derived from those sweeps, which is what `docs/final_claims.md` references.

---

## Source layout (`src/exp_suite/`)

The package is CLI-first: every experiment run goes through `exp-suite` commands, writes Parquet + JSON artifacts to disk, and all analysis reads those artifacts back. Nothing computed in analysis scripts that isn't derived from artifacts.

- `workload.py` — synthetic evidence stream generator (conflict rate, delay families, missingness)
- `state.py` / `state_view.py` — the three semantics: baseline_a (last by event time), baseline_b (last by receipt time), proposed (all unique values)
- `decisions.py` — four policies: always_act, always_wait, wait_on_conflict, risk_threshold
- `reconciliation.py` — ground-truth outcome labels + arrival times
- `metrics.py` — M1–M9 and E3 metrics, all derived from artifacts
- `shocks.py` — Exp3 time-varying shock schedules (identity, step, impulse, ramp)
- `runner.py` — single-run orchestrator; writes manifest last as a completeness signal
- `sweep.py` — sweep-level aggregation with bootstrap CIs
- `cli.py` — all CLI commands
- `config.py` — Pydantic schemas for the TOML configs
- `grid.py` — locked config generation for each experiment grid
- `manifest.py` / `artifacts.py` — manifest JSON + artifact write utilities

---

## Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .

exp-suite version
```

Developed on Windows 10/11. The Python code itself is platform-agnostic; the sweep runner scripts (`scripts/run_exp*.ps1`) are PowerShell.

### Regenerating the experiment summaries

```powershell
python scripts/generate_exp1_paper_summary.py
python scripts/generate_exp2_policy_summary.py
python scripts/analyze_exp3_results.py
```

These read from external artifact directories for Exp2/Exp3. If you're on a different machine, you'll need those directories or equivalent sweep outputs.

---

## Tests

```powershell
pytest tests/
```

These are sanity checks, not a comprehensive test suite. They cover: proposed semantics exposing conflict_size > 1, identity shock being a no-op, Exp2/Exp3 event inheritance from matched seeds, and sweep aggregation correctness.

---

## Reproducibility

Every run writes a `run_manifest.json` as its final artifact — its presence signals completeness. All locked configs under `configs/locked/` are immutable post-execution. The inclusion rules in the summary scripts are deterministic and documented in-code (e.g., `scripts/generate_exp1_paper_summary.py` around line 107). Seed Set A (seeds 0–29) and Seed Set B (seeds 30–59) were split upfront; Set B wasn't touched until Set A was finalized.

There are a couple known imperfections: one Exp1 sweep was rerun after the initial run, and one sweep had an incomplete manifest. Both are handled with documented deterministic selection rules (newest `created_utc`, ties broken by directory name). See `docs/experiment1_full_summary.md` for specifics.

---

## Contact

Zach Larkin — zachary.larkin@vanderbilt.edu


