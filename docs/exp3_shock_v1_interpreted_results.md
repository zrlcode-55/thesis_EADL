## Exp3 interpreted results (shock v1)

### Exp3 identity gate (exp3_shock_v1_gate)

- **Claim tested**: Exp3 with `shock.shape=identity` (multiplier always 1.0) reduces exactly to Exp2 on the same base-point set.
- **Result**: passed = **True**
- **Compared**: 12 base points × 4 policies × 5 metrics
- **Worst absolute difference (Exp3(identity) vs Exp2)**: 0 on `M3_avg_cost` for policy `always_act` at base point `wc_exponential__k0p25__a0p05`
- **Cross-reference table**: `artifacts\exp3_shock_v1_gate__exp2_vs_exp3_identity__metrics.csv`
- **Audit artifact (original prereg gate)**: `artifacts/exp3_identity_reduction_gate.json`

### Exp3 full shock sweep (exp3_shock_v1_48sweeps)

- **What changes in Exp3**: the loss function is evaluated under a time-varying multiplier `m(t)` applied to `cost_false_act`, `cost_false_wait`, and `wait_cost`.
- **Important implementation detail**: `shock.shape=step` **does not use** `duration_frac`; it applies `m(t)=mag` for all `t >= start_frac`.
- **Cross-reference tables**:
  - `artifacts\exp3_shock_v1_48sweeps__A__metrics.csv`
  - `artifacts\exp3_shock_v1_48sweeps__B__metrics.csv`

#### Seed set A: strongest observed shock-induced average-cost increase (mean over base points)

- **always_act**: Δavg_cost_vs_noshock ≈ **28.4448** under `step` mag=10 start=0.2 dur=0.2
- **always_wait**: Δavg_cost_vs_noshock ≈ **76.1413** under `step` mag=10 start=0.2 dur=0.2
- **risk_threshold**: Δavg_cost_vs_noshock ≈ **60.7938** under `step` mag=10 start=0.2 dur=0.2
- **wait_on_conflict**: Δavg_cost_vs_noshock ≈ **32.8648** under `step` mag=10 start=0.2 dur=0.2

#### Seed set A: policy-behavior invariance checks vs identity (max absolute delta)

- **M5_deferral_rate**: 0
- **M1_correctness_rate**: 0

#### Seed set B: strongest observed shock-induced average-cost increase (mean over base points)

- **always_act**: Δavg_cost_vs_noshock ≈ **27.9023** under `step` mag=10 start=0.2 dur=0.2
- **always_wait**: Δavg_cost_vs_noshock ≈ **76.681** under `step` mag=10 start=0.2 dur=0.2
- **risk_threshold**: Δavg_cost_vs_noshock ≈ **61.2879** under `step` mag=10 start=0.2 dur=0.2
- **wait_on_conflict**: Δavg_cost_vs_noshock ≈ **32.275** under `step` mag=10 start=0.2 dur=0.2

#### Seed set B: policy-behavior invariance checks vs identity (max absolute delta)

- **M5_deferral_rate**: 0
- **M1_correctness_rate**: 0
