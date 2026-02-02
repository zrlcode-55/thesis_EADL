### Experiment 3 — Full Summary (Shock v1, preregistered sweep)

This report is **artifact-derived** and intended as the Exp3 analog of `docs/experiment1_full_summary.md`.

## Executive summary (thesis-ready, citation-safe)
- **Estimand**: whether Exp2-stable policies remain well-behaved under time-varying cost shocks, and whether tail risk becomes shock-dominated.
- **Base points**: 12 (inherited from `configs/locked/exp2_policy_v2_16pt/`).
- **Shock keys**: 4 (identity, step-early 10×, step-late 10×, ramp-early 2×).
- **Total sweeps per seed set**: 48 (= 12 × 4).
- **Policies per sweep**: 4 (`always_act`, `always_wait`, `wait_on_conflict`, `risk_threshold`).
- **Seeds**: A=0–29, B=30–59 (strict holdout: same sweep points, different seeds).

## Data inclusion + integrity checks (paper-safe)
- **Seed Set A sweeps found**: 48 (expected 48); finalized+seed-OK: **48**
- **Seed Set B sweeps found**: 48 (expected 48); finalized+seed-OK: **48**
- Inclusion rule: a sweep is included iff `sweep_progress.json.last_run_id == "FINALIZED"`, `completed==total`, and `sweep_manifest.json.seeds` exactly matches the preregistered seed range.

## Hypotheses (as preregistered) and what we observed
- Source prereg: `docs/exp3_go_no_go_prereg.md` (see **V** shock design + **IX** metrics discipline + **X** claim bounding).
- **H0 / Control**: identity shock should reduce to Exp2 (no-shock equivalence).
  - **Observed**: gate passed = **True**; worst abs diff = 0.0.
- **H1 / Severity**: strong shocks increase tail risk (primary metric: `E3_p99_amplification`).
  - **Observed**: step-early 10× drives the largest amplification in this preregistered set.
- **H2 / Phase sensitivity**: early vs late step shocks differ (expected: early > late due to longer exposure).
- **H3 / Shape**: ramp (2×) produces different amplification patterns than step (10×).

## Holdout stability (A vs B)
- **Primary (E3_p99_amplification)**: n=192, Pearson r=0.9999999533258395, sign agreement=144/144
- **Δavg_cost_vs_noshock**: n=192, Pearson r=0.9999393813655039, sign agreement=144/144

- **Policy churn (E3_policy_churn_rate_mean)**: n=192, Pearson r=0.9999999999999983, sign agreement=92/92

## Scenario results (Seed Set A; mean over base points)
Rows are **shock key × policy**. Values are the mean (across the 12 base points) of the per-sweep per-policy mean metric.

| shock_key | policy | E3_p95_amp | E3_p99_amp | Δavg_cost_vs_noshock | churn_rate |
|---|---:|---:|---:|---:|---:|
| identity | always_act | 1 | 1 | 0 | 0 |
| identity | always_wait | 1 | 1 | 0 | 0 |
| identity | wait_on_conflict | 1 | 1 | 0 | 0.164217 |
| identity | risk_threshold | 1 | 1 | 0 | 0.150532 |
| ramp_early_2x | always_act | 2 | 2 | 2.53801 | 0 |
| ramp_early_2x | always_wait | 1.99804 | 1.99895 | 7.57099 | 0 |
| ramp_early_2x | wait_on_conflict | 1.92305 | 1.99665 | 3.00152 | 0.164217 |
| ramp_early_2x | risk_threshold | 1.99856 | 1.99924 | 6.01918 | 0.150532 |
| step_late_10x | always_act | 10 | 10 | 7.49495 | 0 |
| step_late_10x | always_wait | 9.96183 | 9.98065 | 31.7249 | 0 |
| step_late_10x | wait_on_conflict | 9.27298 | 9.92936 | 9.71628 | 0.164217 |
| step_late_10x | risk_threshold | 9.97204 | 9.9864 | 24.9262 | 0.150532 |
| step_early_10x | always_act | 10 | 10 | 28.4448 | 0 |
| step_early_10x | always_wait | 9.99751 | 9.99845 | 76.1413 | 0 |
| step_early_10x | wait_on_conflict | 9.64185 | 9.99603 | 32.8648 | 0.164217 |
| step_early_10x | risk_threshold | 9.99813 | 9.99898 | 60.7938 | 0.150532 |

Seed Set B reproduces these patterns with near-perfect correlation (see holdout stats above).

## Preregistered comparisons (Seed Set A; mean over base points)
- **Step early 10× − step late 10×** (positive means early > late):
  - E3_p99_amplification / always_act: 0
  - E3_p99_amplification / always_wait: 0.0177963
  - E3_p99_amplification / risk_threshold: 0.0125777
  - E3_p99_amplification / wait_on_conflict: 0.0666651
  - E3_delta_avg_cost_vs_noshock / always_act: 20.9498
  - E3_delta_avg_cost_vs_noshock / always_wait: 44.4164
  - E3_delta_avg_cost_vs_noshock / risk_threshold: 35.8676
  - E3_delta_avg_cost_vs_noshock / wait_on_conflict: 23.1485
- **Step early 10× − ramp early 2×** (positive means step > ramp):
  - E3_p99_amplification / always_act: 8
  - E3_p99_amplification / always_wait: 7.9995
  - E3_p99_amplification / risk_threshold: 7.99973
  - E3_p99_amplification / wait_on_conflict: 7.99937
  - E3_delta_avg_cost_vs_noshock / always_act: 25.9068
  - E3_delta_avg_cost_vs_noshock / always_wait: 68.5703
  - E3_delta_avg_cost_vs_noshock / risk_threshold: 54.7746
  - E3_delta_avg_cost_vs_noshock / wait_on_conflict: 29.8633

## Tail amplification prevalence (Seed Set A)
Fraction of base points with **E3_p99_amplification > 1.0** (per shock × policy):

| shock_key | policy | frac_gt1 |
|---|---:|---:|
| identity__m1.0__s0.2__d0.2 | always_act | 0 |
| identity__m1.0__s0.2__d0.2 | always_wait | 0 |
| identity__m1.0__s0.2__d0.2 | risk_threshold | 0 |
| identity__m1.0__s0.2__d0.2 | wait_on_conflict | 0 |
| ramp__m2.0__s0.2__d0.2 | always_act | 1 |
| ramp__m2.0__s0.2__d0.2 | always_wait | 1 |
| ramp__m2.0__s0.2__d0.2 | risk_threshold | 1 |
| ramp__m2.0__s0.2__d0.2 | wait_on_conflict | 1 |
| step__m10.0__s0.2__d0.2 | always_act | 1 |
| step__m10.0__s0.2__d0.2 | always_wait | 1 |
| step__m10.0__s0.2__d0.2 | risk_threshold | 1 |
| step__m10.0__s0.2__d0.2 | wait_on_conflict | 1 |
| step__m10.0__s0.7__d0.2 | always_act | 1 |
| step__m10.0__s0.7__d0.2 | always_wait | 1 |
| step__m10.0__s0.7__d0.2 | risk_threshold | 1 |
| step__m10.0__s0.7__d0.2 | wait_on_conflict | 1 |

## Cross-reference artifacts (what to cite)
- Gate: `artifacts/exp3_identity_reduction_gate.json` and `artifacts/exp3_shock_v1_gate__exp2_vs_exp3_identity__metrics.csv`
- Exp3 point-level tables:
  - `artifacts/exp3_shock_v1_48sweeps__A__metrics.csv`
  - `artifacts/exp3_shock_v1_48sweeps__B__metrics.csv`
- Exp3 scenario-level aggregates: `artifacts/exp3_shock_v1_48sweeps__summary_full.json`

## Notes / limitations (explicit)
- In this sweep, shocks multiply **all** cost components (`cost_false_act`, `cost_false_wait`, `wait_cost`) by the same multiplier, so decision boundaries for `risk_threshold` are invariant to shocks (both sides scale equally).
- `shock.shape=step` persists from `start_frac` to end of episode (it does **not** use `duration_frac`).
