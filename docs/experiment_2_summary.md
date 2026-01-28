### Experiment 2 — Full Summary (LEGACY: semantics-varying grid run)

**Important**: This summary corresponds to `exp2_grid_v1` (baseline_a/baseline_b/proposed across 54 regimes).
That run is **not** the strict preregistered Exp2 isolation design (“state semantics fixed; policy varies”).

For the thesis-defensible Exp2, use **`exp2_policy_v1`** (policy sweep with fixed semantics) as described in `docs/experiment2_runbook.md` and `scripts/run_exp2_policy_v1.ps1`.

This report is **artifact-derived** from:
- Locked configs: `configs/locked/exp2_grid_v1/`
- Seed Set A artifacts: `artifacts/exp2/` (prefix `exp2_grid_v1__A`)
- Holdout Seed Set B artifacts: `C:\exp2_artifacts` (prefix `exp2_grid_v1__B_r2`)

## Executive summary (thesis-ready, citation-safe)
- **Primary outcome**: `M3_avg_cost` (lower is better), evaluated on a **preregistered 54-regime-point grid** with **30 seeds per seed set**.
- **Headline** (descriptive, bounded to this grid):
  - **Seed Set A**: `proposed` had lower per-point mean `M3_avg_cost` than `baseline_a` in **18 / 54** regime points.
  - **Holdout stability**: A vs B per-point deltas (proposed − baseline_b) have Pearson correlation **0.9994456824178921** with sign agreement **54 / 54** (excluding exact zeros).
- **Data completeness**:
  - **Seed Set A**: **54 / 54** points finalized; expected runs = 4860
  - **Seed Set B (holdout)**: **54 / 54** points finalized; expected runs = 4860

## Hypothesis linkage (what Exp2 tests, without over-claiming)
- Exp2 tests whether **cost-aware deferral policies** (WAIT vs ACT under uncertainty) change observed cost outcomes relative to baselines, under matched evidence + reconciliation streams.
- Working expectation (pre-results): **regime-dependent tradeoffs**:
  - `proposed` may defer more (higher `M5_deferral_rate`), potentially changing tail behavior (`M4_*`) and average cost (`M3_*`).
  - Effects should be stable under matched holdout seeds if they reflect the modeled phenomenon rather than noise.

## Claim bank (pinpointed, citation-safe)
- **Data completeness**: both A and B include **4860 / 4860** eval runs across **54 / 54** regime points under the paper-safe inclusion rule.
- **Primary outcome, analysis split (A)**: On the preregistered 54-point grid, `proposed` achieved lower per-point mean **M3_avg_cost** than `baseline_a` in **18 / 54** regime points.
- **Primary outcome, holdout split (B)**: On the same grid, `proposed` achieved lower per-point mean **M3_avg_cost** than `baseline_a` in **18 / 54** regime points.
- **Holdout stability**: Per-regime-point deltas (proposed − baseline_b) between A and B have Pearson correlation **0.9994456824178921** with sign agreement **54 / 54** (excluding exact zeros).

## Preregistered design (inputs)
- **Grid size**: **54 regime points** (3×3×3×2)
- **Systems compared**: `baseline_a`, `baseline_b`, `proposed`
- **Primary outcome**: **M3_avg_cost** (lower is better)
- **Seed sets**:
  - **A (analysis)**: seeds 0–29
  - **B (holdout)**: seeds 30–59

## Data inclusion + integrity checks (paper-safe)
- **Expected eval runs per seed set**: 54 points × 3 systems × 30 seeds = **4860 runs**
- **Canonical sweep inclusion rule**: include only sweeps where
  - `sweep_progress.json.last_run_id == "FINALIZED"` and `completed == total == 90`, and
  - `sweep_manifest.json.seeds` exactly matches the preregistered seed range for the seed set.
- **Canonical sweep selection rule**: if multiple eligible sweeps exist for the same regime point, select the one with the newest `created_utc` (ties by directory name).
- **Sweep manifest robustness**: if `sweep_manifest.json.runs` is incomplete, rebuild the run list from per-run `run_manifest.json` files.
- **Seed Set A finalized points**: **54 / 54** (audit: `artifacts/audit_exp2_grid_v1__A.json`)
- **Seed Set B finalized points**: **54 / 54** (audit: `artifacts/audit_exp2_grid_v1__B_r2.json`)
- **Note on duplicates**: If multiple eligible full sweeps exist for the same point (reruns), we select exactly one canonical sweep by newest `created_utc`. Duplicates are reported below and contribute extra run directories on disk, but do not change the selected evaluation set.

## Primary outcome results (M3_avg_cost)
### Seed Set A
- **Included eval runs**: **4860 / 4860** across **54 / 54** regime points
- **Canonical full sweeps selected**: 54 (expected 54)
- **Duplicate eligible full sweeps (same point, reruns)**: 5
- **Sweep manifest rebuilds applied**: 0 sweep(s)
- **Proposed vs baseline_a (per-point wins)**: **18 / 54** wins (33.3%), **36** losses, **0** ties
- **Proposed vs baseline_b (per-point wins)**: **18 / 54** wins (33.3%), **36** losses, **0** ties
- **Delta summary (proposed − baseline_a)**: mean 0.17945569451678786, median 0.049506730778166474, min -0.5153222312496695, max 1.0803726481166662
- **Delta summary (proposed − baseline_b)**: mean 0.17945569451678786, median 0.049506730778166474, min -0.5153222312496695, max 1.0803726481166662

### Seed Set B_r2
- **Included eval runs**: **4860 / 4860** across **54 / 54** regime points
- **Canonical full sweeps selected**: 54 (expected 54)
- **Duplicate eligible full sweeps (same point, reruns)**: 0
- **Sweep manifest rebuilds applied**: 0 sweep(s)
- **Proposed vs baseline_a (per-point wins)**: **18 / 54** wins (33.3%), **36** losses, **0** ties
- **Proposed vs baseline_b (per-point wins)**: **18 / 54** wins (33.3%), **36** losses, **0** ties
- **Delta summary (proposed − baseline_a)**: mean 0.17688952292258422, median 0.04849838553879837, min -0.5474022037151922, max 1.0766017765242673
- **Delta summary (proposed − baseline_b)**: mean 0.17688952292258422, median 0.04849838553879837, min -0.5474022037151922, max 1.0766017765242673

## Holdout stability (A vs B)
- Common regime points compared: **54 / 54**
- Pearson correlation of per-point deltas (proposed − baseline_b): **0.9994456824178921**
- Sign agreement on deltas (excluding exact zeros): **54 / 54**

## Top wins / top losses (where it helps vs where it hurts)
- Delta = `proposed_mean - baseline_mean` on `M3_avg_cost` (negative is better for `proposed`).
- We report the top 10 most negative (wins) and top 10 most positive (losses) regime points.

### Seed Set A
#### Proposed vs baseline_a

| kind | rank | point_key | delta | proposed_mean | baseline_mean |
|---|---:|---|---:|---:|---:|
| win | 1 | `cr0p20__sig1p00__cfa20p00__cws0p05` | -0.5153222312496695 | 8.902677768750332 | 9.418000000000001 |
| win | 2 | `cr0p20__sig0p50__cfa20p00__cws0p05` | -0.5017708434166668 | 8.916229156583334 | 9.418000000000001 |
| win | 3 | `cr0p20__sig0p25__cfa20p00__cws0p05` | -0.49828034260833576 | 8.919719657391665 | 9.418000000000001 |
| win | 4 | `cr0p10__sig1p00__cfa20p00__cws0p05` | -0.27816205419074613 | 9.382432918137052 | 9.660594972327798 |
| win | 5 | `cr0p10__sig0p50__cfa20p00__cws0p05` | -0.2714057499375784 | 9.38918922239022 | 9.660594972327798 |
| win | 6 | `cr0p10__sig0p25__cfa20p00__cws0p05` | -0.2696532509874654 | 9.390941721340333 | 9.660594972327798 |
| win | 7 | `cr0p20__sig1p00__cfa20p00__cws0p10` | -0.258911129166 | 9.159088870834001 | 9.418000000000001 |
| win | 8 | `cr0p20__sig0p50__cfa20p00__cws0p10` | -0.23180835350000173 | 9.1861916465 | 9.418000000000001 |
| win | 9 | `cr0p20__sig0p25__cfa20p00__cws0p10` | -0.22482735188333436 | 9.193172648116667 | 9.418000000000001 |
| win | 10 | `cr0p10__sig1p00__cfa20p00__cws0p10` | -0.14952157454139048 | 9.511073397786408 | 9.660594972327798 |
| loss | 1 | `cr0p20__sig0p25__cfa5p00__cws0p10` | 1.0803726481166662 | 3.4348726481166665 | 2.3545000000000003 |
| loss | 2 | `cr0p20__sig0p50__cfa5p00__cws0p10` | 1.0733916464999997 | 3.4278916465 | 2.3545000000000003 |
| loss | 3 | `cr0p20__sig1p00__cfa5p00__cws0p10` | 1.0462888708339997 | 3.400788870834 | 2.3545000000000003 |
| loss | 4 | `cr0p20__sig0p25__cfa5p00__cws0p05` | 0.8069196573916666 | 3.161419657391667 | 2.3545000000000003 |
| loss | 5 | `cr0p20__sig0p50__cfa5p00__cws0p05` | 0.8034291565833334 | 3.1579291565833336 | 2.3545000000000003 |
| loss | 6 | `cr0p20__sig1p00__cfa5p00__cws0p05` | 0.7898777687503329 | 3.144377768750333 | 2.3545000000000003 |
| loss | 7 | `cr0p20__sig0p25__cfa10p00__cws0p10` | 0.6453059814499991 | 5.35430598145 | 4.7090000000000005 |
| loss | 8 | `cr0p20__sig0p50__cfa10p00__cws0p10` | 0.6383249798333326 | 5.347324979833333 | 4.7090000000000005 |
| loss | 9 | `cr0p20__sig1p00__cfa10p00__cws0p10` | 0.6112222041673334 | 5.320222204167334 | 4.7090000000000005 |
| loss | 10 | `cr0p10__sig0p25__cfa5p00__cws0p10` | 0.5320004927573461 | 2.9471492358392957 | 2.4151487430819496 |

#### Proposed vs baseline_b

| kind | rank | point_key | delta | proposed_mean | baseline_mean |
|---|---:|---|---:|---:|---:|
| win | 1 | `cr0p20__sig1p00__cfa20p00__cws0p05` | -0.5153222312496695 | 8.902677768750332 | 9.418000000000001 |
| win | 2 | `cr0p20__sig0p50__cfa20p00__cws0p05` | -0.5017708434166668 | 8.916229156583334 | 9.418000000000001 |
| win | 3 | `cr0p20__sig0p25__cfa20p00__cws0p05` | -0.49828034260833576 | 8.919719657391665 | 9.418000000000001 |
| win | 4 | `cr0p10__sig1p00__cfa20p00__cws0p05` | -0.27816205419074613 | 9.382432918137052 | 9.660594972327798 |
| win | 5 | `cr0p10__sig0p50__cfa20p00__cws0p05` | -0.2714057499375784 | 9.38918922239022 | 9.660594972327798 |
| win | 6 | `cr0p10__sig0p25__cfa20p00__cws0p05` | -0.2696532509874654 | 9.390941721340333 | 9.660594972327798 |
| win | 7 | `cr0p20__sig1p00__cfa20p00__cws0p10` | -0.258911129166 | 9.159088870834001 | 9.418000000000001 |
| win | 8 | `cr0p20__sig0p50__cfa20p00__cws0p10` | -0.23180835350000173 | 9.1861916465 | 9.418000000000001 |
| win | 9 | `cr0p20__sig0p25__cfa20p00__cws0p10` | -0.22482735188333436 | 9.193172648116667 | 9.418000000000001 |
| win | 10 | `cr0p10__sig1p00__cfa20p00__cws0p10` | -0.14952157454139048 | 9.511073397786408 | 9.660594972327798 |
| loss | 1 | `cr0p20__sig0p25__cfa5p00__cws0p10` | 1.0803726481166662 | 3.4348726481166665 | 2.3545000000000003 |
| loss | 2 | `cr0p20__sig0p50__cfa5p00__cws0p10` | 1.0733916464999997 | 3.4278916465 | 2.3545000000000003 |
| loss | 3 | `cr0p20__sig1p00__cfa5p00__cws0p10` | 1.0462888708339997 | 3.400788870834 | 2.3545000000000003 |
| loss | 4 | `cr0p20__sig0p25__cfa5p00__cws0p05` | 0.8069196573916666 | 3.161419657391667 | 2.3545000000000003 |
| loss | 5 | `cr0p20__sig0p50__cfa5p00__cws0p05` | 0.8034291565833334 | 3.1579291565833336 | 2.3545000000000003 |
| loss | 6 | `cr0p20__sig1p00__cfa5p00__cws0p05` | 0.7898777687503329 | 3.144377768750333 | 2.3545000000000003 |
| loss | 7 | `cr0p20__sig0p25__cfa10p00__cws0p10` | 0.6453059814499991 | 5.35430598145 | 4.7090000000000005 |
| loss | 8 | `cr0p20__sig0p50__cfa10p00__cws0p10` | 0.6383249798333326 | 5.347324979833333 | 4.7090000000000005 |
| loss | 9 | `cr0p20__sig1p00__cfa10p00__cws0p10` | 0.6112222041673334 | 5.320222204167334 | 4.7090000000000005 |
| loss | 10 | `cr0p10__sig0p25__cfa5p00__cws0p10` | 0.5320004927573461 | 2.9471492358392957 | 2.4151487430819496 |


### Seed Set B_r2
#### Proposed vs baseline_a

| kind | rank | point_key | delta | proposed_mean | baseline_mean |
|---|---:|---|---:|---:|---:|
| win | 1 | `cr0p20__sig1p00__cfa20p00__cws0p05` | -0.5474022037151922 | 9.019998449748835 | 9.567400653464027 |
| win | 2 | `cr0p20__sig0p50__cfa20p00__cws0p05` | -0.533993469643443 | 9.033407183820584 | 9.567400653464027 |
| win | 3 | `cr0p20__sig0p25__cfa20p00__cws0p05` | -0.5305238433508563 | 9.03687681011317 | 9.567400653464027 |
| win | 4 | `cr0p20__sig1p00__cfa20p00__cws0p10` | -0.2882645261207877 | 9.27913612734324 | 9.567400653464027 |
| win | 5 | `cr0p10__sig1p00__cfa20p00__cws0p05` | -0.2640296473576971 | 9.23336828556222 | 9.497397932919917 |
| win | 6 | `cr0p20__sig0p50__cfa20p00__cws0p10` | -0.26144705797729095 | 9.305953595486736 | 9.567400653464027 |
| win | 7 | `cr0p10__sig0p50__cfa20p00__cws0p05` | -0.2571759614107503 | 9.240221971509166 | 9.497397932919917 |
| win | 8 | `cr0p10__sig0p25__cfa20p00__cws0p05` | -0.2554111809853783 | 9.241986751934538 | 9.497397932919917 |
| win | 9 | `cr0p20__sig0p25__cfa20p00__cws0p10` | -0.2545078053921177 | 9.31289284807191 | 9.567400653464027 |
| win | 10 | `cr0p10__sig1p00__cfa20p00__cws0p10` | -0.13492306746994842 | 9.362474865449968 | 9.497397932919917 |
| loss | 1 | `cr0p20__sig0p25__cfa5p00__cws0p10` | 1.0766017765242673 | 3.468451939890274 | 2.3918501633660068 |
| loss | 2 | `cr0p20__sig0p50__cfa5p00__cws0p10` | 1.0696625239390944 | 3.461512687305101 | 2.3918501633660068 |
| loss | 3 | `cr0p20__sig1p00__cfa5p00__cws0p10` | 1.042845055795596 | 3.4346952191616027 | 2.3918501633660068 |
| loss | 4 | `cr0p20__sig0p25__cfa5p00__cws0p05` | 0.8005857385655273 | 3.192435901931534 | 2.3918501633660068 |
| loss | 5 | `cr0p20__sig0p50__cfa5p00__cws0p05` | 0.7971161122729411 | 3.188966275638948 | 2.3918501633660068 |
| loss | 6 | `cr0p20__sig1p00__cfa5p00__cws0p05` | 0.7837073782011919 | 3.1755575415671986 | 2.3918501633660068 |
| loss | 7 | `cr0p20__sig0p25__cfa10p00__cws0p10` | 0.6328985825521389 | 5.416598909284152 | 4.7837003267320135 |
| loss | 8 | `cr0p20__sig0p50__cfa10p00__cws0p10` | 0.6259593299669666 | 5.40965965669898 | 4.7837003267320135 |
| loss | 9 | `cr0p20__sig1p00__cfa10p00__cws0p10` | 0.5991418618234681 | 5.382842188555482 | 4.7837003267320135 |
| loss | 10 | `cr0p10__sig0p25__cfa5p00__cws0p10` | 0.5419184061828717 | 2.916267889412851 | 2.374349483229979 |

#### Proposed vs baseline_b

| kind | rank | point_key | delta | proposed_mean | baseline_mean |
|---|---:|---|---:|---:|---:|
| win | 1 | `cr0p20__sig1p00__cfa20p00__cws0p05` | -0.5474022037151922 | 9.019998449748835 | 9.567400653464027 |
| win | 2 | `cr0p20__sig0p50__cfa20p00__cws0p05` | -0.533993469643443 | 9.033407183820584 | 9.567400653464027 |
| win | 3 | `cr0p20__sig0p25__cfa20p00__cws0p05` | -0.5305238433508563 | 9.03687681011317 | 9.567400653464027 |
| win | 4 | `cr0p20__sig1p00__cfa20p00__cws0p10` | -0.2882645261207877 | 9.27913612734324 | 9.567400653464027 |
| win | 5 | `cr0p10__sig1p00__cfa20p00__cws0p05` | -0.2640296473576971 | 9.23336828556222 | 9.497397932919917 |
| win | 6 | `cr0p20__sig0p50__cfa20p00__cws0p10` | -0.26144705797729095 | 9.305953595486736 | 9.567400653464027 |
| win | 7 | `cr0p10__sig0p50__cfa20p00__cws0p05` | -0.2571759614107503 | 9.240221971509166 | 9.497397932919917 |
| win | 8 | `cr0p10__sig0p25__cfa20p00__cws0p05` | -0.2554111809853783 | 9.241986751934538 | 9.497397932919917 |
| win | 9 | `cr0p20__sig0p25__cfa20p00__cws0p10` | -0.2545078053921177 | 9.31289284807191 | 9.567400653464027 |
| win | 10 | `cr0p10__sig1p00__cfa20p00__cws0p10` | -0.13492306746994842 | 9.362474865449968 | 9.497397932919917 |
| loss | 1 | `cr0p20__sig0p25__cfa5p00__cws0p10` | 1.0766017765242673 | 3.468451939890274 | 2.3918501633660068 |
| loss | 2 | `cr0p20__sig0p50__cfa5p00__cws0p10` | 1.0696625239390944 | 3.461512687305101 | 2.3918501633660068 |
| loss | 3 | `cr0p20__sig1p00__cfa5p00__cws0p10` | 1.042845055795596 | 3.4346952191616027 | 2.3918501633660068 |
| loss | 4 | `cr0p20__sig0p25__cfa5p00__cws0p05` | 0.8005857385655273 | 3.192435901931534 | 2.3918501633660068 |
| loss | 5 | `cr0p20__sig0p50__cfa5p00__cws0p05` | 0.7971161122729411 | 3.188966275638948 | 2.3918501633660068 |
| loss | 6 | `cr0p20__sig1p00__cfa5p00__cws0p05` | 0.7837073782011919 | 3.1755575415671986 | 2.3918501633660068 |
| loss | 7 | `cr0p20__sig0p25__cfa10p00__cws0p10` | 0.6328985825521389 | 5.416598909284152 | 4.7837003267320135 |
| loss | 8 | `cr0p20__sig0p50__cfa10p00__cws0p10` | 0.6259593299669666 | 5.40965965669898 | 4.7837003267320135 |
| loss | 9 | `cr0p20__sig1p00__cfa10p00__cws0p10` | 0.5991418618234681 | 5.382842188555482 | 4.7837003267320135 |
| loss | 10 | `cr0p10__sig0p25__cfa5p00__cws0p10` | 0.5419184061828717 | 2.916267889412851 | 2.374349483229979 |


## Secondary metrics (descriptive; mean of per-point means)
- These are **not** preregistered primary outcomes; treat as descriptive tradeoff context.
### Seed Set A
- **baseline_a**: M3_avg_cost=5.503023096471146, M4_p95_cost=11.666666666666666, M4_p99_cost=11.666666666666666, M5_deferral_rate=0.0
- **baseline_b**: M3_avg_cost=5.503023096471146, M4_p95_cost=11.666666666666666, M4_p99_cost=11.666666666666666, M5_deferral_rate=0.0
- **proposed**: M3_avg_cost=5.6824787909879335, M4_p95_cost=13.065892087351854, M4_p99_cost=13.775983175555556, M5_deferral_rate=0.09510243515369741

### Seed Set B_r2
- **baseline_a**: M3_avg_cost=5.56529497158691, M4_p95_cost=11.666666666666666, M4_p99_cost=11.666666666666666, M5_deferral_rate=0.0
- **baseline_b**: M3_avg_cost=5.56529497158691, M4_p95_cost=11.666666666666666, M4_p99_cost=11.666666666666666, M5_deferral_rate=0.0
- **proposed**: M3_avg_cost=5.742184494509495, M4_p95_cost=13.073499685203704, M4_p99_cost=13.776247323464816, M5_deferral_rate=0.09589624280411638

## Artifact anchors (what to cite)
- Locked configs (defines the 54 regime points): `configs/locked/exp2_grid_v1/`
- Audit (A): `artifacts/audit_exp2_grid_v1__A.json`
- Audit (B): `artifacts/audit_exp2_grid_v1__B_r2.json`
- Point-level tables (generated):
  - `artifacts/exp2_grid_v1_table__A.csv`
  - `artifacts/exp2_grid_v1_table__B_r2.csv`
- Extremes tables (generated):
  - `artifacts/exp2_grid_v1_extremes__A.csv`
  - `artifacts/exp2_grid_v1_extremes__B_r2.csv`

