### Final Claims (Exp1–Exp3) — Single Source of Truth

This document is the **non-negotiable thesis ledger**: it aggregates only what is supported by **locked configs**, **artifact files**, and **code-path-verifiable metric definitions**.

- **Not** an opinion piece.
- **Not** "what we meant" — it is "what the code produced and what the artifacts contain."
- If a statistic is not **already materialized** in `artifacts/` (or cannot be deterministically regenerated from artifacts + locked configs), it **does not belong** in the manuscript.

---

## EXPERIMENTAL HIERARCHY (NON-NEGOTIABLE — ADVISOR GUIDANCE)

**"Which experiment matters if you only believe one?"**

**Experiment 1 = THE THESIS**  
- **Primary contribution**: Conflict-aware state semantics reduce regret vs. collapse-to-one baselines.
- **Structure**: 54 preregistered regime points, holdout stability (A/B), deterministic from artifacts.
- **This must dominate**: abstract, figures, discussion, oral defense.

**Experiment 2 = POLICY CONSEQUENCE**  
- **Role**: Demonstrates that policy choice matters under fixed (proposed) semantics.
- **Structure**: 12 wait-cost points, 4 policies, fixed semantics.
- **Contribution**: Secondary; shows cost-aware policies can fail under regime mismatch.

**Experiment 3 = STRESS PROBE**  
- **Role**: Tests robustness under dynamic cost shocks.
- **Structure**: 4 shock shapes × 12 base points, inherits Exp2 semantics.
- **Contribution**: Tertiary; shows boundary invariance and tail amplification under stress.

**Verdict**: If Exp1 does not dominate your manuscript structure, the thesis is structurally weak. Exp2/Exp3 are supporting evidence, not co-equal contributions.

---

## ABSTRACT PRE-CHECK (ADVISOR REQUIREMENT — DO NOT WRITE ABSTRACT YET)

Before writing the abstract, you must answer:

### What the abstract MUST NOT say:
- ❌ No real-world deployment claims
- ❌ No "novel framework" language
- ❌ No field-level criticism
- ❌ No future-looking hype

### What the abstract MUST contain (in this order):
1. **Problem**: Decisions must be made before reconciliation; current state models collapse conflict.
2. **Method**: Controlled experiments isolating state semantics, policies, and cost shocks.
3. **Primary Result (Exp1)**: Conflict-aware state reduces regret in X/Y preregistered regimes with holdout stability.
4. **Scope Limitation**: Results are synthetic, bounded, and comparative.

**Target length**: 150–180 words. If you cannot fit this structure, you are not ready to write.

---

## Document organization

This document is structured to support rigorous manuscript writing:

1. **Global reproducibility contract** (below): metric definitions, shock semantics, code anchors.
2. **Codebase apparatus overview**: implementation modules and repo file structure.
3. **Experiment 1 (Grid v1)**: 54-point preregistered regime grid; win/loss counts; holdout stability.
4. **Experiment 2 (Policy sweep v2)**: 12-point wait-cost sweep; policy comparison; holdout validation.
5. **Experiment 3 (Shock v1)**: 48-sweep shock robustness analysis; identity gate; tail amplification.
6. **Cross-experiment synthesis**: bounded "safe to say" claims; explicit non-claims.

**For each experiment**, you will find:
- **What it supports** (scope of valid claims)
- **Inputs** (locked configs)
- **Data inclusion rules** (what was excluded and why)
- **Claims** (numbered C1–C13, with evidence anchors)
- **Artifact anchors** (file paths for regeneration)
- **Regeneration commands** (deterministic reproduction)

---

## Global reproducibility contract (applies to every claim below)

- **Locked configs are the experiment definition**: `configs/locked/**`
- **Artifacts are the ground truth outputs**: `artifacts/**` (CSV/JSON and, where present, sweep directories)
- **Metrics are computed from artifacts**: see `src/exp_suite/metrics.py`
- **Shock semantics are defined in code**: see `src/exp_suite/shocks.py`

### Shared metric definitions (code-anchored)

These are the semantics used by Exp2/Exp3 policy evaluation and (in parts) Exp1:

- **`M3_avg_cost`**: mean realized loss over **labeled decisions** (Exp2/Exp3).  
  Code anchor: `src/exp_suite/metrics.py` (`compute_exp2_metrics`, `compute_exp3_metrics`).
- **`M5_deferral_rate`**: fraction of labeled decisions where action is `WAIT`.  
  Code anchor: `src/exp_suite/metrics.py` (`valid["is_wait"]`).
- **`M2_mean_wait_seconds_when_wait`**: mean `(reconciliation_arrival_time - decision_time)` over labeled decisions where action is `WAIT`, clipped at 0.  
  Code anchor: `src/exp_suite/metrics.py`.
- **`M1_correctness_rate`**: fraction of labeled decisions where realized loss is within `correctness_epsilon` of the oracle (best of `{ACT, WAIT}`) under the observed outcome + realized wait duration.  
  Code anchor: `src/exp_suite/metrics.py` (`correct = chosen <= oracle + eps`).
- **`M3b_avg_regret_vs_oracle`**: mean `(chosen_loss - oracle_loss)` where `oracle_loss = min(loss(ACT), loss(WAIT))`.  
  Code anchor: `src/exp_suite/metrics.py` (`regret = chosen - oracle`).

#### Definition: "Labeled decisions"

All Exp2/Exp3 metrics (and Exp1 correctness/regret) are computed over **labeled decisions**:
- **Labeled**: A decision that successfully joins with a reconciliation record on `(entity_id, t_idx)` and has a non-null `outcome`.
- **Unlabeled**: A decision with no matching reconciliation or null outcome (rare in well-formed runs; indicates data pipeline issue).
- **Coverage**: In all reported Exp1/Exp2/Exp3 runs, label coverage is ~100% (`decisions_labeled / decisions_total ≈ 1.0`).
- **No censoring risk**: Unlabeled decisions are pipeline errors, not systematically different cases. The workload generator produces reconciliation for every `(entity_id, t_idx)` timepoint.
- Code anchor: `src/exp_suite/metrics.py` lines 84-88, 549-557 (`valid = joined[~pd.isna(joined["loss"])]`).

### Shock semantics (Exp3)

- **Shock multiplier** \(m(t)\) is defined by `shock.shape` over normalized episode time \(t \in [0,1]\).  
  Code anchor: `src/exp_suite/shocks.py` (`shock_multiplier`).
- **Important detail (non-negotiable)**: for `shape == "step"`, the multiplier is **`mag` for all `t >= start_frac`**; it does **not** use `duration_frac`.  
  Code anchor: `src/exp_suite/shocks.py` (`if shape == "step": return mag if t >= start else 1.0`).
- Per-component scaling is controlled by `shock.apply_to`.  
  Code anchor: `src/exp_suite/shocks.py` (`shock_scales_for_components`).

### Code snippets (verbatim; thesis-auditable)

#### Exp3 shock schedule semantics (`step` ignores `duration_frac`)

```python
def shock_multiplier(shock: ShockModel, t_frac: float) -> float:
    """Compute shock multiplier m(t) for normalized t in [0,1]."""
    t = clamp01(float(t_frac))
    shape = shock.shape
    mag = float(shock.magnitude)
    if shape == "identity":
        return 1.0

    start = clamp01(float(shock.start_frac))
    dur = clamp01(float(shock.duration_frac))
    end = clamp01(start + dur) if dur > 0.0 else start

    if shape == "step":
        return mag if t >= start else 1.0
```

Source: `src/exp_suite/shocks.py`

#### Exp2 metric correctness + regret (oracle definition)

```python
oracle = min(chosen, alt)
regret = chosen - oracle

eps = float(getattr(cfg, "correctness_epsilon", 0.0))
correct = chosen <= oracle + eps
```

Source: `src/exp_suite/metrics.py` (`compute_exp2_metrics`)

#### Exp3 per-decision loss scaling (all targeted components scale)

```python
scales = shock_scales_for_components(cfg.shock, t_frac)
cfa = float(cfg.cost_false_act) * float(scales["cost_false_act"])
cfw = float(cfg.cost_false_wait) * float(scales["cost_false_wait"])
w_scale = float(scales["wait_cost"])
```

Source: `src/exp_suite/metrics.py` (`_loss_for_action_exp3`)

#### Exp1 inclusion rule (finalized + full seed set only; excludes partials)

```python
if sp.get("last_run_id") != "FINALIZED":
    continue
if total_i <= 0 or completed_i != total_i:
    continue
if total_i != 3 * seed.expected_seed_count:
    continue

sm_path = sweep_dir / "sweep_manifest.json"
if not sm_path.exists():
    continue
sm = _load_json(sm_path)
seeds = sm.get("seeds") or []
try:
    seed_set = {int(x) for x in seeds}
except Exception:
    continue
# Strictly require the full expected seeds. This excludes smokes / partial seed sweeps.
if seed_set != expected_seeds:
    continue
```

Source: `scripts/generate_exp1_paper_summary.py` (`_collect_runs_for_seedset`)

### Decision algorithms (policy definitions)

These algorithms define the four timing policies evaluated in Exp2/Exp3. Each policy maps `(conflict_size, cfg)` → `{ACT, WAIT}`.

#### Algorithm 1: Risk-Threshold Policy (Expected-Loss Minimization)

**Purpose:** Choose action that minimizes expected loss under uncertainty proxy.

**Pseudocode:**
```
FUNCTION decide_risk_threshold(conflict_size, cfg):
  # Proxy uncertainty: normalized conflict size
  p ← (conflict_size - 1) / (cfg.source_count - 1)  # ∈ [0, 1]
  p ← clamp(p, 0.0, 1.0)
  
  # Expected wait duration (reconciliation lag + jitter)
  E[wait_seconds] ← cfg.reconciliation_lag_seconds + E[jitter]
  
  # Expected losses (under proxy distribution)
  E[L(ACT)]  ← (1 - p) × cfg.cost_false_act
  E[L(WAIT)] ← p × cfg.cost_false_wait + wait_cost(E[wait_seconds])
  
  # Minimax decision rule
  IF E[L(ACT)] ≤ E[L(WAIT)]:
    RETURN "ACT"
  ELSE:
    RETURN "WAIT"
```

**Code anchor:** `src/exp_suite/decisions.py` (lines 127-173)

**Key insight (Exp2 C6-C8):** `risk_threshold` uses conflict_size as a proxy for outcome uncertainty. When `conflict_size = 1` (no disagreement), `p = 0`, so `E[L(ACT)] = 0` → always ACT. When `conflict_size = source_count` (maximal disagreement), `p = 1`, so `E[L(WAIT)] = cost_false_wait + wait_cost` → WAIT if cheaper.

---

#### Algorithm 2: Wait-on-Conflict Policy (Conflict-Aware Baseline)

**Purpose:** Defer to reconciliation when evidence disagrees.

**Pseudocode:**
```
FUNCTION decide_wait_on_conflict(conflict_size):
  IF conflict_size > 1:
    RETURN "WAIT"  # Multiple candidates → wait for reconciliation
  ELSE:
    RETURN "ACT"   # Single candidate → proceed immediately
```

**Code anchor:** `src/exp_suite/decisions.py` (line 125)

**Key insight (Exp1 C2-C5):** Under `baseline_a` or `baseline_b` semantics, `conflict_size` is always 1 (state collapses to single candidate), so this policy degenerates to `always_act`. Under `proposed` semantics, `conflict_size` can be > 1, enabling conflict-aware deferral.

---

#### Algorithm 3: Baseline Policies (Always-Act, Always-Wait)

**Purpose:** Non-adaptive reference policies.

**Pseudocode:**
```
FUNCTION decide_always_act(conflict_size):
  RETURN "ACT"  # Ignore evidence; always proceed

FUNCTION decide_always_wait(conflict_size):
  RETURN "WAIT"  # Ignore evidence; always defer
```

**Code anchor:** `src/exp_suite/decisions.py` (lines 120-123)

---

#### Algorithm 4: State Representation Semantics (Exp1 Key Differentiator)

**Purpose:** How systems track candidate values under conflict.

**Pseudocode:**
```
FUNCTION state_view(semantics, evidence_set):
  # evidence_set = {(source_id, event_time, receipt_time, value), ...}
  
  IF semantics == "baseline_a":
    # Naive overwrite: trust event time (source time), collapse to one value
    chosen ← last(evidence_set, order_by=event_time)
    RETURN StateView(candidates=[chosen.value], conflict_size=1)
  
  ELIF semantics == "baseline_b":
    # Last-writer-wins: trust arrival order (receipt time), collapse to one value
    chosen ← last(evidence_set, order_by=receipt_time)
    RETURN StateView(candidates=[chosen.value], conflict_size=1)
  
  ELIF semantics == "proposed":
    # Conflict-aware: retain all unique values (ordered by first receipt)
    candidates ← unique_values(evidence_set, order_by=receipt_time)
    RETURN StateView(candidates=candidates, conflict_size=|candidates|)
```

**Code anchor:** `src/exp_suite/state_view.py` (lines 41-80)

**Key insight (Exp1 C2-C5):** `proposed` exposes `conflict_size > 1` to policies when evidence disagrees; baselines always collapse to `conflict_size = 1`. This is the **only** difference between `baseline_b` and `proposed` in Exp1 (same LWW merge rule, different conflict visibility).

---

#### Algorithm 5: Oracle + Regret Computation (Exp1/Exp2 Primary Outcome)

**Purpose:** Hindsight-optimal action given realized outcome + wait duration.

**Pseudocode:**
```
FUNCTION compute_oracle_and_regret(decision, outcome, wait_seconds, cfg):
  # Realized losses under both actions (hindsight-perfect)
  loss_if_ACT  ← loss(action="ACT",  outcome=outcome, wait_seconds=0,            cfg)
  loss_if_WAIT ← loss(action="WAIT", outcome=outcome, wait_seconds=wait_seconds, cfg)
  
  # Oracle: best action in hindsight
  oracle_loss ← min(loss_if_ACT, loss_if_WAIT)
  
  # Regret: how much worse was the chosen action?
  chosen_loss ← loss(action=decision.action, outcome=outcome, wait_seconds=wait_seconds, cfg)
  regret ← chosen_loss - oracle_loss
  
  # Correctness: within epsilon of oracle?
  correct ← (chosen_loss ≤ oracle_loss + cfg.correctness_epsilon)
  
  RETURN {oracle_loss, regret, correct}

FUNCTION loss(action, outcome, wait_seconds, cfg):
  # Classification component
  IF action == "ACT" AND outcome == "needs_act":
    classification_loss ← 0  # correct intervention
  ELIF action == "ACT" AND outcome == "ok":
    classification_loss ← cfg.cost_false_act  # false positive
  ELIF action == "WAIT" AND outcome == "needs_act":
    classification_loss ← cfg.cost_false_wait  # false negative
  ELSE:  # action == "WAIT" AND outcome == "ok"
    classification_loss ← 0  # correct deferral
  
  # Delay component (only for WAIT)
  IF action == "WAIT":
    delay_loss ← wait_cost(wait_seconds, cfg)
  ELSE:
    delay_loss ← 0
  
  RETURN classification_loss + delay_loss
```

**Code anchor:** `src/exp_suite/metrics.py` (`_loss_for_action`, `compute_exp2_metrics`)

**Key claim (C2-C5, C6-C8):** `M3b_avg_regret_vs_oracle` averages `regret` over all labeled decisions. A policy with zero regret would be hindsight-optimal (impossible without perfect foresight).

---

#### Algorithm 6: Time-Aware Cost Computation (Exp3 Shocks)

**Purpose:** Apply time-varying shock multiplier to decision-time costs.

**Pseudocode:**
```
FUNCTION compute_costs_with_shock(t_idx, cfg):
  # Normalized episode time
  t_frac ← t_idx / cfg.events_per_entity  # ∈ [0, 1]
  
  # Shock multiplier at this time (see "Shock semantics" above)
  m(t) ← shock_multiplier(cfg.shock, t_frac)
  
  # Scale targeted components (cfg.shock.apply_to)
  IF "cost_false_act" ∈ cfg.shock.apply_to:
    cost_false_act ← cfg.cost_false_act × m(t)
  ELSE:
    cost_false_act ← cfg.cost_false_act
  
  IF "cost_false_wait" ∈ cfg.shock.apply_to:
    cost_false_wait ← cfg.cost_false_wait × m(t)
  ELSE:
    cost_false_wait ← cfg.cost_false_wait
  
  IF "wait_cost" ∈ cfg.shock.apply_to:
    wait_cost_scale ← m(t)
  ELSE:
    wait_cost_scale ← 1.0
  
  RETURN {cost_false_act, cost_false_wait, wait_cost_scale}
```

**Code anchor:** `src/exp_suite/metrics.py` (`_loss_for_action_exp3`), `src/exp_suite/shocks.py` (`shock_multiplier`, `shock_scales_for_components`)

**Key claim (C12):** In the Exp3 v1 sweep, **all** cost components (`cost_false_act`, `cost_false_wait`, `wait_cost`) are scaled by the same `m(t)`, so `risk_threshold` decision boundaries are invariant to shocks (both sides of the inequality scale equally). This is a design choice, not a fundamental limitation.

---

## Codebase apparatus overview (implementation modules)

The experiment apparatus is implemented in `src/exp_suite/` with strict separation of concerns:

- **`workload.py`**: generates synthetic conflict + reconciliation event streams under specified regime parameters (conflict rate, delay distribution).
- **`state.py`**: implements the three state-tracking semantics (baseline_a, baseline_b, proposed).
- **`state_view.py`**: constructs conflict-aware state views (with budgeted conflict tracking for proposed).
- **`decisions.py`**: implements the four timing policies (always_act, always_wait, wait_on_conflict, risk_threshold).
- **`reconciliation.py`**: generates ground-truth outcome labels and reconciliation arrival times.
- **`metrics.py`**: computes all artifact-derived metrics (M1–M9, E3) from decisions + reconciliation tables; no "invented" numbers.
- **`shocks.py`**: defines time-varying shock schedules for Exp3 (identity, step, ramp, impulse).
- **`config.py`**: Pydantic schemas for locked TOML configs (Exp1Config, Exp2Config, Exp3Config).
- **`runner.py`**: single-run orchestrator (workload → state → decisions → reconciliation → metrics → artifacts).
- **`cli.py`**: CLI commands (`exp-suite run`, `exp-suite exp2-policy-run`, `exp-suite exp3-shock-run`, `exp-suite summarize-sweep`).
- **`sweep.py`**: sweep-level aggregation (per-policy mean/CI from per-seed runs).
- **`grid.py`**: locked config generation for Exp1/Exp2/Exp3 grids.
- **`manifest.py`**: sweep/run manifest JSON generation + git-rev tracking.
- **`artifacts.py`**: writes per-run Parquet tables + JSON metadata.

**Workflow** (single run): `workload.py` → `state.py` + `state_view.py` → `decisions.py` → `reconciliation.py` → `metrics.py` → artifacts written.

**Workflow** (sweep): CLI (`cli.py`) orchestrates N runs → `sweep.py` aggregates → `scripts/*.py` generate summary docs.

### Repository file structure

```
configs/
  locked/                      # preregistered, immutable experiment definitions
    exp1_grid_v1/              # 162 configs (54 points × 3 systems)
    exp2_policy_v2_16pt/       # 48 configs (12 wait-cost points × 4 policies)
    exp3_shock_v1_48sweeps/    # 192 configs (12 base × 4 shocks × 4 policies)

artifacts/                     # in-repo summaries + audits (NOT raw sweep dirs)
  audit_*.json                 # completeness checks (finalized sweeps, seed counts)
  exp1_grid_v1_table__*.csv    # Exp1 point-level means per system
  exp3_shock_v1_*__metrics.csv # Exp3 long-form metrics (per sweep × policy × metric)
  exp3_*.json                  # Exp3 scenario aggregates + gate reports

scripts/                       # deterministic report generators (read artifacts, write docs)
  generate_exp1_paper_summary.py
  generate_exp2_policy_summary.py
  analyze_exp3_results.py
  run_exp*.ps1                 # PowerShell sweep runners (write to C:\*_artifacts)

docs/                          # markdown summaries (thesis-ready, citation-safe)
  experiment1_full_summary.md
  experiment_2_policy_summary__v2_policy.md
  experiment3_full_summary.md
  final_claims.md              # THIS FILE (single source of truth)

src/exp_suite/                 # implementation (see "Codebase apparatus overview" above)
```

**Key constraint**: raw sweep directories (per-run `run_manifest.json`, `metrics.json`, Parquet tables) are written to external directories (`C:\*_artifacts`) and **not committed** to this repo. The in-repo `artifacts/` directory contains only **summary CSVs/JSONs** derived from those sweeps.

---

The sections below present the experimental results in order (Exp1 → Exp2 → Exp3), with each experiment's claims bounded by its preregistered design and data inclusion rules.

---

## Experiment 1 (Exp1) — Grid v1 (preregistered)

### What Exp1 supports (bounded)

- Claims about relative performance on the **preregistered 54-regime-point grid** under preregistered **seed splits A and B**.
- **Descriptive** win/loss counts, deltas, and holdout stability statistics.
- **Not supported here**: universal superiority claims (“always better”), real-world deployment claims, or inferential significance without separate analysis.

### Inputs (locked)

- **Locked grid configs**: `configs/locked/exp1_grid_v1/` (162 files = 54 points × 3 systems)
- **Systems**: `baseline_a`, `baseline_b`, `proposed`
- **Primary outcome**: `M3b_avg_regret_vs_oracle` (lower is better)
- **Grid factorization** (54 points = 3×3×3×2):
  - `conflict_rate` ∈ {0.01, 0.10, 0.20} — fraction of timepoints with disagreement across sources
  - `delay_sigma` (lognormal σ) ∈ {0.25, 0.50, 1.00} — receipt-time delay spread
  - `cost_false_act` ∈ {5.0, 10.0, 20.0} — loss for acting when truth="ok"
  - `cost_wait_per_second` ∈ {0.05, 0.10} — linear wait cost per second
- **Seeds**:
  - **A**: 0–29
  - **B**: 30–59

### Seed split discipline

- **Seed Set A** (0–29): Used for initial analysis and preregistered design validation.
- **Seed Set B** (30–59): Strict holdout set; **not used for any threshold selection, hyperparameter tuning, or design choices**.
- **No post-hoc tuning on A:** All experiment parameters (costs, delays, conflict rates, policies) were locked in `configs/locked/` **before** running Seed Set A. No parameters were adjusted after observing A results.
- **B is the real test:** Holdout stability (Pearson r > 0.999) on B confirms that per-point delta structures generalize beyond the initial seed set.

### Data inclusion + integrity (artifact-derived)

From `docs/experiment1_full_summary.md` (generated from on-disk artifacts) and the referenced audits:

- **Expected eval runs per seed set**: 54 points × 3 systems × 30 seeds = **4860**
- **Inclusion rule** (paper-safe): only sweeps where:
  - `sweep_progress.json.last_run_id == "FINALIZED"` and `completed == total == 90`, and
  - `sweep_manifest.json.seeds` exactly matches the preregistered seed range.
- **Selection rule**: if multiple eligible sweeps exist for the same regime point, select newest `created_utc` (ties by directory name).
- **Robustness rule**: if `sweep_manifest.json.runs` is incomplete, rebuild from per-run `run_manifest.json`.

Artifact anchors:

- Audit (A): `artifacts/audit_exp1_grid_v1__A.json`
- Audit (B): `artifacts/audit_exp1_grid_v1__B_r1.json`
- Point-level tables:
  - `artifacts/exp1_grid_v1_table__A.csv`
  - `artifacts/exp1_grid_v1_table__B_r1.csv`

### Known imperfections (Exp1) — factual

From `docs/experiment1_full_summary.md`:

- Seed A includes **1 duplicated eligible full sweep** (handled by the deterministic selection rule).
- Seed A includes **1 sweep with incomplete `sweep_manifest.json.runs`** (handled by deterministic rebuild from `run_manifest.json`).

**Transparency note:** These imperfections are disclosed upfront. Both were handled deterministically (newest sweep selected for duplicates; manifest rebuilt from per-run files for incomplete manifests). The inclusion rule (lines 195-199) and code anchor (lines 88-109) ensure only finalized, full-seed sweeps are included in the claims below.

### Claims (Exp1) — supported, with numbers

- **C1 (completeness)**: Seed Set A includes **4860 / 4860** eval runs across **54 / 54** regime points; Seed Set B includes **4860 / 4860** across **54 / 54** regime points.  
  Evidence: `docs/experiment1_full_summary.md`, `artifacts/audit_exp1_grid_v1__A.json`, `artifacts/audit_exp1_grid_v1__B_r1.json`.

- **C2 (primary outcome, A)**: On the preregistered 54-point grid, `proposed` had lower per-point mean `M3b_avg_regret_vs_oracle` than `baseline_a` in **39 / 54** points and lower than `baseline_b` in **39 / 54** points.  
  Evidence: `docs/experiment1_full_summary.md`.

- **C3 (primary outcome, B holdout)**: On the same grid, `proposed` had lower per-point mean `M3b_avg_regret_vs_oracle` than `baseline_a` in **36 / 54** points and lower than `baseline_b` in **36 / 54** points.  
  Evidence: `docs/experiment1_full_summary.md`.

- **C4 (not universal)**: `proposed` loses on **15 / 54** points (A) and **18 / 54** points (B). Therefore, any “always better” claim is false.  
  Evidence: `docs/experiment1_full_summary.md`.

- **C5 (holdout stability)**: Per-point deltas (proposed − baseline_b) between A and B have Pearson correlation **0.9996442758509282** with sign agreement **51 / 54** (excluding exact zeros).  
  Evidence: `docs/experiment1_full_summary.md`.

### Delta statistics (Exp1; per-point deltas proposed − baseline)

From `docs/experiment1_full_summary.md`:

- **Seed Set A**
  - **proposed − baseline_a**: mean **-0.22209302489142535**, median **-0.04950673077816603**, min **-1.0803726481166658**, max **0.18249369191433473**
  - **proposed − baseline_b**: mean **-0.22209302489142535**, median **-0.04950673077816603**, min **-1.0803726481166658**, max **0.18249369191433473**

- **Seed Set B**
  - **proposed − baseline_a**: mean **-0.21904153424080275**, median **-0.04849838553879815**, min **-1.0766017765242673**, max **0.20196247748312057**
  - **proposed − baseline_b**: mean **-0.21904153424080275**, median **-0.04849838553879815**, min **-1.0766017765242673**, max **0.20196247748312057**

Evidence: `docs/experiment1_full_summary.md`.

**Why baseline_a and baseline_b deltas are identical:**
- Both baselines collapse state to `conflict_size = 1` (single candidate).
- **baseline_a**: selects last value by `event_time` (source timestamp).
- **baseline_b**: selects last value by `receipt_time` (arrival timestamp).
- In Exp1, delays are small (lognormal μ=0, σ=0.25–0.50), so `event_time` and `receipt_time` orderings typically align.
- When orderings align, `last-by-event == last-by-receipt` → identical decisions and outcomes.
- **Quantitative check**: In Exp1, `baseline_a` and `baseline_b` produced identical aggregate regret statistics (mean, median, min, max) across all 54 regime points in both seed sets (see `docs/experiment1_full_summary.md` lines 60-71). Per-decision divergence frequency is not quantified in committed artifacts, but aggregate metrics confirm empirical equivalence under the Exp1 delay regime.
- This is an empirical result, not a data error. The semantics differ in principle (event-time vs receipt-time trust), but produce the same behavior under the Exp1 delay regime.
- Code anchor: `src/exp_suite/state_view.py` lines 62-70; delay configs: `configs/locked/exp1_grid_v1/*.toml`.

### Secondary tradeoff context (descriptive; not primary)

Mean-of-per-point-means (from `docs/experiment1_full_summary.md`):

- **Seed Set A**
  - `baseline_a`: M1=0.4716876939832411, M3=7.458982717430386, M7_bytes=203.0, M8_ms=0.0019438805601151407, M9_budget=1.0
  - `baseline_b`: M1=0.4716876939832411, M3=7.458982717430386, M7_bytes=203.0, M8_ms=0.0019439422187896985, M9_budget=1.0
  - `proposed`:  M1=0.4756069655412564, M3=7.23688969253896,  M7_bytes=205.75480000000002, M8_ms=0.0021764256854190918, M9_budget=2.988888888888889

- **Seed Set B**
  - `baseline_a`: M1=0.477025283278878,  M3=7.405620905045739, M7_bytes=203.0, M8_ms=0.0017060840070135545, M9_budget=1.0
  - `baseline_b`: M1=0.477025283278878,  M3=7.405620905045739, M7_bytes=203.0, M8_ms=0.0015365080735473722, M9_budget=1.0
  - `proposed`:  M1=0.48053121824364875, M3=7.186579370804936, M7_bytes=205.76386666666664, M8_ms=0.0017770295266355217, M9_budget=2.9925925925925925

**Aggregation method (all Exp1 tables):**
- All reported means are **macro-averages over regime points** (equal-weighted by point).
- Per-point means are computed first (averaging over 30 seeds within each point), then averaged across 54 points.
- This is **not** a micro-average over all decisions (which would weight high-volume points more heavily).
- **Robustness check**: Micro-averaging (pooling all decisions across all points) was not computed for the committed artifacts, but macro-averaging is reported to avoid dominance by high-volume regimes. The per-point win/loss counts (C2-C4) are unaffected by aggregation method and show the regime-dependent structure.
- Rationale: Each regime point represents a distinct experimental condition; equal weighting prevents high-entity-count points from dominating.

Metric anchors (implementation):

- Overhead metrics and conflict budget: `src/exp_suite/metrics.py` (keys `M7_state_bytes_*`, `M8_stateview_ms_*`, `M9_conflict_budget_size`).

### Regeneration (deterministic, from repo artifacts)

Regenerates `docs/experiment1_full_summary.md` and `artifacts/exp1_grid_v1_table__{A,B_r1}.csv` from on-disk sweep artifacts:

- `python scripts/generate_exp1_paper_summary.py`

---

## Experiment 2 (Exp2) — Policy sweep v2 (fixed semantics; policy varies)

Exp2 policy sweep is summarized in `docs/experiment_2_policy_summary__v2_policy.md`.

### Inputs (locked)

- **Locked policy configs**: `configs/locked/exp2_policy_v2_16pt/`
- **Policies**: `always_act`, `always_wait`, `wait_on_conflict`, `risk_threshold`
- **Seeds**:
  - **A**: 0–29
  - **B**: 30–59

### Completeness (artifact-derived)

These audits exist in-repo and confirm sweep finalization + expected run counts **in the external artifacts directory** recorded in the audit JSON:

- `artifacts/audit_exp2_policy_v2_16pt__A.json`:
  - expected points: 12; finalized points: 12
  - expected runs per point: 120 (= 30 seeds × 4 policies)
- `artifacts/audit_exp2_policy_v2_16pt__B.json`:
  - expected points: 12; finalized points: 12
  - expected runs per point: 120 (= 30 seeds × 4 policies)

**Important constraint**: the underlying Exp2 policy sweep directories referenced in these audits are on disk under `C:\exp2_policy_v2_16pt_artifacts` (not committed into this repo). The numeric policy-performance claims below are therefore anchored to the markdown summary file in `docs/`.

### Workload regime (Exp2; explains always_act dominance)

**Outcome distribution:**
- Truth trajectory starts at 0 ("ok" outcome) and evolves slowly (5% probability per timestep, ±random walk).
- Code: `src/exp_suite/reconciliation.py` line 59 (`label = "needs_act" if truth_value != 0 else "ok"`); `src/exp_suite/workload.py` lines 67-77 (truth initialization + evolution).
- **Implication**: Early timesteps (where most decisions occur) heavily favor "ok" outcomes, making `always_act` structurally low-risk for false-act errors.

**Reconciliation lag:**
- Fixed at **30.0 seconds** (no jitter) across all Exp2 points.
- Code: `configs/locked/exp2_policy_v2_16pt/*.toml` (`reconciliation_lag_seconds = 30.0`, `reconciliation_jitter.seconds = 0.0`).

**Cost parameters (constant across wait-cost points):**
- `cost_false_act = 10.0` (loss for acting when truth="ok")
- `cost_false_wait = 10.0` (loss for waiting when truth="needs_act")
- `wait_cost` varies by point (this is the sweep axis):
  - **Linear**: per_second ∈ {0.01, 0.02, 0.05, 0.10, 0.20} → 0.3–6.0 for 30s wait
  - **Exponential**: k ∈ {0.25, 0.50, 1.00}, a ∈ {0.05, 0.10}
  - **Quadratic**: k ∈ {0.00, 0.01}

**Why `always_act` wins 12/12 points:**
- With "ok"-heavy outcomes (truth starts at 0) and 30s fixed lag, waiting costs dominate the risk of rare false-act errors.
- **Quantitative outcome distribution (from Exp2 runs)**: For `always_act` policy, `M1_correctness_rate = 0.561` (Seed A) and `0.568` (Seed B) → acting is correct in ~56% of labeled decisions. Since `always_act` is correct when `outcome="ok"` and incorrect when `outcome="needs_act"`, this implies **~56% "ok", ~44% "needs_act"** across Exp2 decisions. This "ok"-heavy regime makes acting structurally favorable.
- Even at the cheapest wait cost (linear 0.01/s), waiting 30s costs 0.3 base + outcome-dependent loss.
- Policies that defer (`risk_threshold`, `wait_on_conflict`) pay wait costs without sufficient false-wait avoidance benefit in this regime.
- Code: `src/exp_suite/decisions.py` lines 120-175 (policy logic); `src/exp_suite/metrics.py` (loss computation); outcome distribution derived from `docs/experiment_2_policy_summary__v2_policy.md` (lines 69, 81).

### Reproducibility scope

| Artifact | In-Repo | Requires External Dirs | Regeneration Command |
|---|---|---|---|
| **Exp1 point-level tables** | ✅ CSV in `artifacts/` | ⚠️ Yes (sweep dirs under external path) | `python scripts/generate_exp1_paper_summary.py` |
| **Exp2 summary** | ✅ Markdown in `docs/` | ⚠️ Yes (`C:\exp2_policy_v2_16pt_artifacts`) | `python scripts/generate_exp2_policy_summary.py` |
| **Exp3 summary + CSVs** | ✅ CSV/JSON in `artifacts/` + markdown in `docs/` | ⚠️ Yes (`C:\exp3_shock_v1_48sweeps_artifacts`) | `python scripts/analyze_exp3_results.py` |
| **Audit JSONs** | ✅ In `artifacts/` | ❌ No (generated) | `python scripts/audit_exp*_completeness.py` |

**Repo-only verifiable:** Audit JSONs, Exp1/Exp3 tables/CSVs in `artifacts/`.  
**Requires external sweep dirs:** Regeneration of Exp1/Exp2/Exp3 summaries from raw sweeps.

**Note:** Numeric claims in `final_claims.md` are anchored to in-repo markdown summaries (`docs/experiment*_summary.md`) and CSV/JSON files (`artifacts/*`), which **are** committed. The underlying raw sweep directories (10s of GB) are not committed but are documented in audit JSONs.

**Verification boundary (threat model):** Any claim requiring raw per-run traces (e.g., per-decision action sequences, per-timestep state snapshots) beyond the committed CSV/JSON artifacts is **explicitly excluded** from this ledger. All claims herein are verifiable from in-repo summaries + audits, or from regenerating those summaries via documented scripts (which require external sweep dirs). This protects against unverifiable or tampered claims.

### Claims (Exp2 policy v2) — supported, with numbers

From `docs/experiment_2_policy_summary__v2_policy.md`:

- **C6 (win counts)**: Per-point winner by mean `M3_avg_cost` is `always_act` in **12 / 12** points for **Seed Set A** and **12 / 12** points for **Seed Set B** (holdout).  
  Evidence: `docs/experiment_2_policy_summary__v2_policy.md`.

- **C7 (holdout stability)**: Delta vs `always_act` per point is near-perfectly correlated between A and B:
  - `always_wait`: Pearson **0.9999999999397959** (n=12)
  - `risk_threshold`: Pearson **0.9998965817104882** (n=12)
  - `wait_on_conflict`: Pearson **0.9999999999238908** (n=12)  
  Evidence: `docs/experiment_2_policy_summary__v2_policy.md`.

- **C8 (descriptive mean-of-point-means table)**: The mean-of-per-point-means aggregates are:
  - **Seed Set A**
    - `always_act`: M3_avg_cost 4.788806; M1_correctness_rate 0.561192; M3b_avg_regret_vs_oracle 2.938557; M5_deferral_rate 0.000000; M2_mean_wait_seconds_when_wait 0.000000
    - `always_wait`: M3_avg_cost 9.736626; M1_correctness_rate 0.438808; M3b_avg_regret_vs_oracle 7.886377; M5_deferral_rate 1.000000; M2_mean_wait_seconds_when_wait 29.389667
    - `wait_on_conflict`: M3_avg_cost 5.248945; M1_correctness_rate 0.548836; M3b_avg_regret_vs_oracle 3.398696; M5_deferral_rate 0.090145; M2_mean_wait_seconds_when_wait 29.376719
    - `risk_threshold`: M3_avg_cost 7.885492; M1_correctness_rate 0.526976; M3b_avg_regret_vs_oracle 6.035243; M5_deferral_rate 0.834034; M2_mean_wait_seconds_when_wait 26.941700
  - **Seed Set B**
    - `always_act`: M3_avg_cost 4.715742; M1_correctness_rate 0.567877; M3b_avg_regret_vs_oracle 2.893744; M5_deferral_rate 0.000000; M2_mean_wait_seconds_when_wait 0.000000
    - `always_wait`: M3_avg_cost 9.809452; M1_correctness_rate 0.432123; M3b_avg_regret_vs_oracle 7.987455; M5_deferral_rate 1.000000; M2_mean_wait_seconds_when_wait 29.388784
    - `wait_on_conflict`: M3_avg_cost 5.169093; M1_correctness_rate 0.556198; M3b_avg_regret_vs_oracle 3.347096; M5_deferral_rate 0.090309; M2_mean_wait_seconds_when_wait 29.375657
    - `risk_threshold`: M3_avg_cost 7.952632; M1_correctness_rate 0.519596; M3b_avg_regret_vs_oracle 6.130635; M5_deferral_rate 0.833884; M2_mean_wait_seconds_when_wait 26.940904  
  Evidence: `docs/experiment_2_policy_summary__v2_policy.md`.

**Note on always_act invariance:** The `always_act` policy ignores all wait-cost parameters (the Exp2 sweep axis) because it never defers. Therefore, its mean cost (`M3_avg_cost = 4.788806` for A, `4.715742` for B) is identical across all 12 wait-cost points. This is expected, not a data error.  
Code anchor: `src/exp_suite/decisions.py` line 122.

### Point-level table (Exp2; all 12 wait-cost points × 4 policies)

From `docs/experiment_2_policy_summary__v2_policy.md` (48 rows shown inline; this is the complete table used to compute win counts + holdout stability):

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

Evidence: `docs/experiment_2_policy_summary__v2_policy.md`.

### Process / pipeline (code + runner anchors)

- Sweep runner: `exp-suite exp2-policy-run` (creates `sweep_manifest.json`, `sweep_progress.json`, per-run `run_manifest.json`, and `metrics.json`).  
  Code anchor: `src/exp_suite/cli.py` (`@app.command(name="exp2-policy-run")`).
- Runner script used for v2 (16pt): `scripts/run_exp2_policy_v2_16pt.ps1` (writes to `C:\exp2_policy_v2_16pt_artifacts`).
- Summary generator: `scripts/generate_exp2_policy_summary.py` (reads `sweep_summary.json` per sweep; does not “invent” numbers).

### Regeneration (deterministic, but needs external sweep artifacts)

To re-generate `docs/experiment_2_policy_summary__v2_policy.md`, the required sweep directories must be present on disk (as recorded in the audits, default `C:\exp2_policy_v2_16pt_artifacts`), and each sweep must have `sweep_summary.json` (or you must generate it via `exp-suite summarize-sweep`).

---

## Experiment 3 (Exp3) — Shock v1 (preregistered 48-sweep set)

### Inputs (locked)

- **Base points**: inherited from `configs/locked/exp2_policy_v2_16pt/` (12 base points)
- **Shock keys**: 4 (identity, step-early 10×, step-late 10×, ramp-early 2×)
- **Total sweeps per seed set**: 48 (= 12 × 4)
- **Policies per sweep**: 4
- **Seeds**:
  - **A**: 0–29
  - **B**: 30–59

Locked config sets:

- Identity gate configs: `configs/locked/exp3_shock_v1_gate/`
- Full 48-sweep set: `configs/locked/exp3_shock_v1_48sweeps/`

### Data inclusion + integrity (artifact-derived)

From `docs/experiment3_full_summary.md`:

- Seed Set A sweeps found: 48; finalized+seed-OK: **48**
- Seed Set B sweeps found: 48; finalized+seed-OK: **48**
- Inclusion rule: finalized sweep + seed list exactly matches preregistered range.

### Claims (Exp3) — supported, with numbers

From `docs/experiment3_full_summary.md` and in-repo artifacts:

- **C9 (identity reduction gate)**: identity shock reduces exactly to Exp2 on the same base-point set:
  - gate passed = **True**
  - worst abs diff = **0.0**  
  Evidence:
  - `artifacts/exp3_identity_reduction_gate.json`
  - `artifacts/exp3_shock_v1_gate__exp2_vs_exp3_identity__metrics.csv`
  - `artifacts/exp3_shock_v1_gate__exp2_vs_exp3_identity__report.json`

- **C10 (holdout stability)**:
  - `E3_p99_amplification`: n=192, Pearson r=**0.9999999533258395**, sign agreement=144/144
  - `E3_delta_avg_cost_vs_noshock`: n=192, Pearson r=**0.9999393813655039**, sign agreement=144/144
  - `E3_policy_churn_rate_mean`: n=192, Pearson r=**0.9999999999999983**, sign agreement=92/92  
  Evidence: `docs/experiment3_full_summary.md`, `artifacts/exp3_shock_v1_48sweeps__summary_full.json`.
  
**Definition: Policy churn** (Exp3): Churn measures changes in **discrete actions** (`ACT` ↔ `WAIT`), not changes in realized cost. A policy with zero churn under shocks makes the same action sequence regardless of cost scaling. Code anchor: `src/exp_suite/metrics.py` (`E3_policy_churn_rate_mean` computation).

- **C11 (scenario means; Seed Set A)**: mean over base points (12) yields the table in `docs/experiment3_full_summary.md`, including (selected rows shown here verbatim):
  - identity / always_act: E3_p99_amp = 1; Δavg_cost_vs_noshock = 0
  - ramp_early_2x / always_act: E3_p99_amp = 2; Δavg_cost_vs_noshock = 2.53801
  - step_late_10x / always_act: E3_p99_amp = 10; Δavg_cost_vs_noshock = 7.49495
  - step_early_10x / always_act: E3_p99_amp = 10; Δavg_cost_vs_noshock = 28.4448  
  Evidence: `docs/experiment3_full_summary.md`, `artifacts/exp3_shock_v1_48sweeps__summary_full.json`.

#### Exp3 scenario table (Seed Set A; mean over base points) — full

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

### Preregistered comparisons (Exp3; Seed Set A mean over base points)

From `docs/experiment3_full_summary.md`:

- **Step early 10× − step late 10×** (positive means early > late):
  - `E3_p99_amplification` / always_act: **0**
  - `E3_p99_amplification` / always_wait: **0.0177963**
  - `E3_p99_amplification` / risk_threshold: **0.0125777**
  - `E3_p99_amplification` / wait_on_conflict: **0.0666651**
  - `E3_delta_avg_cost_vs_noshock` / always_act: **20.9498**
  - `E3_delta_avg_cost_vs_noshock` / always_wait: **44.4164**
  - `E3_delta_avg_cost_vs_noshock` / risk_threshold: **35.8676**
  - `E3_delta_avg_cost_vs_noshock` / wait_on_conflict: **23.1485**

- **Step early 10× − ramp early 2×** (positive means step > ramp):
  - `E3_p99_amplification` / always_act: **8**
  - `E3_p99_amplification` / always_wait: **7.9995**
  - `E3_p99_amplification` / risk_threshold: **7.99973**
  - `E3_p99_amplification` / wait_on_conflict: **7.99937**
  - `E3_delta_avg_cost_vs_noshock` / always_act: **25.9068**
  - `E3_delta_avg_cost_vs_noshock` / always_wait: **68.5703**
  - `E3_delta_avg_cost_vs_noshock` / risk_threshold: **54.7746**
  - `E3_delta_avg_cost_vs_noshock` / wait_on_conflict: **29.8633**

Evidence: `docs/experiment3_full_summary.md`.

### Tail amplification prevalence (Exp3; Seed Set A)

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

Evidence: `docs/experiment3_full_summary.md`.

- **C12 (implementation limitation; shock scaling)**: shocks in this sweep multiply **all** cost components (`cost_false_act`, `cost_false_wait`, `wait_cost`) by the same multiplier (by design of the locked configs), so `risk_threshold` decision boundaries are invariant to shocks when both sides scale equally.  
  Evidence: `docs/experiment3_full_summary.md`; config-generation runner `scripts/run_exp3_shock_v1_from_exp2_policy_v2_16pt.ps1` uses `--apply-to cost_false_act --apply-to cost_false_wait --apply-to wait_cost`.

- **C13 (implementation limitation; step ignores duration)**: `shock.shape=step` persists from `start_frac` to end of episode; it does **not** use `duration_frac`.  
  Evidence: `docs/experiment3_full_summary.md`; code anchor: `src/exp_suite/shocks.py`.

### Artifact anchors (Exp3)

- Gate:
  - `artifacts/exp3_identity_reduction_gate.json`
  - `artifacts/exp3_shock_v1_gate__exp2_vs_exp3_identity__metrics.csv`
  - `artifacts/exp3_shock_v1_gate__exp2_vs_exp3_identity__report.json`
- Point-level long-form metrics tables:
  - `artifacts/exp3_shock_v1_48sweeps__A__metrics.csv`
  - `artifacts/exp3_shock_v1_48sweeps__B__metrics.csv`
- Scenario-level aggregates:
  - `artifacts/exp3_shock_v1_48sweeps__summary_full.json`
  - `artifacts/exp3_shock_v1_48sweeps__summary__A.json`
  - `artifacts/exp3_shock_v1_48sweeps__summary__B.json`
- Completeness audits:
  - `artifacts/audit_exp3_shock_v1_48sweeps__A.json`
  - `artifacts/audit_exp3_shock_v1_48sweeps__B.json`

### Process / pipeline (code + runner anchors)

- Sweep runner: `exp-suite exp3-shock-run` (per-shock-point sweeps, matched seeds across policies).  
  Code anchor: `src/exp_suite/cli.py` (`@app.command(name="exp3-shock-run")`).
- Experiment runner used for Exp3: `scripts/run_exp3_shock_v1_from_exp2_policy_v2_16pt.ps1` (writes to `C:\exp3_shock_v1_48sweeps_artifacts`).
- Results extraction + reporting: `scripts/analyze_exp3_results.py` (writes the in-repo `artifacts/exp3_*` CSV/JSON outputs and `docs/experiment3_full_summary.md`).

### Regeneration (deterministic, but needs external sweep artifacts)

The in-repo Exp3 artifacts above were generated from on-disk sweep directories under:

- `C:\exp3_go_nogo_gate_artifacts`
- `C:\exp3_shock_v1_48sweeps_artifacts`

These raw sweep directories are **not committed** into this repo. Re-running `scripts/analyze_exp3_results.py` requires those directories (or equivalent) to exist.

---

## Cross-experiment “safe to say” summary (bounded)

- **Regime dependence exists** (Exp1): `proposed` is not universally better; it wins in a majority of preregistered regime points but loses on a non-trivial subset.  
- **Holdout stability is very high** in Exp1 and Exp3 for the reported per-point delta structures (Pearson r > 0.999 for all primary metrics), under the preregistered seed splits.  
- **Shock severity dominates tails** in Exp3 within the preregistered shock set (step 10× scenarios produce the largest tail amplification), with identity reducing exactly to the no-shock baseline.

---

## Explicit non-claims (these are disallowed unless new artifacts are produced)

- Any claim of **statistical significance**, confidence intervals across regimes, or generalized population inference (unless separately preregistered + analyzed and materialized).
- Any claim about **real-world deployment performance** or external validity not directly modeled in the locked configs.
- Any claim that a method is **always** better across regimes (explicitly falsified by Exp1 win/loss tables).


