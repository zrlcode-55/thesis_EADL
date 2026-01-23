### Experiment 1 — Full Summary (Grid v1, preregistered)

This report is **artifact-derived** from `configs/locked/exp1_grid_v1/` + `artifacts/` and is intended as the single reference for paper writing.

## Executive summary (thesis-ready, citation-safe)
- **Primary outcome**: `M3b_avg_regret_vs_oracle` (lower is better), evaluated on a **preregistered 54-regime-point grid** with **30 seeds per seed set**.
- **Data completeness**: **4860 / 4860 eval runs** per seed set (A and B) across **54 / 54** regime points under the inclusion rules below.
- **What worked (headline)**:
  - **Seed Set A**: `proposed` had lower per-point mean regret than `baseline_a` in **39 / 54** regime points and lower than `baseline_b` in **39 / 54** regime points.
  - **Seed Set B (holdout)**: `proposed` had lower per-point mean regret than `baseline_a` in **36 / 54** regime points and lower than `baseline_b` in **36 / 54** regime points.
  - **Holdout stability**: per-point deltas (proposed − baseline_b) between A and B have Pearson correlation **0.9996442758509282** with sign agreement **51 / 54** (excluding exact zeros).
- **What did not work / was undesirable (bounded, not speculative)**:
  - **Not universal**: `proposed` loses on **15 / 54** points in A and **18 / 54** points in B (so any “always better” claim is false).
  - **Overhead + budget tradeoff (descriptive, not optimized here)**: mean-of-per-point-means suggests `proposed` uses higher `M7_state_bytes_mean`, higher `M8_stateview_ms_mean`, and higher `M9_conflict_budget_size` than baselines (see “Secondary metrics”).
  - **Rerun / bookkeeping complexity**: Seed A includes **1 duplicated eligible full sweep** (handled by a deterministic selection rule) and **1 sweep with an incomplete `sweep_manifest.json` run list** (handled by rebuilding from `run_manifest.json`).

## What you can safely claim from this report (scope)
- This report supports **descriptive claims** about performance **on the preregistered Exp1 grid** (54 regime points) under the preregistered seed splits (A and B).
- It does **not** support claims about universal superiority, real-world deployment, or statistical significance unless you add separate analyses.

## Preregistered design (inputs)
- **Grid size**: **54 regime points** (3×3×3×2)
- **Systems compared**: `baseline_a`, `baseline_b`, `proposed`
- **Primary outcome**: **M3b_avg_regret_vs_oracle** (lower is better)
- **Seed sets**:
  - **A (analysis)**: seeds 0–29
  - **B (holdout)**: seeds 30–59

## Definitions (how numbers are computed)
- **Regime point**: one locked config point key `cr…__sig…__cfa…__cws…` from `configs/locked/exp1_grid_v1/`.
- **Per-point system mean**: mean of M3b_avg_regret_vs_oracle over the 30 seeds for that system at that regime point.
- **Delta (proposed − baseline)**: difference between per-point means (negative is better for proposed).
- **Win/Loss/Tie counts**: computed **per regime point** by the sign of the delta; each regime point has equal weight.
- **Mean delta**: mean of the per-point deltas across regime points (equal-weighted by point).

## Data inclusion + integrity checks (paper-safe)
- **Expected eval runs per seed set**: 54 points × 3 systems × 30 seeds = **4860 runs**
- **Canonical sweep inclusion rule**: include only sweeps where
  - `sweep_progress.json.last_run_id == "FINALIZED"` and `completed == total == 90`, and
  - `sweep_manifest.json.seeds` exactly matches the preregistered seed range for the seed set.
- **Canonical sweep selection rule**: if multiple eligible sweeps exist for the same regime point, select the one with the newest `created_utc` (ties by directory name).
- **Sweep manifest robustness**: if `sweep_manifest.json.runs` is incomplete, rebuild the run list from per-run `run_manifest.json` files.
- **Seed Set A finalized points**: **54 / 54** (audit: `artifacts/audit_exp1_grid_v1__A.json`)
- **Seed Set B finalized points**: **54 / 54** (audit: `artifacts/audit_exp1_grid_v1__B_r1.json`)

## Expectations stated up front (not results)
- We did **not** claim universal superiority; we expected **regime-dependent tradeoffs**.
- Holdout goal: **Seed Set B should broadly agree with Seed Set A** on the regime map (directionally).

## Primary outcome results (M3b_avg_regret_vs_oracle)
### Seed Set A
- **Included eval runs**: **4860 / 4860** across **54 / 54** regime points
- **Canonical full sweeps selected**: 54 (expected 54)
- **Duplicate eligible full sweeps (same point, reruns)**: 1
- **Sweep manifest rebuilds applied**: 1 sweep(s)
  - duplicate regime point keys: cr0p01__sig0p25__cfa10p00__cws0p05
  - rebuilt from run manifests: sweep_exp1_grid_v1__A_r11__cr0p20__sig1p00__cfa5p00__cws0p10
- **Proposed vs baseline_a (per-point wins)**: **39 / 54** wins (72.2%), **15** losses, **0** ties
- **Proposed vs baseline_b (per-point wins)**: **39 / 54** wins (72.2%), **15** losses, **0** ties
- **Delta summary (proposed − baseline_a)**: mean -0.22209302489142535, median -0.04950673077816603, min -1.0803726481166658, max 0.18249369191433473
- **Delta summary (proposed − baseline_b)**: mean -0.22209302489142535, median -0.04950673077816603, min -1.0803726481166658, max 0.18249369191433473

### Seed Set B_r1
- **Included eval runs**: **4860 / 4860** across **54 / 54** regime points
- **Canonical full sweeps selected**: 54 (expected 54)
- **Duplicate eligible full sweeps (same point, reruns)**: 0
- **Sweep manifest rebuilds applied**: 0 sweep(s)
- **Proposed vs baseline_a (per-point wins)**: **36 / 54** wins (66.7%), **18** losses, **0** ties
- **Proposed vs baseline_b (per-point wins)**: **36 / 54** wins (66.7%), **18** losses, **0** ties
- **Delta summary (proposed − baseline_a)**: mean -0.21904153424080275, median -0.04849838553879815, min -1.0766017765242673, max 0.20196247748312057
- **Delta summary (proposed − baseline_b)**: mean -0.21904153424080275, median -0.04849838553879815, min -1.0766017765242673, max 0.20196247748312057

## Paper-ready claim bank (pinpointed, citation-safe)
- **Primary outcome, analysis split (A)**: On the preregistered 54-point grid, `proposed` achieved lower per-point mean **M3b_avg_regret_vs_oracle** than `baseline_a` in **39 / 54** regime points, and lower than `baseline_b` in **39 / 54** regime points.
- **Primary outcome, holdout split (B)**: On the same grid, `proposed` achieved lower per-point mean **M3b_avg_regret_vs_oracle** than `baseline_a` in **36 / 54** regime points, and lower than `baseline_b` in **36 / 54** regime points.
- **Holdout stability**: Per-regime-point deltas (proposed − baseline_b) between A and B have Pearson correlation **0.9996442758509282** with sign agreement **51 / 54** (excluding exact zeros).
- **Data completeness (for these claims)**: both A and B include **4860 / 4860** eval runs across **54 / 54** regime points under the paper-safe inclusion rule above.

## Recommended “artifact pack” for paper + Exp2 (reasonable + advanced)

### The minimal citation pack (already present)
- **Locked preregistered grid**: `configs/locked/exp1_grid_v1/`
- **Integrity audits** (counts + missingness checks):  
  - `artifacts/audit_exp1_grid_v1__A.json`  
  - `artifacts/audit_exp1_grid_v1__B_r1.json`
- **Point-level tables (system means per regime point)**:  
  - `artifacts/exp1_grid_v1_table__A.csv`  
  - `artifacts/exp1_grid_v1_table__B_r1.csv`
- **This summary**: `docs/experiment1_full_summary.md`

### Storytelling tables that “tell the story” (recommended to add)
These are derived tables you can generate from the existing point-level CSVs above (no new experiments required):
- **Per-point delta table** (for heatmaps + ranking): `artifacts/exp1_grid_v1_deltas__{A,B_r1}.csv`
  - columns: `point_key`, `delta_proposed_minus_baseline_a`, `delta_proposed_minus_baseline_b`, plus optionally `mean_M7_bytes`, `mean_M8_ms`, `mean_M9_budget` deltas.
- **Top wins / top losses** (for “where it helps / where it hurts” paragraphs): `artifacts/exp1_grid_v1_extremes__{A,B_r1}.csv`
  - top-K most negative deltas (best improvements) and top-K most positive deltas (worst regressions), with the regime point key.
- **Holdout stability scatter data**: `artifacts/exp1_grid_v1_holdout_scatter__A_vs_B.csv`
  - columns: `point_key`, `delta_A`, `delta_B`, `sign_agree`.

### Advanced artifacts (if you want Harvard-proof figures fast)
- **Regime map heatmaps**: a single figure per baseline comparison showing the 54 points as facets; drives the “regime-dependent” claim.
- **Tradeoff plots**: scatter of `delta_regret` vs `delta_overhead` (bytes and/or ms) per regime point.
- **Appendix table**: the full 54-point delta table (or a condensed version) so reviewers can audit “where it fails”.

### Suggested artifact directory layout (keeps Exp1 and Exp2 clean)
- `artifacts/exp1/`  
  - `tables/` (CSV tables used in the paper)  
  - `figures/` (PNG/PDF exports, named by figure number)  
  - `notes/` (short markdown explaining any reruns, exclusions, or fixes)
- `artifacts/exp2/` (same structure)

## Holdout stability (A vs B)
- Common regime points compared: **54 / 54**
- Pearson correlation of per-point deltas (proposed − baseline_b): **0.9996442758509282**
- Sign agreement on deltas (excluding exact zeros): **51 / 54**

## Secondary metrics (descriptive; mean of per-point means)
- These are **not** preregistered primary outcomes; treat as descriptive tradeoff context.
### Seed Set A
- **baseline_a**: M1=0.4716876939832411, M3=7.458982717430386, M7_bytes=203.0, M8_ms=0.0019438805601151407, M9_budget=1.0
- **baseline_b**: M1=0.4716876939832411, M3=7.458982717430386, M7_bytes=203.0, M8_ms=0.0019439422187896985, M9_budget=1.0
- **proposed**: M1=0.4756069655412564, M3=7.23688969253896, M7_bytes=205.75480000000002, M8_ms=0.0021764256854190918, M9_budget=2.988888888888889

### Seed Set B_r1
- **baseline_a**: M1=0.477025283278878, M3=7.405620905045739, M7_bytes=203.0, M8_ms=0.0017060840070135545, M9_budget=1.0
- **baseline_b**: M1=0.477025283278878, M3=7.405620905045739, M7_bytes=203.0, M8_ms=0.0015365080735473722, M9_budget=1.0
- **proposed**: M1=0.48053121824364875, M3=7.186579370804936, M7_bytes=205.76386666666664, M8_ms=0.0017770295266355217, M9_budget=2.9925925925925925

## Artifact anchors (what to cite)
- Locked configs (defines the 54 regime points): `configs/locked/exp1_grid_v1/`
- Audit (A): `artifacts/audit_exp1_grid_v1__A.json`
- Audit (B): `artifacts/audit_exp1_grid_v1__B_r1.json`
- Point-level tables (generated):
  - `artifacts/exp1_grid_v1_table__A.csv`
  - `artifacts/exp1_grid_v1_table__B_r1.csv`

## Figure suggestions (optional)
- **Regime-map heatmaps**: delta (proposed − baseline) as heatmap facets over (conflict_rate × delay_sigma) for each cost setting.
- **Tradeoff scatter**: per regime point, x=delta regret, y=delta overhead (bytes or ms), label by conflict_rate.
- **Holdout stability**: scatter of A deltas vs B deltas with y=x line + correlation.

