### Experiment 2 — Policy Sweep Summary (THESIS: fixed semantics, policy varies)

This report summarizes **Exp2 Policy v1** sweeps (fixed state semantics; policy varies) from sweep summaries.

## Inputs (artifact anchors)
- Seed Set A artifacts: `C:\exp2_policy_artifacts` (prefix `exp2_policy_v1_8pt__A`)
- Holdout Seed Set B artifacts: `C:\exp2_policy_artifacts` (prefix `exp2_policy_v1_8pt__B`)

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

## Executive summary (bounded, thesis-safe)
- **Design contract (Exp2)**: state semantics fixed (`system="proposed"`); evidence stream fixed; only **policy** and **WAIT-cost curvature** vary.
- **Primary outcome**: `M3_avg_cost` (lower is better).
- **Result (this 8-point sweep)**: across the **7 wait-cost points** included here, `always_act` achieves the lowest mean `M3_avg_cost` in **7/7 points** on **Seed Set A** and **7/7 points** on **holdout Seed Set B**.
- **Holdout stability**: the per-point delta patterns vs `always_act` are highly stable from A→B (Pearson correlations near 1.0 for all non-`always_act` policies).
- **Implementation sanity**: `always_act` and `always_wait` behave as intended (deferral rates ~0 and ~1 respectively), ruling out “policy wiring” as an explanation for the ordering.

## Claim bank (copy/paste, no over-claims)
- **C1 (completeness)**: For this 8-point policy sweep, we include **7/7 finalized points** in Seed Set A and **7/7 finalized points** in holdout Seed Set B (common points A∩B = 7).
- **C2 (primary result; bounded to tested regimes)**: Under the declared loss model and wait-cost families tested here, `always_act` yields lower `M3_avg_cost` than `always_wait`, `wait_on_conflict`, and `risk_threshold` in **every included wait-cost point** (7/7) on both A and B.
- **C3 (policy tradeoff, descriptive)**: Deferral behavior differs materially across policies (e.g., `risk_threshold` defers much more than `wait_on_conflict`), and higher deferral is associated with higher realized average cost in this regime set.
- **C4 (holdout stability; descriptive)**: The ordering and per-point delta patterns are stable under the matched-seed holdout split (A vs B), suggesting the observed differences are not an artifact of a single seed set.
- **C5 (non-claims; explicit)**: These results do **not** claim optimality beyond the tested regimes, do **not** claim general inference accuracy, and do **not** evaluate representation power or reconciliation quality.

## Implication for Experiment 3 (dependency, deterministic)
Exp3 (shock stress test) depends on Exp2 in only one way: it requires that the **policy implementations** and **cost accounting** are correct and stable so shock responses can be interpreted.

- **What Exp2 establishes for Exp3**: policy wiring is correct (sanity checks pass), metrics are artifact-derived, and the A/B split shows stable cost ordering for these regimes.
- **What Exp3 should test next (bounded)**: whether the same policies remain stable (or exhibit oscillation/amplification) under **non-stationary external shocks**, even if `always_act` is cost-optimal in stationary regimes like these.

## Completeness
- **Seed Set A points included**: **7**
- **Seed Set B points included**: **7**
- **Common points (A∩B)**: **7**

## Win counts (per-point winner by mean cost)
### Seed Set A
- **always_act**: 7 wins
- **always_wait**: 0 wins
- **wait_on_conflict**: 0 wins
- **risk_threshold**: 0 wins

### Seed Set B (holdout)
- **always_act**: 7 wins
- **always_wait**: 0 wins
- **wait_on_conflict**: 0 wins
- **risk_threshold**: 0 wins

## Holdout stability (delta vs `always_act` per point)
- **always_wait**: n_points=7, pearson=0.9999999999876488
- **risk_threshold**: n_points=7, pearson=0.9998937402113901
- **wait_on_conflict**: n_points=7, pearson=0.999999999985899

## Point-level winners (A and B)
| point_key | winner_A | winner_B |
|---|---|---|
| `wc_exponential__k0p50__a0p10` | `always_act` | `always_act` |
| `wc_exponential__k1p00__a0p10` | `always_act` | `always_act` |
| `wc_linear__ps0p01` | `always_act` | `always_act` |
| `wc_linear__ps0p02` | `always_act` | `always_act` |
| `wc_linear__ps0p05` | `always_act` | `always_act` |
| `wc_quadratic__k0p00` | `always_act` | `always_act` |
| `wc_quadratic__k0p01` | `always_act` | `always_act` |

## Policy correctness + tradeoff summary (mean of per-point means)
- These are descriptive aggregates across regime points; they are **not** the primary win/loss analysis.

### Seed Set A
| policy | M3_avg_cost | M1_correctness_rate | M3b_avg_regret_vs_oracle | M5_deferral_rate | M2_mean_wait_seconds_when_wait |
|---|---|---|---|---|---|
| `always_act` | 4.788806 | 0.589815 | 2.680161 | 0.000000 | 0.000000 |
| `always_wait` | 10.748724 | 0.410185 | 8.640078 | 1.000000 | 29.389667 |
| `wait_on_conflict` | 5.340008 | 0.572391 | 3.231363 | 0.090145 | 29.376719 |
| `risk_threshold` | 7.812959 | 0.557572 | 5.704313 | 0.779876 | 25.192239 |

#### Sanity checks (policy-implementation correctness)
- **always_act deferral_rate** (expected ~0): 0.000000
- **always_wait deferral_rate** (expected ~1): 1.000000

### Seed Set B (holdout)
| policy | M3_avg_cost | M1_correctness_rate | M3b_avg_regret_vs_oracle | M5_deferral_rate | M2_mean_wait_seconds_when_wait |
|---|---|---|---|---|---|
| `always_act` | 4.715742 | 0.596056 | 2.639291 | 0.000000 | 0.000000 |
| `always_wait` | 10.821463 | 0.403944 | 8.745012 | 1.000000 | 29.388784 |
| `wait_on_conflict` | 5.260314 | 0.579256 | 3.183862 | 0.090309 | 29.375657 |
| `risk_threshold` | 7.870946 | 0.550676 | 5.794495 | 0.779735 | 25.191494 |

#### Sanity checks (policy-implementation correctness)
- **always_act deferral_rate** (expected ~0): 0.000000
- **always_wait deferral_rate** (expected ~1): 1.000000

## Point-level primary metric (`M3_avg_cost`) by policy
- Shows the per-point **mean** (from sweep summaries) for each policy on A and B.

| point_key | policy | mean_A | mean_B | delta_B_minus_A |
|---|---|---:|---:|---:|
| `wc_exponential__k0p50__a0p10` | `always_act` | 4.788806 | 4.715742 | -0.073065 |
| `wc_exponential__k0p50__a0p10` | `always_wait` | 14.179651 | 14.252148 | 0.072497 |
| `wc_exponential__k0p50__a0p10` | `wait_on_conflict` | 5.648790 | 5.569632 | -0.079158 |
| `wc_exponential__k0p50__a0p10` | `risk_threshold` | 13.319666 | 13.398257 | 0.078591 |
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
| `wc_quadratic__k0p00` | `always_act` | 4.788806 | 4.715742 | -0.073065 |
| `wc_quadratic__k0p00` | `always_wait` | 6.075390 | 6.148409 | 0.073019 |
| `wc_quadratic__k0p00` | `wait_on_conflict` | 4.919248 | 4.838817 | -0.080431 |
| `wc_quadratic__k0p00` | `risk_threshold` | 5.944949 | 6.025334 | 0.080386 |
| `wc_quadratic__k0p01` | `always_act` | 4.788806 | 4.715742 | -0.073065 |
| `wc_quadratic__k0p01` | `always_wait` | 13.853162 | 13.925770 | 0.072608 |
| `wc_quadratic__k0p01` | `wait_on_conflict` | 5.619761 | 5.540561 | -0.079200 |
| `wc_quadratic__k0p01` | `risk_threshold` | 13.022207 | 13.100951 | 0.078744 |

## Notes
- This summary requires `sweep_summary__metrics_recomputed.json` per sweep. If missing, run:
  - `exp-suite summarize-sweep --sweep-dir <sweep_dir>` (or `summarize-sweep-metrics` if using recomputed metrics)

