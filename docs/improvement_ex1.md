## Experiment 1 Improvement Plan (Top-Tier, No-Bias, Committee-Defensible)

Purpose: upgrade Experiment 1 from “single-regime comparison” to a **pre-registered cost characterization** over a finite, locked regime grid—without changing the thesis target or allowing outcome-driven tuning.

This plan is written so a reviewer can answer:
- **What was decided before seeing results?**
- **What can change, and what cannot?**
- **How can I reproduce every number from artifacts only?**

---

## 1) Scope: what stays targeted (does NOT change)

- **Decision layer**: pre-commit action under delayed reconciliation (ACT vs WAIT).
- **Truth source**: reconciliation outcome labels (authoritative outcome in `reconciliation.parquet`).
- **Evaluation**: decision-theoretic loss + regret vs oracle (primary outcomes); overhead/conflict-budget (feasibility outcomes).
- **Systems compared**: `baseline_a`, `baseline_b` (receipt-time LWW), `proposed`.
- **Artifacts**: per-run immutable artifacts + manifests; sweep manifests + summaries.

This plan expands only the **parameter regimes** (controlled variation), not the research question.

---

## 2) Core claim we are trying to earn (framing that survives scrutiny)

We are *not* claiming universal superiority. We are aiming for a defensible characterization:

> Exception-aware (conflict-preserving) state changes the information available to decision policies. Under delayed reconciliation, it can reduce expected decision cost / regret in identifiable regimes, at a measurable feasibility cost (conflict budget + overhead). We map where it helps, where it hurts, and why.

This is a “systems cost characterization” result, not a benchmark contest.

---

## 3) Pre-registered evaluation contract (grid_v1)

### 3.1 Primary endpoint (locked)

- **Primary metric**: **M3b_avg_regret_vs_oracle** (lower is better)
- **Secondary metrics**:
  - **M3_avg_loss**
  - **M7_state_bytes_mean**
  - **M8_stateview_ms_mean**
  - **M9_conflict_budget_size**

### 3.2 Policy (locked)

- **Primary policy**: `risk_threshold` (formal expected-loss boundary)
- Optional additional policy (separately versioned): `wait_on_conflict` (heuristic baseline)

No new policies may be introduced in `grid_v1` after seeing results. Any new policy becomes `grid_v2`.

### 3.3 Regime grid axes (locked before EVAL)

Grid axes should be small enough to run, but broad enough to show boundaries.

**Recommended minimal `grid_v1` (runtime-aware)**:
- **conflict_rate**: `[0.01, 0.10, 0.20]`  (3)
- **delay.lognormal.sigma**: `[0.25, 0.50, 1.00]` (3)
- **cost ratio** (implemented by scaling `cost_false_act` holding `cost_false_wait` fixed):
  - `cost_false_wait = 10.0`
  - `cost_false_act = {5.0, 10.0, 20.0}`  (3)
- **cost_wait_per_second**: `[0.05, 0.10]` (2)

Total regime points: \(3 \times 3 \times 3 \times 2 = 54\).

If runtime is too high, reduce **one axis** (do not prune points based on observed results). Example runtime cut:
- drop `cost_wait_per_second` axis → 27 points.

### 3.4 Fixed parameters (locked)

These remain fixed across all regime points:
- `entity_count`, `source_count`, `events_per_entity`
- reconciliation mechanism and jitter model
- event generator structure (only parameters above vary)
- metric implementation (versioned by git rev)
- overhead thresholds/sampling limits (use v2_overhead locked values)

---

## 4) Anti-bias protocol (DEV vs EVAL + holdout seeds)

### 4.1 DEV phase (allowed exploration, not citable)

Goal: pick the grid axes/values and ensure the pipeline runs reliably.

Rules:
- You may run ad hoc sweeps to size runtime and sanity-check metrics.
- You may adjust grid axis values *only during DEV*.
- **Do not cite DEV numbers**; they are for engineering and design decisions only.

### 4.2 EVAL phase (locked, citable)

Once `grid_v1` configs are committed:
- No changes to configs, policy definition, metrics, or selection criteria.
- Any necessary change becomes a new version (`grid_v2`) and triggers re-run requirements.

### 4.3 Holdout seeds (strongest practical safeguard)

Pre-register two disjoint seed sets:
- **Seed set A (analysis)**: e.g., 0–29
- **Seed set B (confirmation)**: e.g., 30–59

Workflow:
- Run `grid_v1` on seed set A, summarize, and form hypotheses.
- Any follow-on idea must be validated by running **the same `grid_v1`** on seed set B.
- If B disagrees with A materially, we report that discrepancy (it is a result).

---

## 5) Implementation plan (what we will actually do in the repo)

### 5.1 Create locked grid configs

- Directory: `configs/locked/exp1_grid_v1/`
- For each regime point: create **three** configs (only `system` differs):
  - `...__baseline_a.toml`
  - `...__baseline_b.toml`
  - `...__proposed.toml`

Naming convention encodes the regime point, e.g.:
- `exp1_grid_v1__cr0p10__sig0p50__cfa10__cws0p10__baseline_a.toml`

### 5.2 Run sweeps per regime point (matched-seed)

For each regime point directory:
- Run a sweep with a deterministic sweep id, e.g.:
  - `exp1_grid_v1__cr0p10__sig0p50__cfa10__cws0p10__A_n30`
  - `...__B_n30` (holdout)

Each sweep produces:
- `sweep_manifest.json`
- `sweep_progress.json`
- `sweep_summary.json` (includes deterministic bootstrap CIs for means)

### 5.3 Aggregate across regime points into a “regime map”

Create a grid-level summary artifact:
- `artifacts/exp1_grid_v1_summary__A.json`
- `artifacts/exp1_grid_v1_summary__B.json`

Contents:
- For each regime point:
  - system means/CIs for M3b, M3, M7, M8, M9
  - deltas: proposed − baseline_a, proposed − baseline_b (for primary metric M3b)
- Overall:
  - fraction of regime points where proposed has lower mean M3b than each baseline
  - distribution of deltas (median, quantiles)

Note: grid-level aggregation should be purely artifact-derived (no manual spreadsheet edits).

---

## 6) How this produces “top-tier” results without overclaiming

This plan forces us to report:
- **benefit regions** (where proposed reduces regret)
- **harm regions** (where proposed increases regret)
- **tradeoff cost** (M7/M8/M9), with thresholds pinned

This is exactly the kind of result DS reviewers respect: a clean, reproducible characterization of decision-information tradeoffs under delayed reconciliation.

---

## 7) Explicit “what would be invalid” (to keep integrity crisp)

Any of the following after EVAL lock requires `grid_v2`:
- changing grid axes/values
- changing the policy definition or thresholds
- changing the loss parameters
- changing metric definitions/implementation
- deleting or excluding runs without a preregistered rule

All such changes must be logged in `post_runner.md` with sweep IDs affected.


