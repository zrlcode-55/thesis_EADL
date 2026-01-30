### Experiment 2 — Policy Sweep Summary (THESIS: fixed semantics, policy varies)

This report summarizes Exp2 policy sweeps (fixed state semantics; policy varies) from sweep summaries.
- Sweep prefix A: `exp2_policy_v2_16pt__A`
- Sweep prefix B: `exp2_policy_v2_16pt__B`

## Inputs (artifact anchors)
- Seed Set A artifacts: `C:\exp2_policy_v2_16pt_artifacts` (prefix `exp2_policy_v2_16pt__A`)
- Holdout Seed Set B artifacts: `C:\exp2_policy_v2_16pt_artifacts` (prefix `exp2_policy_v2_16pt__B`)

## Primary outcome
- **Primary metric**: `M3_avg_cost` (lower is better)
- **Policies**: `always_act`, `always_wait`, `wait_on_conflict`, `risk_threshold`
- **Reported metrics**: `M3_avg_cost`, `M5_deferral_rate`, `M2_mean_wait_seconds_when_wait`, `M4_p95_cost`, `M4_p99_cost`, `M1_correctness_rate`, `M3b_avg_regret_vs_oracle`

## Metric definitions (thesis-safe)
- **`M3_avg_cost`**: mean realized loss per labeled decision (lower is better).
- **`M5_deferral_rate`**: fraction of labeled decisions where action is `WAIT`.
- **`M2_mean_wait_seconds_when_wait`**: mean of `(reconciliation_arrival_time - decision_time)` over labeled decisions where action is `WAIT` (clipped at 0).
- **`M1_correctness_rate`**: decision-theoretic correctness rate: a decision is “correct” if its realized loss is within `correctness_epsilon` of the minimum realized loss among `{ACT, WAIT}` under the observed outcome and realized wait duration.
- **`M3b_avg_regret_vs_oracle`**: mean `(chosen_loss - oracle_loss)` where `oracle_loss = min(loss(ACT), loss(WAIT))` under the observed outcome and realized wait duration.
- **Note**: these are **artifact-derived** and do **not** claim inference accuracy or representation quality; they evaluate timing decisions under the specified loss model.

## Completeness
- **Seed Set A points included**: **12**
- **Seed Set B points included**: **12**
- **Common points (A∩B)**: **12**

## Win counts (per-point winner by mean cost)
### Seed Set A
- **always_act**: 12 wins
- **always_wait**: 0 wins
- **wait_on_conflict**: 0 wins
- **risk_threshold**: 0 wins

### Seed Set B (holdout)
- **always_act**: 12 wins
- **always_wait**: 0 wins
- **wait_on_conflict**: 0 wins
- **risk_threshold**: 0 wins

## Holdout stability (delta vs `always_act` per point)
- **always_wait**: n_points=12, pearson=0.9999999999397959
- **risk_threshold**: n_points=12, pearson=0.9998965817104882
- **wait_on_conflict**: n_points=12, pearson=0.9999999999238908

## Point-level winners (A and B)
| point_key | winner_A | winner_B |
|---|---|---|
| `wc_exponential__k0p25__a0p05` | `always_act` | `always_act` |
| `wc_exponential__k0p50__a0p05` | `always_act` | `always_act` |
| `wc_exponential__k0p50__a0p10` | `always_act` | `always_act` |
| `wc_exponential__k1p00__a0p05` | `always_act` | `always_act` |
| `wc_exponential__k1p00__a0p10` | `always_act` | `always_act` |
| `wc_linear__ps0p01` | `always_act` | `always_act` |
| `wc_linear__ps0p02` | `always_act` | `always_act` |
| `wc_linear__ps0p05` | `always_act` | `always_act` |
| `wc_linear__ps0p10` | `always_act` | `always_act` |
| `wc_linear__ps0p20` | `always_act` | `always_act` |
| `wc_quadratic__k0p00` | `always_act` | `always_act` |
| `wc_quadratic__k0p01` | `always_act` | `always_act` |

## Policy correctness + tradeoff summary (mean of per-point means)
- These are descriptive aggregates across regime points; they are **not** the primary win/loss analysis.

### Seed Set A
| policy | M3_avg_cost | M1_correctness_rate | M3b_avg_regret_vs_oracle | M5_deferral_rate | M2_mean_wait_seconds_when_wait |
|---|---|---|---|---|---|
| `always_act` | 4.788806 | 0.561192 | 2.938557 | 0.000000 | 0.000000 |
| `always_wait` | 9.736626 | 0.438808 | 7.886377 | 1.000000 | 29.389667 |
| `wait_on_conflict` | 5.248945 | 0.548836 | 3.398696 | 0.090145 | 29.376719 |
| `risk_threshold` | 7.885492 | 0.526976 | 6.035243 | 0.834034 | 26.941700 |

#### Sanity checks (policy-implementation correctness)
- **always_act deferral_rate** (expected ~0): 0.000000
- **always_wait deferral_rate** (expected ~1): 1.000000

### Seed Set B (holdout)
| policy | M3_avg_cost | M1_correctness_rate | M3b_avg_regret_vs_oracle | M5_deferral_rate | M2_mean_wait_seconds_when_wait |
|---|---|---|---|---|---|
| `always_act` | 4.715742 | 0.567877 | 2.893744 | 0.000000 | 0.000000 |
| `always_wait` | 9.809452 | 0.432123 | 7.987455 | 1.000000 | 29.388784 |
| `wait_on_conflict` | 5.169093 | 0.556198 | 3.347096 | 0.090309 | 29.375657 |
| `risk_threshold` | 7.952632 | 0.519596 | 6.130635 | 0.833884 | 26.940904 |

#### Sanity checks (policy-implementation correctness)
- **always_act deferral_rate** (expected ~0): 0.000000
- **always_wait deferral_rate** (expected ~1): 1.000000

## Point-level primary metric (`M3_avg_cost`) by policy
- Shows the per-point **mean** (from sweep summaries) for each policy on A and B.

| point_key | policy | mean_A | mean_B | delta_B_minus_A |
|---|---|---:|---:|---:|
| `wc_exponential__k0p25__a0p05` | `always_act` | 4.788806 | 4.715742 | -0.073065 |
| `wc_exponential__k0p25__a0p05` | `always_wait` | 6.048534 | 6.121559 | 0.073025 |
| `wc_exponential__k0p25__a0p05` | `wait_on_conflict` | 4.916832 | 4.836397 | -0.080435 |
| `wc_exponential__k0p25__a0p05` | `risk_threshold` | 5.920508 | 6.000903 | 0.080395 |
| `wc_exponential__k0p50__a0p05` | `always_act` | 4.788806 | 4.715742 | -0.073065 |
| `wc_exponential__k0p50__a0p05` | `always_wait` | 6.885875 | 6.958859 | 0.072985 |
| `wc_exponential__k0p50__a0p05` | `wait_on_conflict` | 4.992251 | 4.911949 | -0.080302 |
| `wc_exponential__k0p50__a0p05` | `risk_threshold` | 6.682429 | 6.762652 | 0.080222 |
| `wc_exponential__k0p50__a0p10` | `always_act` | 4.788806 | 4.715742 | -0.073065 |
| `wc_exponential__k0p50__a0p10` | `always_wait` | 14.179651 | 14.252148 | 0.072497 |
| `wc_exponential__k0p50__a0p10` | `wait_on_conflict` | 5.648790 | 5.569632 | -0.079158 |
| `wc_exponential__k0p50__a0p10` | `risk_threshold` | 13.319666 | 13.398257 | 0.078591 |
| `wc_exponential__k1p00__a0p05` | `always_act` | 4.788806 | 4.715742 | -0.073065 |
| `wc_exponential__k1p00__a0p05` | `always_wait` | 8.560555 | 8.633460 | 0.072905 |
| `wc_exponential__k1p00__a0p05` | `wait_on_conflict` | 5.143090 | 5.063054 | -0.080036 |
| `wc_exponential__k1p00__a0p05` | `risk_threshold` | 8.206272 | 8.286148 | 0.079876 |
| `wc_exponential__k1p00__a0p10` | `always_act` | 4.788806 | 4.715742 | -0.073065 |
| `wc_exponential__k1p00__a0p10` | `always_wait` | 23.148108 | 23.220037 | 0.071930 |
| `wc_exponential__k1p00__a0p10` | `wait_on_conflict` | 6.456168 | 6.378419 | -0.077749 |
| `wc_exponential__k1p00__a0p10` | `risk_threshold` | 4.788806 | 4.715742 | -0.073065 |
| `wc_linear__ps0p01` | `always_act` | 4.788806 | 4.715742 | -0.073065 |
| `wc_linear__ps0p01` | `always_wait` | 5.505090 | 5.578146 | 0.073056 |
| `wc_linear__ps0p01` | `wait_on_conflict` | 4.867895 | 4.787374 | -0.080521 |
| `wc_linear__ps0p01` | `risk_threshold` | 5.426002 | 5.506514 | 0.080512 |
| `wc_linear__ps0p02` | `always_act` | 4.788806 | 4.715742 | -0.073065 |
| `wc_linear__ps0p02` | `always_wait` | 5.798987 | 5.872034 | 0.073047 |
| `wc_linear__ps0p02` | `wait_on_conflict` | 4.894376 | 4.813903 | -0.080473 |
| `wc_linear__ps0p02` | `risk_threshold` | 5.693417 | 5.773873 | 0.080456 |
| `wc_linear__ps0p05` | `always_act` | 4.788806 | 4.715742 | -0.073065 |
| `wc_linear__ps0p05` | `always_wait` | 6.680677 | 6.753698 | 0.073021 |
| `wc_linear__ps0p05` | `wait_on_conflict` | 4.973821 | 4.893489 | -0.080332 |
| `wc_linear__ps0p05` | `risk_threshold` | 6.495662 | 6.575950 | 0.080288 |
| `wc_linear__ps0p10` | `always_act` | 4.788806 | 4.715742 | -0.073065 |
| `wc_linear__ps0p10` | `always_wait` | 8.150160 | 8.223137 | 0.072976 |
| `wc_linear__ps0p10` | `wait_on_conflict` | 5.106229 | 5.026133 | -0.080096 |
| `wc_linear__ps0p10` | `risk_threshold` | 7.832738 | 7.912745 | 0.080007 |
| `wc_linear__ps0p20` | `always_act` | 4.788806 | 4.715742 | -0.073065 |
| `wc_linear__ps0p20` | `always_wait` | 11.089127 | 11.162015 | 0.072888 |
| `wc_linear__ps0p20` | `wait_on_conflict` | 5.371045 | 5.291421 | -0.079623 |
| `wc_linear__ps0p20` | `risk_threshold` | 10.506889 | 10.586335 | 0.079447 |
| `wc_quadratic__k0p00` | `always_act` | 4.788806 | 4.715742 | -0.073065 |
| `wc_quadratic__k0p00` | `always_wait` | 6.939587 | 7.012561 | 0.072973 |
| `wc_quadratic__k0p00` | `wait_on_conflict` | 4.997083 | 4.916788 | -0.080294 |
| `wc_quadratic__k0p00` | `risk_threshold` | 6.731311 | 6.811514 | 0.080203 |
| `wc_quadratic__k0p01` | `always_act` | 4.788806 | 4.715742 | -0.073065 |
| `wc_quadratic__k0p01` | `always_wait` | 13.853162 | 13.925770 | 0.072608 |
| `wc_quadratic__k0p01` | `wait_on_conflict` | 5.619761 | 5.540561 | -0.079200 |
| `wc_quadratic__k0p01` | `risk_threshold` | 13.022207 | 13.100951 | 0.078744 |

## Notes
- This summary requires `sweep_summary.json` per sweep. If missing, run:
  - `exp-suite summarize-sweep --sweep-dir <sweep_dir>` (or `summarize-sweep-metrics` if using recomputed metrics)

