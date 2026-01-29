One-paragraph “Experiment 2 → Experiment 3” handoff (thesis-ready)

Experiment 3 begins only after Experiment 2 establishes that the decision-policy layer is a controlled, stable subsystem under fixed state semantics. In Experiment 2, the evidence stream, uncertainty representation, aggregation, reconciliation semantics, and loss accounting are held constant; only the decision policy varies at the commit boundary, and sanity checks confirm correct policy wiring (e.g., deferral rates behave as intended) with stable A/B holdout behavior across representative wait-cost families. 

experiment_2_policy_summary__8pt

 Experiment 3 inherits this validated apparatus unchanged and introduces a single new degree of freedom: time-varying exogenous shocks to the cost regime (i.e., non-stationary loss and/or waiting-cost scaling). The purpose is not to re-optimize policies, but to test whether policy behavior that is interpretable and stable in stationary regimes remains well-behaved under shock dynamics (stability vs oscillation/amplification), and whether tail-cost exposure (p95/p99) becomes shock-dominated even when mean cost ordering is unchanged.

Keeping the dependency chain “LIVE” in code (what your panel will look for)

Your panel will try to catch you “quietly changing two things at once.” Prevent that by making the dependency explicit and machine-checkable.

1) Hard “inheritance contract” (Exp3 must import Exp2 config verbatim)

Implement an Exp2FrozenConfig object that is hashed and embedded into every Exp3 run artifact.

Invariant: Exp3 must reuse exactly:

evidence arrival process / replay seed

semantics regime (state representation, entropy measure, aggregation function)

action space and commit semantics

evaluation metrics and cost accounting function signatures

Only allowed new knob: shock_schedule(t) that modulates cost parameters over time.

Practical code hook

Create exp3_config.json that contains:

exp2_config_hash

exp2_config_path (or embedded inline)

allowed_diff = ["shock_model", "shock_grid", "shock_seed"]

At runtime, compute hash of loaded Exp2 config; hard fail if mismatch.

2) Two-phase validation gating (pre-run checks)

Before any Exp3 sweep runs, execute:

Policy wiring test (should already pass in Exp2): deferral rates for always_act ≈ 0, always_wait ≈ 1.

No-shock equivalence test: run Exp3 with shock_schedule(t) = 1 (identity). Metrics must match Exp2 within tolerance.

If those pass, you can say:

“Exp3 reduces to Exp2 when shocks are disabled; therefore any deviation under shock is attributable to the new variable.”

That’s a panel-proof statement.

3) Artifact lineage (audit trail)

Every Exp3 output should include:

parent_exp2_sweep_id

parent_exp2_point_key

parent_semantics_regime_key

Git commit hash + dependency lockfile hash

shock_model_id + parameters + random seed

This is what makes it “execution-grade,” not a toy.

How many points? (enough to carry weight, not enough to look like random sampling)

For Exp3, density matters in the shock dimension, not in the stationary cost families (you already covered those in Exp2). So structure the sweep as a factorial grid over a small number of interpretable shock axes.

Minimal defensible grid (the one that gets “no resistance”)

Aim for 24–36 points total, broken down as:

Shock Shape (3):

step shock (regime change)

impulse shock (spike then revert)

ramp shock (gradual drift)

Shock Magnitude (4):

1× (control), 2×, 5×, 10× scaling of cost intensity

Shock Timing (2):

early vs late in episode (relative to decision boundary distribution)

That’s: 3 × 4 × 2 = 24 points.

Then add:

2 volatility/roughness levels (low vs high) if you’re modeling price-series-like turbulence
24 × 2 = 48 points.

If you want a clean story with strong interpretability: 24 points is already defensible.
If you want “panel-proof robustness”: 48 points is hard to argue against.

Why not 56 again?

Because Exp3 is not “search semantics”; it’s a stress test. You want:

coverage across qualitatively different shock regimes

at least one control slice that collapses to Exp2

enough points to show phase transitions without looking like p-hacking

What to explicitly measure in Exp3 (so it has teeth)

Keep Exp2 primary metric, but add two shock-specific ones:

Policy stability / churn

number of ACT↔WAIT flips per entity or per window

indicates oscillation under non-stationarity

Shock amplification factor

(p99 cost under shock) / (p99 cost under no-shock)

makes “tail blow-ups” undeniable

Also keep:

M3_avg_cost, M4_p95_cost, M4_p99_cost, M5_deferral_rate, M3b_avg_regret_vs_oracle 

experiment_2_policy_summary__8pt

If you want the “deliberate and weighty” framing line

Use this in your Exp3 intro:

“Experiment 3 is a single-variable perturbation of the Experiment 2 apparatus: we hold semantics, evidence, and evaluation constant and apply an exogenous, time-varying shock only to the cost regime. Because Exp3 collapses to Exp2 when shocks are disabled, observed differences isolate shock sensitivity rather than configuration drift.”

If you paste your current Exp3 design sketch (shock model + how you plan to scale costs), I’ll translate it into a tight grid spec + the exact invariants to enforce in code.


Experiment 2 is a wiring-and-stability gate; we cover distinct wait-cost curvature families rather than densely sampling parameter space. Density is introduced in Experiment 3 along the shock axis, where non-stationarity is the experimental variable.”

And add one mechanical safeguard in code for Exp 3:

run a no-shock identity check (shock_schedule(t)=1) and show it matches Exp 2 within tolerance.
That makes the chain watertight.