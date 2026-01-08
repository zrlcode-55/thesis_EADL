## Post-Runner Journal (Pre-Registered Discipline Log)

Purpose: keep a *committee-defensible* record of what we observed and what we changed **after** seeing it.

Rules:
- Every observation must reference **artifacts/run IDs** (not memory).
- Every change must state **what changed**, **why**, and **what it invalidates** (if anything).
- No silent tweaks: if we change assumptions/hypotheses/configs/code paths, it goes here.

---

## Entry Template (copy/paste)

### Date:

### Phase: DEV / EVAL

### Context / intent (1–3 sentences)

### Hypothesis / expectation (pre-run)

### Runs executed (artifact pointers)
- Run IDs:
- Config file paths:
- `config_sha256` values:
- Git rev (from manifest):

### What we observed (post-run)
- Observation 1:
- Observation 2:

### What we changed (if any)
- **Change**:
  - **Reason**:
  - **Scope** (what experiments/claims this affects):
  - **Follow-up** (what we will rerun / what remains fixed):

### What we did NOT change (explicit)
- Kept fixed:

### Next actions
- Next snippet / task:
- Next run plan (configs/sweep IDs):

---

## Log

### 2026-01-08 — Experiment 1 (Conflict & Delay Correctness): baseline_a vs proposed (DEV)

### Date:
2026-01-08

### Phase: DEV

### Context / intent (1–3 sentences)
First clean A/B comparison where **semantics changes decisions** while holding the evidence stream and loss model fixed. Goal: observe directionality without tuning.

### Hypothesis / expectation (pre-run)
Unknown. We explicitly did not assume proposed would “win”; we expected semantics to change the ACT/WAIT boundary and therefore change loss/regret.

### Runs executed (artifact pointers)
- Run IDs:
  - baseline_a: `20260108T045514Z_b0b9ac02`
  - proposed: `20260108T045521Z_508dd86b`
- Config file paths:
  - both derived from `configs/exp1_minimal.toml` with only `system` changed
- `config_sha256` values:
  - baseline_a: `0d384dd8f2512472de7a3b17e0f59efe1b95619d3ff01727b2ff35b2869eb1b8`
  - proposed: `ffa15ea7280394a4085a0708df90d76bb05b1ebd0deda5846e611df1c33f0abd`
- Git rev (from manifest):
  - `ba3d8e5`

### What we observed (post-run)
- Observation 1: proposed is worse under the current simple policy + cost regime (likely due to more WAIT and accumulated delay cost).
  - baseline_a metrics:
    - M1 correctness rate: 0.5474
    - M3 avg loss: 2.263
    - M3b avg regret vs oracle: 0.9338601583
  - proposed metrics:
    - M1 correctness rate: 0.533
    - M3 avg loss: 2.8509542503199996
    - M3b avg regret vs oracle: 1.52181440862
- Observation 2: the outcome is genuinely empirical (semantics affects decisions) and must be studied rather than “tuned away.”

### What we changed (if any)
- None. (No parameter/policy tuning after observing outcomes.)

### What we did NOT change (explicit)
- Kept fixed:
  - seed = 0
  - evidence generator config (entity_count/source_count/events_per_entity/conflict_rate/missingness/delay)
  - decision opportunity definition (per entity per t_idx)
  - cost model (loss parameters)
  - evaluation code path (artifact-derived metrics)

### Next actions
- Next snippet / task:
  - introduce a principled policy family that uses observable conflict measures (e.g., conflict_size/entropy) and delay distribution assumptions, then re-run comparisons under locked configs.
- Next run plan (configs/sweep IDs):
  - create `configs/locked/exp1_eval_v1_*.toml` and run a small matched-seed sweep.

### 2026-01-08 — Experiment 1 (Conflict & Delay Correctness): Eval v2 policy (risk_threshold) (EVAL smoke)

### Date:
2026-01-08

### Phase: EVAL (smoke)

### Context / intent (1–3 sentences)
Evaluate a mathematically specified ACT/WAIT boundary (`risk_threshold`) derived from expected loss under delayed reconciliation, using locked configs and matched seeds.

### Hypothesis / expectation (pre-run)
Unknown. The goal is not to “win,” but to test whether an expected-loss boundary changes regret/cost behavior relative to the naive conflict rule.

### Runs executed (artifact pointers)
- Sweep ID: `exp1_eval_v2_smoke`
- Sweep dir: `artifacts/sweep_exp1_eval_v2_smoke/`
- Config file paths:
  - `configs/locked/exp1_eval_v2_baseline_a.toml`
  - `configs/locked/exp1_eval_v2_proposed.toml`
- Seeds: 0, 1, 2
- Git rev (from sweep): `ba3d8e5`

### What we observed (post-run)
From `artifacts/sweep_exp1_eval_v2_smoke/sweep_summary.json` (means over seeds):

- baseline_a:
  - M1 correctness rate mean: 0.47433333333333333
  - M3 avg loss mean: 8.193745315986668
  - M3b avg regret vs oracle mean: 6.800256821306667
- proposed:
  - M1 correctness rate mean: 0.4801333333333333
  - M3 avg loss mean: 7.652185027353333
  - M3b avg regret vs oracle mean: 6.2586965326733335

Observation: under the `risk_threshold` policy in this regime, proposed shows lower mean loss and regret than baseline_a (small N=3; smoke only).

### What we changed (if any)
- Change: introduced `policy = "risk_threshold"` (expected-loss inequality boundary) and created locked eval v2 configs.
  - Reason: move from heuristic waiting-on-conflict to a formally specified decision boundary grounded in the loss model.
  - Scope: Experiment 1 policy comparisons; does not change workload generation or reconciliation semantics.
  - Follow-up: run a larger seed set under the same locked configs before making any claims.

### What we did NOT change (explicit)
- Kept fixed:
  - workload generator and parameters (except policy selection)
  - matched seeds across systems
  - artifact-derived metric computation

### Next actions
- Expand evaluation: run `exp1_eval_v2` with a larger matched seed set (e.g., 30–100 seeds) and summarize.
- Decide whether to add entropy-weighted proxy p as a separate, versioned policy (v3) only if v2 results are unstable across seeds.

### 2026-01-08 — Experiment 1 (Conflict & Delay Correctness): Eval v2 policy (risk_threshold) N=30 (EVAL)

### Date:
2026-01-08

### Phase: EVAL

### Context / intent (1–3 sentences)
Increase seed count to reduce variance and test whether the v2 (risk_threshold) advantage is stable under matched-seed evaluation.

### Hypothesis / expectation (pre-run)
Unknown. The goal is stability checking, not tuning.

### Runs executed (artifact pointers)
- Sweep ID: `exp1_eval_v2_n30`
- Sweep dir: `artifacts/sweep_exp1_eval_v2_n30/`
- Config file paths:
  - `configs/locked/exp1_eval_v2_baseline_a.toml`
  - `configs/locked/exp1_eval_v2_proposed.toml`
- Seeds: 0–29 (inclusive)

### What we observed (post-run)
From `artifacts/sweep_exp1_eval_v2_n30/sweep_summary.json` (means over 30 seeds):

- baseline_a:
  - M1 correctness rate mean: 0.48302974861638986
  - M3 avg loss mean: 8.106874574949789
  - M3b avg regret vs oracle mean: 6.688159750714315
- proposed:
  - M1 correctness rate mean: 0.48664979262519176
  - M3 avg loss mean: 7.578379080092669
  - M3b avg regret vs oracle mean: 6.159664255857196

Observation: proposed remains better than baseline_a on mean loss and regret under v2, and the direction matches the N=3 smoke sweep.

### What we changed (if any)
- None (same locked configs; only increased seed range).

### What we did NOT change (explicit)
- Kept fixed:
  - locked config files and cost model
  - workload generator and reconciliation semantics
  - metric definitions/implementation

### 2026-01-08 — Experiment 1 (Conflict & Delay Correctness): Eval v2 policy (risk_threshold) N=100 (EVAL)

### Date:
2026-01-08

### Phase: EVAL

### Context / intent (1–3 sentences)
Lock in a high-credibility matched-seed evaluation (N=100) for v2 `risk_threshold` to test stability under distributed-systems scrutiny.

### Hypothesis / expectation (pre-run)
Unknown. This is a stability/replication run of v2 under the same locked configs.

### Runs executed (artifact pointers)
- Sweep ID: `exp1_eval_v2_n100`
- Sweep dir: `artifacts/sweep_exp1_eval_v2_n100/`
- Config file paths:
  - `configs/locked/exp1_eval_v2_baseline_a.toml`
  - `configs/locked/exp1_eval_v2_proposed.toml`
- Seeds: 0–99 (inclusive)

### What we observed (post-run)
From `artifacts/sweep_exp1_eval_v2_n100/sweep_summary.json` (means over 100 seeds):

- baseline_a:
  - M1 correctness rate mean: 0.47284676455291064
  - M3 avg loss mean: 8.208754049023323 (std: 0.3257089979034647)
  - M3b avg regret vs oracle mean: 6.819874888488531
- proposed:
  - M1 correctness rate mean: 0.47822280496099223
  - M3 avg loss mean: 7.664692881210658 (std: 0.287399723639039)
  - M3b avg regret vs oracle mean: 6.275813720675867

Observation: proposed remains better than baseline_a on mean loss and regret under v2 at N=100.

### What we changed (if any)
- None (same locked configs; increased N only).




