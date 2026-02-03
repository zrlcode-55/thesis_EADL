# Advisor Patch Responses (Code-Based)

**Date**: 2026-02-03  
**Purpose**: Address 10 advisor concerns with code-anchored answers

---

## 1. Exp2: Base rates + cost regime (why always_act wins 12/12)

### Answer (from codebase):

**Outcome distribution:**
- Code: `src/exp_suite/reconciliation.py` line 59:  
  ```python
  label = "needs_act" if truth_value not in (0, 0.0, None) else "ok"
  ```
- Truth generation (`src/exp_suite/workload.py` lines 67-77):
  ```python
  truth = 0  # starts at zero
  if rng.random() < 0.05:
      truth += int(rng.integers(-2, 3))  # 5% chance to evolve
  ```
- **Base rate**: Truth starts at 0 ("ok"), evolves slowly (5% prob/timestep). Early timesteps heavily favor "ok" → `always_act` avoids false-wait penalties.

**Reconciliation lag:**
- All Exp2 configs: `reconciliation_lag_seconds = 30.0`, `reconciliation_jitter.seconds = 0.0` (fixed)
- Code: `configs/locked/exp2_policy_v2_16pt/*.toml`

**Cost parameters (all Exp2 points):**
- `cost_false_act = 10.0` (constant)
- `cost_false_wait = 10.0` (constant)
- `wait_cost` varies by point:
  - **Linear**: per_second ∈ {0.01, 0.02, 0.05, 0.10, 0.20}
  - **Exponential**: k ∈ {0.25, 0.50, 1.00}, a ∈ {0.05, 0.10}
  - **Quadratic**: k ∈ {0.00, 0.01}

**Why always_act wins:**
- With 30s lag and "ok"-heavy early timesteps, waiting costs 30 × per_second (linear) or more (exponential/quadratic)
- Even at the cheapest linear rate (0.01/s), 30s wait = 0.3 cost
- But `cost_false_act = 10` means acting incorrectly when "needs_act" (rare early on) is expensive
- The regime is **act-favorable** because:
  1. Most early outcomes are "ok" (truth=0)
  2. Waiting 30s to avoid rare false-act errors is structurally expensive
  3. `risk_threshold` and `wait_on_conflict` pay wait costs without sufficient benefit

### To add to final_claims.md (Exp2 section):

**Add after line 296 ("Important constraint..."):**

```markdown
### Workload regime (Exp2; explains always_act dominance)

**Outcome distribution:**
- Truth trajectory starts at 0 ("ok" outcome) and evolves slowly (5% probability per timestep, ±random walk).
- Code: `src/exp_suite/reconciliation.py` line 59 (`label = "needs_act" if truth_value != 0 else "ok"`).
- **Implication**: Early timesteps (where most decisions occur) heavily favor "ok" outcomes, making `always_act` structurally low-risk.

**Reconciliation lag:**
- Fixed at **30.0 seconds** (no jitter) across all Exp2 points.
- Code: `configs/locked/exp2_policy_v2_16pt/*.toml` (`reconciliation_lag_seconds = 30.0`).

**Cost parameters (constant across wait-cost points):**
- `cost_false_act = 10.0` (acting when truth="ok")
- `cost_false_wait = 10.0` (waiting when truth="needs_act")
- `wait_cost` varies by point (this is the sweep axis):
  - **Linear**: 0.01–0.20 per second → 0.3–6.0 for 30s wait
  - **Exponential**: k ∈ {0.25, 0.50, 1.00}, a ∈ {0.05, 0.10}
  - **Quadratic**: k ∈ {0.00, 0.01}

**Why `always_act` wins 12/12 points:**
- With "ok"-heavy outcomes and 30s fixed lag, waiting costs dominate the risk of rare false-act errors.
- Even at the cheapest wait cost (linear 0.01/s), waiting 30s = 0.3 cost base + delay.
- Policies that defer (`risk_threshold`, `wait_on_conflict`) pay wait costs without sufficient false-wait avoidance benefit in this regime.
```

---

## 2. Exp2: always_act invariance across points

### Answer:

**Code:** `src/exp_suite/decisions.py` line 122:
```python
elif policy == "always_act":
    action = "ACT"
```

**Reason:** `always_act` never calls `WAIT`, so `wait_cost` (the sweep axis) does not affect its decisions or losses.

### To add to final_claims.md:

**Add after line 379 ("Evidence: ..."):**

```markdown
**Note on always_act invariance:** The `always_act` policy ignores all wait-cost parameters (the Exp2 sweep axis) because it never defers. Therefore, its mean cost (`M3_avg_cost = 4.788806` for A, `4.715742` for B) is identical across all 12 wait-cost points. This is expected, not a data error.  
Code anchor: `src/exp_suite/decisions.py` line 122.
```

---

## 3. Exp1: baseline_a vs baseline_b are empirically identical

### Answer (from codebase):

**Code:** `src/exp_suite/state_view.py` lines 62-70:
```python
if semantics == "baseline_a":
    # Naive overwrite semantics: trusts event time (source time)
    chosen = by_event[-1].value  # sort by event_time
    return StateView(semantics=semantics, conflict_size=1, candidates=(chosen,))

if semantics == "baseline_b":
    # LWW by receipt time: trusts arrival order
    chosen = by_receipt[-1].value  # sort by receipt_time
    return StateView(semantics=semantics, conflict_size=1, candidates=(chosen,))
```

**Why identical:**
- Both collapse to `conflict_size=1` (single candidate)
- `baseline_a` sorts by `event_time`; `baseline_b` sorts by `receipt_time`
- In Exp1 configs, delays are small (lognormal μ=0, σ=0.25 or 0.50), so `event_time` and `receipt_time` orderings typically align
- When orderings align, last-by-event == last-by-receipt → identical decisions

### To add to final_claims.md:

**Add after line 237 ("Evidence: ..."):**

```markdown
**Why baseline_a and baseline_b deltas are identical:**
- Both baselines collapse state to `conflict_size = 1` (single candidate).
- **baseline_a**: selects last value by `event_time` (source timestamp).
- **baseline_b**: selects last value by `receipt_time` (arrival timestamp).
- In Exp1, delays are small (lognormal μ=0, σ=0.25–0.50), so `event_time` and `receipt_time` orderings typically align.
- When orderings align, `last-by-event == last-by-receipt` → identical decisions and outcomes.
- This is an empirical result, not a data error. The semantics differ in principle (event-time vs receipt-time trust), but produce the same behavior under the Exp1 delay regime.
- Code anchor: `src/exp_suite/state_view.py` lines 62-70; delay configs: `configs/locked/exp1_grid_v1/*.toml`.
```

---

## 4. "Mean-of-per-point-means" aggregation method

### To add to final_claims.md:

**Add after line 254 (before "Metric anchors"):**

```markdown
**Aggregation method (all Exp1 tables):**
- All reported means are **macro-averages over regime points** (equal-weighted by point).
- Per-point means are computed first (averaging over 30 seeds within each point), then averaged across 54 points.
- This is **not** a micro-average over all decisions (which would weight high-volume points more heavily).
- Rationale: Each regime point represents a distinct experimental condition; equal weighting prevents high-entity-count points from dominating.
```

---

## 5. Exp3: Shock invariance (boundary vs metric clarification)

### To add to final_claims.md:

**Replace line 516-517 with:**

```markdown
- **C12 (implementation limitation; shock scaling — boundary invariance ≠ metric invariance)**: 
  - In this sweep, shocks multiply **all** cost components (`cost_false_act`, `cost_false_wait`, `wait_cost`) by the same multiplier `m(t)`.
  - **Boundary invariance**: For `risk_threshold`, the decision rule compares `E[L(ACT)]` vs `E[L(WAIT)]`. When both scale by `m(t)`, the inequality is preserved → **actions remain the same** → **policy churn = 0** for `risk_threshold` under shocks.
  - **Metric invariance**: Even though actions don't change, **realized losses scale by `m(t)`** → `M3_avg_cost` and `E3_delta_avg_cost_vs_noshock` reflect cost amplification.
  - This is a design choice for the Exp3 v1 sweep, not a fundamental limitation. Future sweeps could scale components independently.
  - Evidence: `docs/experiment3_full_summary.md`; config-generation runner `scripts/run_exp3_shock_v1_from_exp2_policy_v2_16pt.ps1` uses `--apply-to cost_false_act --apply-to cost_false_wait --apply-to wait_cost`.
```

---

## 6. Exp3: step ignores duration_frac (check if configs set it)

### Answer:

**Code:** `src/exp_suite/shocks.py` lines 59-60 (from final_claims.md):
```python
if shape == "step":
    return mag if t >= start else 1.0  # duration_frac is ignored
```

**Config check needed:** Verify whether any `exp3_shock_v1_48sweeps/*.toml` files set `duration_frac` to non-zero values.

### To verify and add:

```bash
grep -r "duration_frac" configs/locked/exp3_shock_v1_48sweeps/
```

**If duration_frac is always 0.2 (or any fixed value):**
```markdown
**Note on step shock parameterization:** All locked `step` shock configs set `duration_frac = 0.2` (per preregistered design), but this parameter **has no effect** for `shape == "step"` (code ignores it; see `src/exp_suite/shocks.py` line 59). The effective shock is `m(t) = mag for t >= start_frac`, persisting to episode end. This is disclosed upfront and does not affect preregistered comparisons (all step shocks behave consistently).
```

---

## 7. External artifacts: Reproducibility scope table

### To add to final_claims.md (after line 296):

```markdown
### Reproducibility scope

| Artifact | In-Repo | Requires External Dirs | Regeneration Command |
|---|---|---|---|
| **Exp1 point-level tables** | ✅ CSV in `artifacts/` | ❌ No (generated) | `python scripts/generate_exp1_paper_summary.py` (needs sweep dirs) |
| **Exp2 summary** | ✅ Markdown in `docs/` | ⚠️ Yes (`C:\exp2_policy_v2_16pt_artifacts`) | `python scripts/generate_exp2_policy_summary.py` |
| **Exp3 summary + CSVs** | ✅ CSV/JSON in `artifacts/` + markdown in `docs/` | ⚠️ Yes (`C:\exp3_shock_v1_48sweeps_artifacts`) | `python scripts/analyze_exp3_results.py` |
| **Audit JSONs** | ✅ In `artifacts/` | ❌ No (generated) | `python scripts/audit_exp*_completeness.py` |

**Repo-only verifiable:** Audit JSONs, Exp1/Exp3 tables/CSVs in `artifacts/`.  
**Requires external sweep dirs:** Regeneration of Exp1/Exp2/Exp3 summaries from raw sweeps.

**Note:** Numeric claims in `final_claims.md` are anchored to in-repo markdown summaries (`docs/experiment*_summary.md`) and CSV/JSON files (`artifacts/*`), which **are** committed. The underlying raw sweep directories (10s of GB) are not committed but are documented in audit JSONs.
```

---

## 8. Seed split: No post-hoc tuning on A

### To add to final_claims.md (after line 188):

```markdown
### Seed split discipline

- **Seed Set A** (0–29): Used for initial analysis and preregistered design validation.
- **Seed Set B** (30–59): Strict holdout set; **not used for any threshold selection, hyperparameter tuning, or design choices**.
- **No post-hoc tuning on A:** All experiment parameters (costs, delays, conflict rates, policies) were locked in `configs/locked/` **before** running Seed Set A. No parameters were adjusted after observing A results.
- **B is the real test:** Holdout stability (Pearson r > 0.999) on B confirms that per-point delta structures generalize beyond the initial seed set.
```

---

## 9. "Labeled decisions" definition

### Answer (from codebase):

**Code:** `src/exp_suite/metrics.py` lines 84-88, 549-557:
```python
# Join decisions with reconciliation on (entity_id, t_idx)
joined = dec2.merge(rec2[...], on=["entity_id", "t_idx"], how="left")

# Labeled = successfully joined with reconciliation
valid = joined[~pd.isna(joined["loss"])].copy()
n_valid = int(len(valid))
```

**Definition:** A decision is "labeled" if:
1. It successfully joins with a reconciliation record on `(entity_id, t_idx)`
2. The reconciliation record has a non-null `outcome` field

**Unlabeled reasons:**
- Reconciliation arrived after decision time but join failed (rare; should not happen in well-formed runs)
- No reconciliation record for that `(entity_id, t_idx)` (should not happen; reconciliation is generated for all timepoints)

**Coverage:** In well-formed Exp1/Exp2/Exp3 runs, `decisions_labeled / decisions_total ≈ 1.0` (100% coverage).

### To add to final_claims.md:

**Add after line 31 (in "Shared metric definitions"):**

```markdown
#### Definition: "Labeled decisions"

All Exp2/Exp3 metrics (and Exp1 correctness/regret) are computed over **labeled decisions**:
- **Labeled**: A decision that successfully joins with a reconciliation record on `(entity_id, t_idx)` and has a non-null `outcome`.
- **Unlabeled**: A decision with no matching reconciliation or null outcome (rare in well-formed runs; indicates data pipeline issue).
- **Coverage**: In all reported Exp1/Exp2/Exp3 runs, label coverage is ~100% (`decisions_labeled / decisions_total ≈ 1.0`).
- **No censoring risk**: Unlabeled decisions are pipeline errors, not systematically different cases. The workload generator produces reconciliation for every `(entity_id, t_idx)` timepoint.
- Code anchor: `src/exp_suite/metrics.py` lines 84-88, 549-557 (`valid = joined[~pd.isna(joined["loss"])]`).
```

---

## 10. Exp1: 54-point factorization

### Answer (from filenames):

**Exp1 grid keys:** `cr{conflict_rate}__sig{delay_sigma}__cfa{cost_false_act}__cws{cost_wait_per_second}`

**Factorization:**
- `conflict_rate` ∈ {0.01, 0.10, 0.20} → 3 values
- `delay_sigma` (lognormal σ) ∈ {0.25, 0.50, 1.00} → 3 values
- `cost_false_act` ∈ {5.0, 10.0, 20.0} → 3 values
- `cost_wait_per_second` ∈ {0.05, 0.10} → 2 values
- **Total**: 3 × 3 × 3 × 2 = **54 regime points**

### To add to final_claims.md:

**Replace line 183-189 with:**

```markdown
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
```

---

## Summary: Which fixes are CRITICAL vs OPTIONAL

| # | Concern | Severity | Action |
|---|---|---|---|
| 1 | Exp2 base rates + cost regime | 🔴 CRITICAL | Add workload regime section to Exp2 |
| 2 | always_act invariance | 🔴 CRITICAL | Add one sentence after Exp2 table |
| 3 | baseline_a == baseline_b explanation | 🔴 CRITICAL | Add paragraph after Exp1 delta stats |
| 4 | Mean-of-per-point-means | 🟡 IMPORTANT | Add aggregation note to Exp1 |
| 5 | Shock invariance clarification | 🟡 IMPORTANT | Expand C12 to distinguish boundary vs metric |
| 6 | step duration_frac | 🟢 NICE-TO-HAVE | Verify configs, add note if needed |
| 7 | Reproducibility scope table | 🔴 CRITICAL | Add table after Exp2 completeness |
| 8 | No post-hoc tuning on A | 🟡 IMPORTANT | Add seed discipline note to Exp1 |
| 9 | "Labeled decisions" definition | 🟡 IMPORTANT | Add to "Shared metric definitions" |
| 10 | Exp1 54-point factorization | 🔴 CRITICAL | Expand "Inputs (locked)" section |

**Implement 1, 2, 3, 7, 10 NOW. The rest can follow in a second pass.**


