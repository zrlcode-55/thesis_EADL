### Advisor Checkpoint: Exp3 Go / No-Go Gate (Prereg-style note)

This note is written to satisfy the advisor checkpoint list **I–X** prior to running Experiment 3.

**Exp3 design in this repo**
- **Base points**: 12 (inherited from `configs/locked/exp2_policy_v2_16pt/`)
- **Shock keys**: 4 (hypothesis-driven, includes identity control)
- **Total Exp3 sweep points**: \(12 \times 4 = 48\)
- **Holdout**: Seed Set A and B share identical sweep points; only seeds differ

---

### I. Estimand clarity (one sentence)
**Exp3 estimates whether decision policies that are stable and interpretable under stationary semantics (Exp2) remain stable under time-varying cost shocks, and whether tail risk becomes shock-dominated even when mean ordering is preserved.**

Non-goals (explicit):
- Not optimizing policies
- Not claiming “better performance” in a stationary sense
- Not resweeping base semantics

---

### II. Single-variable intervention test
#### Variables held fixed from Exp2
- **Evidence + uncertainty + reconciliation**: identical schemas and codepaths (same artifact formats and metric computation)
- **Cost accounting logic**: identical loss accounting *implementation* (only input cost parameters may be multiplied by shocks)
- **Policy implementations**: identical policies (`always_act`, `always_wait`, `wait_on_conflict`, `risk_threshold`)
- **Seed discipline**: matched seed ranges; A/B differ only by seed values
- **Base point set**: inherited deterministically from locked Exp2 configs (`exp2_policy_v2_16pt`)

#### Variables allowed to change in Exp3 (exactly one)
- **`shock_schedule(t)` applied as a multiplier to declared cost parameters over time**

---

### III. Reduction check (non-negotiable)
We must verify: **Exp3(identity shock) reduces to Exp2** on shared metrics, using the *actual* base-point set and matched seeds.

#### Procedure (recorded)
Run:
- `scripts/run_exp3_go_nogo_gate.ps1`

This performs:
- Exp2: `exp-suite exp2-policy-run` on all 12 base points with seeds 0–2
- Exp3(identity): `exp-suite exp3-shock-run` on the corresponding identity-shock points with seeds 0–2
- Summarization + comparison into a single JSON report

#### Acceptance criterion (predeclared)
For each base point × policy × metric below, comparing **Exp3(identity)** vs **Exp2**:
- Metrics: `M3_avg_cost`, `M4_p95_cost`, `M4_p99_cost`, `M5_deferral_rate`, `M2_mean_wait_seconds_when_wait`
- Tolerance: **abs ≤ 1e-9** (rel tol = 0.0)

#### Artifact (attachable)
- `artifacts/exp3_identity_reduction_gate.json`

If this gate fails, **Exp3 is invalid** until fixed.

---

### IV. Base point justification (why 12, and why these)
Source-of-truth base points:
- `configs/locked/exp2_policy_v2_16pt/`

They span wait-cost families and intensities (stationary regimes), so Exp3 does **not** resweep semantics:
- **Linear**: `ps0p01`, `ps0p02`, `ps0p05`, `ps0p10`, `ps0p20`
- **Quadratic**: `k0p00`, `k0p01`
- **Exponential**: `k0p25__a0p05`, `k0p50__a0p05`, `k0p50__a0p10`, `k1p00__a0p05`, `k1p00__a0p10`

Rationale:
- Exp2 already established stationary behavior across these families; Exp3 allocates density to **non-stationarity**.

---

### V. Shock design justification (minimal, hypothesis-driven basis)
Shock set is intentionally small and legible; each key targets a qualitative failure mode:

| Shock key | Tests |
|---|---|
| identity (1×, early) | reduction / control (“Exp3 reduces to Exp2 when shocks are disabled”) |
| step-early (10×) | early commitment sensitivity |
| step-late (10×) | delayed correction sensitivity |
| ramp-early (2×) | gradual drift vs abrupt shock |

This covers: **control + phase sensitivity + severity + shape** without grid explosion.

---

### VI. Holdout meaning
Seed sets:
- **A**: seeds 0–29
- **B**: seeds 30–59

Holdout definition (strict):
- A and B use **identical base points × shock keys**
- Only seeds differ

If points differ, it must be labeled **domain shift**, not holdout.

---

### VII. Stop criteria (predeclared)
Define “enough” vs “expand” before running:

Stop after Seed Set A (no expansion) if:
- ≥80% of sweeps show **tail amplification**: `E3_p99_amplification > 1.0` and
- The amplification pattern repeats across multiple base points and policies (not a single outlier)

Expand (add shock keys, not base points) if:
- A/B sign stability on per-sweep `E3_p99_amplification - 1` is <90% on the overlap set, or
- Observed shock exposure diagnostics suggest insufficient coverage (e.g., `E3_frac_decisions_under_shock` near 0 for most points)

---

### VIII. Negative result plan
If Exp3 shows no amplification/instability under the tested shocks, this means:
- The Exp2-derived policies are **robust under the tested non-stationarity**, within the tested magnitudes/timings
- The thesis claim is bounded: robustness holds **in the evaluated shock regime**, not universally
- If needed, the follow-up is to expand **shock severity/timing**, not to resweep base semantics

---

### IX. Metrics discipline (predeclared roles)
Primary (Exp3-specific):
- `E3_p99_amplification`
- `E3_policy_churn_rate_mean`

Audit / sanity:
- `M1_correctness_rate`
- `M3b_avg_regret_vs_oracle`
- Identity-reduction gate report (`artifacts/exp3_identity_reduction_gate.json`)

Descriptive:
- `M3_avg_cost`, `M4_p95_cost`, `M4_p99_cost`, `M5_deferral_rate`, `M2_mean_wait_seconds_when_wait`
- `E3_frac_decisions_under_shock`, `E3_shock_multiplier_mean/max`

---

### X. Claim bounding (pre-written)
Approved claim templates:
- “Across the sampled **48 Exp3 shock regimes** (12 inherited base points × 4 preregistered shock keys) …”
- “Within the tested shock magnitudes and timings …”
- “We do not claim global optimality or full regime coverage; results are bounded to the preregistered sweep set.”


