### Experiment 2 → Experiment 3 handoff (thesis-ready)

Experiment 3 is a **single-variable perturbation** of the Experiment 2 apparatus. Experiment 2 establishes that the decision-policy layer is a controlled and stable subsystem under fixed state semantics: the evidence stream, uncertainty representation, aggregation, reconciliation semantics, and loss accounting are held constant while **only the decision policy** and **WAIT-cost curvature** vary at the commit boundary. Sanity checks confirm correct policy wiring (e.g., `always_act` and `always_wait` deferral behavior), and A/B holdout behavior is stable across representative wait-cost families.

- **Exp2 artifact anchors**:
  - `docs/experiment_2_policy_summary__8pt.md` (initial policy sweep)
  - `docs/experiment_2_policy_summary__v2_policy.md` (expanded coverage sweep; A/B holdout)

Experiment 3 inherits this validated apparatus unchanged and introduces one additional degree of freedom: **time-varying exogenous shocks to the cost regime** (non-stationary loss and/or waiting-cost scaling). The goal is not to “re-optimize” policies, but to measure whether policy behavior that is interpretable and stable in stationary regimes remains well-behaved under shock dynamics (stability vs oscillation/amplification), and whether tail-risk exposure (p95/p99) becomes shock-dominated even when mean-cost ordering is unchanged.

### Preregistered vs audit metrics (explicit)
Exp2 preregisters measurement of **cost aggregates**, **tail costs**, and **induced delay**. In this thesis, **correctness/regret-style metrics** are treated as **audit/sanity metrics** to validate instrumentation and policy wiring; they are not used to retroactively redefine Exp2’s primary outcome.

### Dependency invariants (Exp3 must inherit Exp2 exactly)
To prevent “changing two things at once,” Exp3 should enforce an explicit inheritance contract:

- **Must be identical to Exp2**:
  - Evidence generation / replay seed discipline
  - State semantics / representation (fixed semantics regime)
  - Action space and commit semantics
  - Reconciliation generation and alignment
  - Cost accounting implementation (same loss functions; same metric computation codepaths)
  - Policy implementations (same `policy_id` behaviors)
- **Only allowed new variable in Exp3**:
  - A shock schedule/model \(shock\_schedule(t)\) that modulates declared cost parameters over time

### Mechanical safeguards (pre-run gating)
Before any Exp3 sweep runs:

- **Policy wiring gate**: verify `always_act` deferral rate ≈ 0 and `always_wait` deferral rate ≈ 1 on a small smoke run.
- **No-shock equivalence gate**: run Exp3 with \(shock\_schedule(t)=1\) (identity). Metrics must match Exp2 within a declared tolerance.

If both gates pass, it is defensible to state: **“When shocks are disabled, Experiment 3 reduces to Experiment 2; therefore deviations under shock are attributable to the introduced shock variable rather than configuration drift.”**

### Artifact lineage (audit trail)
Every Exp3 artifact should record enough lineage to make inheritance machine-checkable:

- `parent_exp2_sweep_id`, `parent_exp2_point_key`
- Code version identifiers (git revision; dependency lockfile hash if applicable)
- Shock model id + parameters + shock seed

### Suggested Exp3 sweep density (interpretable, bounded)
Exp3 density should be in the **shock dimension** (Exp2 already covers stationary wait-cost families). A minimal, interpretable grid:

- **Shock shape (3)**: step / impulse / ramp  
- **Shock magnitude (4)**: 1× control, 2×, 5×, 10×  
- **Shock timing (2)**: early vs late in episode  

Total: \(3 \times 4 \times 2 = 24\) points (optionally add a volatility axis only if preregistered).

### Exp3 measurements (additive, shock-specific)
Keep Exp2’s primary and tail metrics, and add two shock-specific ones:

- **Policy stability / churn**: number of `ACT↔WAIT` flips per entity or per time window
- **Shock amplification factor**: \(p99\_cost\_\text{shock} / p99\_cost\_\text{no-shock}\)