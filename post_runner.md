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

### 2026-01-09 — Experiment 1 (Feasibility / Overhead): Eval v2_overhead N=10 smoke + N=30 (EVAL)

### Date:
2026-01-09

### Phase: EVAL

### Context / intent (1–3 sentences)
Record feasibility evidence (state overhead + state-view compute + conflict budget) under locked thresholds, using matched-seed sweeps and artifact-derived summaries. This is intentionally “no-bias”: thresholds are pinned in locked configs and we do not tune after seeing results.

### Hypothesis / expectation (pre-run)
Unknown. The goal is to measure feasibility costs (M7–M9) and check stability across seeds, not to optimize or cherry-pick.

### Runs executed (artifact pointers)
- Sweep IDs / dirs:
  - N=10 smoke: `exp1_eval_v2_overhead_n10` → `artifacts/sweep_exp1_eval_v2_overhead_n10/`
  - N=30: `exp1_eval_v2_overhead_n30_r1` → `artifacts/sweep_exp1_eval_v2_overhead_n30_r1/`
- Config file paths (locked):
  - `configs/locked/exp1_eval_v2_overhead_baseline_a.toml`
  - `configs/locked/exp1_eval_v2_overhead_proposed.toml`
- Seeds:
  - N=10: 0–9
  - N=30: 0–29
- Git rev:
  - `68633cbc621ede7ae7c6707931aa4cbdc87d5e92`

### What we observed (post-run)
From `artifacts/sweep_exp1_eval_v2_overhead_n30_r1/sweep_summary.json` (means over 30 seeds; bootstrap 95% CI on mean in brackets):

- baseline_a:
  - M3 avg loss mean: 8.106874574949789 [7.980880963174678, 8.238401043523462]
  - M3b avg regret vs oracle mean: 6.688159750714315 [6.52519648683489, 6.85843257024988]
  - M7 state bytes mean: 203.0 [203.0, 203.0]
  - M8 stateview ms mean: 0.001209381230485936 [0.0011629191221436486, 0.0012781189552818735]
  - M9 conflict budget size: 1.0 [1.0, 1.0]
- proposed:
  - M3 avg loss mean: 7.578379080092669 [7.459310416557605, 7.694805500764988]
  - M3b avg regret vs oracle mean: 6.159664255857196 [6.0018871545262, 6.313025724145566]
  - M7 state bytes mean: 205.72679999999997 [205.55040000000005, 205.90809]
  - M8 stateview ms mean: 0.0013183570854986707 [0.001276485356502235, 0.0013883588637690991]
  - M9 conflict budget size: 3.0 [3.0, 3.0]

### What we changed (if any)
- None (locked configs; N increased only).

### What we did NOT change (explicit)
- Kept fixed:
  - locked overhead thresholds and sampling limits (M7–M9)
  - matched seeds and workload generator parameters
  - cost model and metric definitions

### Next actions
- If runtime remains acceptable, run a v2_overhead N=100 sweep under a new sweep id (no config changes).

### 2026-01-12 — Experiment 1 (Grid v1): Seed Set A “1-hour batch” (EVAL)

### Date:
2026-01-12

### Phase: EVAL

### Context / intent (1–3 sentences)
Start the preregistered `grid_v1` characterization under Seed Set A (0–29) with a strict time budget (~1 hour). We ran a fixed number of regime points determined by measured throughput, not by outcomes.

### Hypothesis / expectation (pre-run)
Unknown. This batch is intended to validate throughput and begin collecting citable regime-map evidence without any adaptive pruning.

### Runs executed (artifact pointers)
- Grid config dir: `configs/locked/exp1_grid_v1/` (locked, committed)
- Seed set: A = 0–29
- Sweep prefix: `exp1_grid_v1__A_1h`
- Regime points executed (5 sweeps; each sweep = 3 systems × 30 seeds = 90 runs):
  - `exp1_grid_v1__A_1h__cr0p01__sig0p25__cfa10p00__cws0p05`
  - `exp1_grid_v1__A_1h__cr0p01__sig0p25__cfa10p00__cws0p10`
  - `exp1_grid_v1__A_1h__cr0p01__sig0p25__cfa20p00__cws0p05`
  - `exp1_grid_v1__A_1h__cr0p01__sig0p25__cfa20p00__cws0p10`
  - `exp1_grid_v1__A_1h__cr0p01__sig0p25__cfa5p00__cws0p05`
- Artifacts root: `artifacts/`
- Grid-level batch summary artifact:
  - `artifacts/exp1_grid_v1_summary__A_1h.json`
- Git rev:
  - `c93fd9d`

### What we observed (post-run)
- Throughput: 1 regime point at N=30 took ~645s (~10.75 minutes) → ~5 regime points fit in ~54 minutes.
- Primary metric (M3b_avg_regret_vs_oracle) regime-map direction for this batch:
  - Proposed vs baseline_a: wins 4 / 5 regime points (lower mean regret); losses 1 / 5.
  - Proposed vs baseline_b: wins 4 / 5 regime points (baseline_a and baseline_b were equal for these points).
- Per-point deltas (proposed minus baseline; negative is better):
  - `...__cfa10__cws0p05`: -0.0227118991
  - `...__cfa10__cws0p10`: -0.0364237982
  - `...__cfa20__cws0p05`: +0.0044590842
  - `...__cfa20__cws0p10`: -0.0008151648
  - `...__cfa5__cws0p05`: -0.0435118991

### What we changed (if any)
- None (grid configs + seed set A + metric definitions unchanged).

### What we did NOT change (explicit)
- Kept fixed:
  - preregistered grid_v1 config files and policy definition
  - seed set A definition (0–29)
  - inclusion/exclusion rules (artifact-derived, no manual deletion)

### Next actions
- Continue Seed Set A by running the next batch of regime points under a new sweep prefix (e.g., `exp1_grid_v1__A_1h_r2`) until the full grid is complete.
- Once A is complete, run Seed Set B holdout (30–59) under `exp1_grid_v1__B`.

### 2026-01-12 — Experiment 1 (Grid v1): Seed Set A “1-hour batch” #2 (EVAL)

### Date:
2026-01-12

### Phase: EVAL

### Context / intent (1–3 sentences)
Continue Seed Set A grid execution in another chunk, without changing any preregistered definitions. Goal: expand the regime-map coverage while keeping execution resumable and auditable.

### Hypothesis / expectation (pre-run)
Unknown. This is continued characterization; we accept wins and losses as evidence.

### Runs executed (artifact pointers)
- Seed set: A = 0–29
- Sweep prefix: `exp1_grid_v1__A_1h` (continued; additional regime points added)
- New regime points executed (5 additional sweeps; each sweep = 90 runs):
  - `exp1_grid_v1__A_1h__cr0p01__sig0p25__cfa5p00__cws0p10`
  - `exp1_grid_v1__A_1h__cr0p01__sig0p50__cfa10p00__cws0p05`
  - `exp1_grid_v1__A_1h__cr0p01__sig0p50__cfa10p00__cws0p10`
  - `exp1_grid_v1__A_1h__cr0p01__sig0p50__cfa20p00__cws0p05`
  - `exp1_grid_v1__A_1h__cr0p01__sig0p50__cfa20p00__cws0p10`
- Grid-level updated summary artifact (now 10 regime points total under this prefix):
  - `artifacts/exp1_grid_v1_summary__A_1h.json`
- Git rev:
  - `b8410f4`

### What we observed (post-run)
From `artifacts/exp1_grid_v1_summary__A_1h.json` (10 regime points total):
- Proposed vs baseline_a on primary metric (M3b regret): wins 8 / 10; losses 2 / 10.
- The two loss cases in this subset occur when `cost_false_act = 20.0` and `cost_wait_per_second = 0.05` under both tested delay sigmas (0.25 and 0.50), suggesting a boundary region where aggressive acting is very expensive.

### What we changed (if any)
- None.

### What we did NOT change (explicit)
- Kept fixed:
  - grid_v1 configs, seed set A definition, policy definition, and metric code

### Next actions
- Continue Seed Set A in further 1-hour batches until all 54 regime points are covered, then run Seed Set B (30–59).

### 2026-01-12 — Experiment 1 (Grid v1): Seed Set A aggregate status (EVAL)

### Date:
2026-01-12

### Phase: EVAL

### Context / intent (1–3 sentences)
Consolidate Seed Set A results across multiple execution prefixes into a single aggregate summary artifact, so progress can be tracked without relying on “batch-local” summaries.

### Runs executed (artifact pointers)
- Seed set: A = 0–29
- Sweep prefixes included:
  - `exp1_grid_v1__A_1h` (10 regime points)
  - `exp1_grid_v1__A_r3` (5 regime points)
- Combined summary artifact:
  - `artifacts/exp1_grid_v1_summary__A.json`

### What we observed (post-run)
From `artifacts/exp1_grid_v1_summary__A.json` (15 regime points total):
- Proposed vs baseline_a (primary metric M3b): wins 12 / 15, losses 3 / 15.
- Proposed vs baseline_b (primary metric M3b): wins 12 / 15, losses 3 / 15.

### What we changed (if any)
- None (aggregation is artifact-derived only; no metric definitions changed).

### Next actions
- Continue Seed Set A until all 54 regime points are covered, then run Seed Set B (30–59) and compare A vs B regime-map stability.

#### Update (same day): Seed Set A now at 20 / 54 regime points
From `artifacts/exp1_grid_v1_summary__A.json` (20 regime points total):
- Proposed vs baseline_a (M3b): wins 17 / 20, losses 3 / 20.
- Proposed vs baseline_b (M3b): wins 17 / 20, losses 3 / 20.

#### Update (same day): Seed Set A now at 25 / 54 regime points
From `artifacts/exp1_grid_v1_summary__A.json` (25 regime points total):
- Proposed vs baseline_a (M3b): wins 20 / 25, losses 5 / 25.
- Proposed vs baseline_b (M3b): wins 20 / 25, losses 5 / 25.


### 2026-01-15 — Experiment 1 (Grid v1): Seed Set A rounds r6 + r7 (EVAL)

### Date:
2026-01-15

### Phase: EVAL

### Context / intent (1–3 sentences)
Continue preregistered `grid_v1` Seed Set A (seeds 0–29) in additional resumable “round” chunks, without changing any locked configs, policies, or metric definitions.

### Hypothesis / expectation (pre-run)
Unknown. This is continued regime-map characterization; we accept wins and losses as evidence.

### Runs executed (artifact pointers)
- Sweep prefixes (each = 5 regime points; each point = 3 systems × 30 seeds = 90 runs):
  - `exp1_grid_v1__A_r6`
  - `exp1_grid_v1__A_r7`
- Sweep dirs (examples; see `artifacts/sweep_exp1_grid_v1__A_r6__*` and `artifacts/sweep_exp1_grid_v1__A_r7__*`):
  - `artifacts/sweep_exp1_grid_v1__A_r6__cr0p10__sig0p50__cfa5p00__cws0p10/`
  - `artifacts/sweep_exp1_grid_v1__A_r7__cr0p10__sig1p00__cfa10p00__cws0p05/`
- Combined grid-level summary artifact (regenerated to include `A_r6` and `A_r7`):
  - `artifacts/exp1_grid_v1_summary__A.json` (rows=25)

### What we observed (post-run)
From `artifacts/exp1_grid_v1_summary__A.json` (25 regime points total; primary metric M3b regret):
- Proposed vs baseline_a: wins 20 / 25, losses 5 / 25.
- Proposed vs baseline_b: wins 20 / 25, losses 5 / 25.

Progress (coverage): Seed Set A is now at **35 / 54** regime points completed (across all A-prefixed sweeps, excluding smoke/estimate).

### What we changed (if any)
- None. (No code/config/policy/metric changes; only additional grid points executed and summary regenerated from artifacts.)

### What we did NOT change (explicit)
- Kept fixed:
  - `configs/locked/exp1_grid_v1/*` (locked grid configs)
  - seed set A definition (0–29)
  - metric implementations and aggregation rules (artifact-derived)

### Next actions
- Continue Seed Set A to 54 / 54 (next chunk: `exp1_grid_v1__A_r8`), then run Seed Set B (30–59) under `exp1_grid_v1__B`.


### 2026-01-16 — Experiment 1 (Grid v1): Seed Set A round r8 (EVAL)

### Date:
2026-01-16

### Phase: EVAL

### Context / intent (1–3 sentences)
Continue preregistered `grid_v1` Seed Set A (seeds 0–29) in the next resumable “round” chunk, without changing any locked configs, policies, or metric definitions.

### Hypothesis / expectation (pre-run)
Unknown. Continued characterization; we accept wins and losses as evidence.

### Runs executed (artifact pointers)
- Sweep prefix: `exp1_grid_v1__A_r8`
- Sweep dirs (5 regime points; 3 systems × 30 seeds = 90 runs each):
  - `artifacts/sweep_exp1_grid_v1__A_r8__cr0p10__sig1p00__cfa5p00__cws0p10/`
  - `artifacts/sweep_exp1_grid_v1__A_r8__cr0p20__sig0p25__cfa10p00__cws0p05/`
  - `artifacts/sweep_exp1_grid_v1__A_r8__cr0p20__sig0p25__cfa10p00__cws0p10/`
  - `artifacts/sweep_exp1_grid_v1__A_r8__cr0p20__sig0p25__cfa20p00__cws0p05/`
  - `artifacts/sweep_exp1_grid_v1__A_r8__cr0p20__sig0p25__cfa20p00__cws0p10/`
- Sweep summaries written:
  - `artifacts/sweep_exp1_grid_v1__A_r8__*/sweep_summary.json`
- Combined grid-level summary artifact (regenerated after writing r6–r8 sweep summaries):
  - `artifacts/exp1_grid_v1_summary__A.json` (rows=40)

### What we observed (post-run)
From `artifacts/exp1_grid_v1_summary__A.json` (40 regime points total; primary metric M3b regret):
- Proposed vs baseline_a: wins 29 / 40, losses 11 / 40.
- Proposed vs baseline_b: wins 29 / 40, losses 11 / 40.

Progress (coverage): Seed Set A is now at **40 / 54** regime points completed (excluding smoke/estimate).

### What we changed (if any)
- None. (No code/config/policy/metric changes; only additional grid points executed and summaries regenerated from artifacts.)

### What we did NOT change (explicit)
- Kept fixed:
  - `configs/locked/exp1_grid_v1/*` (locked grid configs)
  - seed set A definition (0–29)
  - metric implementations and aggregation rules (artifact-derived)

### Next actions
- Continue Seed Set A to 54 / 54 (next chunk: `exp1_grid_v1__A_r9` with start-index 40), then run Seed Set B (30–59) under `exp1_grid_v1__B`.

### 2026-01-19 — Experiment 1 (Grid v1): Seed Set A rounds r9 + r10 (EVAL)

### Date:
2026-01-19

### Phase: EVAL

### Context / intent (1–3 sentences)
Continue preregistered `grid_v1` Seed Set A (seeds 0–29) in additional resumable “round” chunks, without changing locked configs, policies, or metric definitions.

### Hypothesis / expectation (pre-run)
Unknown. Continued characterization; we accept wins and losses as evidence.

### Runs executed (artifact pointers)
- Sweep prefixes:
  - `exp1_grid_v1__A_r9`
  - `exp1_grid_v1__A_r10`
- Sweep dirs (examples; see `artifacts/sweep_exp1_grid_v1__A_r9__*` and `artifacts/sweep_exp1_grid_v1__A_r10__*`):
  - `artifacts/sweep_exp1_grid_v1__A_r9__cr0p20__sig0p25__cfa5p00__cws0p05/`
  - `artifacts/sweep_exp1_grid_v1__A_r10__cr0p20__sig1p00__cfa10p00__cws0p10/`
- Sweep summaries written:
  - `artifacts/sweep_exp1_grid_v1__A_r9__*/sweep_summary.json`
  - `artifacts/sweep_exp1_grid_v1__A_r10__*/sweep_summary.json`
- Combined grid-level summary artifact (regenerated through `A_r10`):
  - `artifacts/exp1_grid_v1_summary__A.json` (rows=50)

### What we observed (post-run)
From `artifacts/exp1_grid_v1_summary__A.json` (50 regime points total; primary metric M3b regret):
- Proposed vs baseline_a: wins 37 / 50, losses 13 / 50.
- Proposed vs baseline_b: wins 37 / 50, losses 13 / 50.

Progress (coverage): Seed Set A is now at **50 / 54** regime points completed.

Note: An `A_r11` sweep directory exists but is **partial** (not finalized). We intentionally did **not** continue or start the final chunk yet.

### What we changed (if any)
- None. (No code/config/policy/metric changes; only additional grid points executed and summaries regenerated from artifacts.)

### What we did NOT change (explicit)
- Kept fixed:
  - `configs/locked/exp1_grid_v1/*` (locked grid configs)
  - seed set A definition (0–29)
  - metric implementations and aggregation rules (artifact-derived)

### Next actions
- When ready, finish Seed Set A to 54 / 54 by completing `exp1_grid_v1__A_r11` (start-index 50, limit-points 4), then run Seed Set B (30–59).

### 2026-01-20 — Experiment 1 (Grid v1): Seed Set A complete (54 / 54) (EVAL)

### Date:
2026-01-20

### Phase: EVAL

### Context / intent (1–3 sentences)
Finish the remaining Seed Set A grid points for preregistered `grid_v1` (seeds 0–29), completing full 54/54 regime coverage under the locked configs and metrics.

### Hypothesis / expectation (pre-run)
Unknown. Continued characterization; we accept wins and losses as evidence.

### Runs executed (artifact pointers)
- Final chunk sweep prefix: `exp1_grid_v1__A_r11` (4 regime points; each = 3 systems × 30 seeds = 90 runs)
- Sweep dirs:
  - `artifacts/sweep_exp1_grid_v1__A_r11__cr0p20__sig1p00__cfa20p00__cws0p05/`
  - `artifacts/sweep_exp1_grid_v1__A_r11__cr0p20__sig1p00__cfa20p00__cws0p10/`
  - `artifacts/sweep_exp1_grid_v1__A_r11__cr0p20__sig1p00__cfa5p00__cws0p05/`
  - `artifacts/sweep_exp1_grid_v1__A_r11__cr0p20__sig1p00__cfa5p00__cws0p10/`
- Sweep summaries written:
  - `artifacts/sweep_exp1_grid_v1__A_r11__*/sweep_summary.json`
- Combined grid-level summary artifact (full Seed Set A, 54 regime points):
  - `artifacts/exp1_grid_v1_summary__A.json` (rows=54)

### What we observed (post-run)
From `artifacts/exp1_grid_v1_summary__A.json` (54 regime points total; primary metric M3b regret):
- Proposed vs baseline_a: wins 38 / 54, losses 15 / 54, ties 0 / 54.
- Proposed vs baseline_b: wins 39 / 54, losses 15 / 54, ties 0 / 54.

Progress (coverage): Seed Set A is now at **54 / 54** regime points completed.

### What we changed (if any)
- None. (No code/config/policy/metric changes; only completion of remaining points and artifact-derived summaries.)

### What we did NOT change (explicit)
- Kept fixed:
  - `configs/locked/exp1_grid_v1/*` (locked grid configs)
  - seed set A definition (0–29)
  - metric implementations and aggregation rules (artifact-derived)

### Next actions
- Run Seed Set B holdout (seeds 30–59) over the same 54 regime points under a new sweep prefix family (e.g., `exp1_grid_v1__B_r1`, chunked 5 points at a time) and compare A vs B regime-map stability.


### 2026-01-20 — Experiment 1 (Grid v1): Seed Set B holdout (Batch 1: 5 regime points) complete (EVAL)

### Date:
2026-01-20

### Phase: EVAL

### Context / intent (1–3 sentences)
Run the first holdout chunk for Seed Set B (seeds 30–59) over 5 regime points (3 systems × 30 seeds each = 450 runs) using locked configs and existing metric code.

### Hypothesis / expectation (pre-run)
Holdout stability check: Seed Set B should broadly agree with Seed Set A (wins/losses may shift, but no obvious instrumentation/pathology).

### Runs executed (artifact pointers)
- Command:
  - `.venv\\Scripts\\exp-suite.exe grid-run --sweep-prefix exp1_grid_v1__B_r1 --seed-start 30 --seed-end 59 --start-index 0 --limit-points 5 --resume`
- Git revision recorded in artifacts: `bf397a0`
- Sweep dirs (each 90/90, FINALIZED; each contains `sweep_manifest.json` and per-run `run_manifest.json`):
  - `artifacts/sweep_exp1_grid_v1__B_r1__cr0p01__sig0p25__cfa10p00__cws0p05/`
  - `artifacts/sweep_exp1_grid_v1__B_r1__cr0p01__sig0p25__cfa10p00__cws0p10/`
  - `artifacts/sweep_exp1_grid_v1__B_r1__cr0p01__sig0p25__cfa20p00__cws0p05/`
  - `artifacts/sweep_exp1_grid_v1__B_r1__cr0p01__sig0p25__cfa20p00__cws0p10/`
  - `artifacts/sweep_exp1_grid_v1__B_r1__cr0p01__sig0p25__cfa5p00__cws0p05/`

### Data integrity / “is this legit?”
- Yes: run completeness is signaled by `run_manifest.json` written last (includes checksums for each artifact file); each sweep is marked complete by `sweep_manifest.json` and `sweep_progress.json` with `last_run_id = FINALIZED`.
- “Resume oddness” seen during the run was due to the tool being strict about incomplete run dirs (missing `run_manifest.json`) while a run is mid-flight; we did not edit configs or code during execution.

### What we changed (if any)
- None. (No code/config/policy/metric changes; only additional holdout runs executed and artifacts written.)

### What we did NOT change (explicit)
- Kept fixed:
  - `configs/locked/exp1_grid_v1/*` (locked grid configs)
  - seed set B definition (30–59)
  - metric implementations and aggregation rules (artifact-derived)


### 2026-01-22 — Experiment 1 (Grid v1): Seed Set B holdout (Batch 8: 5 regime points; indices 35–39) complete (EVAL)

### Date:
2026-01-22

### Phase: EVAL

### Context / intent (1–3 sentences)
Continue Seed Set B holdout (seeds 30–59) with the next 5 regime points (indices 35–39) under the same locked configs and metric code.

### Hypothesis / expectation (pre-run)
Holdout stability check: performance trends should broadly match Seed Set A.

### Runs executed (artifact pointers)
- Command:
  - `.venv\\Scripts\\exp-suite.exe grid-run --sweep-prefix exp1_grid_v1__B_r1 --seed-start 30 --seed-end 59 --start-index 35 --limit-points 5 --resume`
- Git revision recorded in artifacts: `871e2e5`
- Sweep dirs (each 90/90, FINALIZED; each contains `sweep_manifest.json` and per-run `run_manifest.json`):
  - `artifacts/sweep_exp1_grid_v1__B_r1__cr0p10__sig1p00__cfa5p00__cws0p10/`
  - `artifacts/sweep_exp1_grid_v1__B_r1__cr0p20__sig0p25__cfa10p00__cws0p05/`
  - `artifacts/sweep_exp1_grid_v1__B_r1__cr0p20__sig0p25__cfa10p00__cws0p10/`
  - `artifacts/sweep_exp1_grid_v1__B_r1__cr0p20__sig0p25__cfa20p00__cws0p05/`
  - `artifacts/sweep_exp1_grid_v1__B_r1__cr0p20__sig0p25__cfa20p00__cws0p10/`

### Data integrity / completeness
- All 5 sweeps are **90/90 FINALIZED**.
- All per-run subdirs have `run_manifest.json`, and all per-run subdirs have `metrics.json`.

### What we changed (if any)
- None. (No code/config/policy/metric changes; only additional holdout runs executed and artifacts written.)

### What we did NOT change (explicit)
- Kept fixed:
  - `configs/locked/exp1_grid_v1/*` (locked grid configs)
  - seed set B definition (30–59)
  - metric implementations and aggregation rules (artifact-derived)

### Next actions
- Continue Seed Set B in 5-point batches until all 54 regime points are covered (next batch: `--start-index 5 --limit-points 5`).
- After coverage is complete, generate/record the Seed Set B grid summary and compare A vs B regime-map stability.

### 2026-01-21 — Experiment 1 (Grid v1): Seed Set B holdout (Batch 2: 5 regime points; indices 5–9) complete (EVAL)

### Date:
2026-01-21

### Phase: EVAL

### Context / intent (1–3 sentences)
Continue Seed Set B holdout (seeds 30–59) with the next 5 regime points (indices 5–9) under the same locked configs and metric code.

### Hypothesis / expectation (pre-run)
Holdout stability check: performance trends should broadly match Seed Set A.

### Runs executed (artifact pointers)
- Command:
  - `.venv\\Scripts\\exp-suite.exe grid-run --sweep-prefix exp1_grid_v1__B_r1 --seed-start 30 --seed-end 59 --start-index 5 --limit-points 5 --resume`
- Git revision recorded in artifacts: `4880b4d`
- Sweep dirs (each 90/90, FINALIZED; each contains `sweep_manifest.json` and per-run `run_manifest.json`):
  - `artifacts/sweep_exp1_grid_v1__B_r1__cr0p01__sig0p25__cfa5p00__cws0p10/`
  - `artifacts/sweep_exp1_grid_v1__B_r1__cr0p01__sig0p50__cfa10p00__cws0p05/`
  - `artifacts/sweep_exp1_grid_v1__B_r1__cr0p01__sig0p50__cfa10p00__cws0p10/`
  - `artifacts/sweep_exp1_grid_v1__B_r1__cr0p01__sig0p50__cfa20p00__cws0p05/`
  - `artifacts/sweep_exp1_grid_v1__B_r1__cr0p01__sig0p50__cfa20p00__cws0p10/`

### Data integrity / completeness
- All 5 sweeps are **90/90 FINALIZED**.
- All per-run subdirs have `run_manifest.json`, and all per-run subdirs have `metrics.json`.

### What we changed (if any)
- None. (No code/config/policy/metric changes; only additional holdout runs executed and artifacts written.)

### What we did NOT change (explicit)
- Kept fixed:
  - `configs/locked/exp1_grid_v1/*` (locked grid configs)
  - seed set B definition (30–59)
  - metric implementations and aggregation rules (artifact-derived)

### Next actions
- Continue Seed Set B in 5-point batches until all 54 regime points are covered (next batch: `--start-index 10 --limit-points 5`).
- After coverage is complete, generate/record the Seed Set B grid summary and compare A vs B regime-map stability.

### 2026-01-21 — Experiment 1 (Grid v1): Seed Set B holdout (Batch 3: 5 regime points; indices 10–14) complete (EVAL)

### Date:
2026-01-21

### Phase: EVAL

### Context / intent (1–3 sentences)
Continue Seed Set B holdout (seeds 30–59) with the next 5 regime points (indices 10–14) under the same locked configs and metric code.

### Hypothesis / expectation (pre-run)
Holdout stability check: performance trends should broadly match Seed Set A.

### Runs executed (artifact pointers)
- Command:
  - `.venv\\Scripts\\exp-suite.exe grid-run --sweep-prefix exp1_grid_v1__B_r1 --seed-start 30 --seed-end 59 --start-index 10 --limit-points 5 --resume`
- Git revision recorded in artifacts: `bc63e44`
- Sweep dirs (each 90/90, FINALIZED; each contains `sweep_manifest.json` and per-run `run_manifest.json`):
  - `artifacts/sweep_exp1_grid_v1__B_r1__cr0p01__sig0p50__cfa5p00__cws0p05/`
  - `artifacts/sweep_exp1_grid_v1__B_r1__cr0p01__sig0p50__cfa5p00__cws0p10/`
  - `artifacts/sweep_exp1_grid_v1__B_r1__cr0p01__sig1p00__cfa10p00__cws0p05/`
  - `artifacts/sweep_exp1_grid_v1__B_r1__cr0p01__sig1p00__cfa10p00__cws0p10/`
  - `artifacts/sweep_exp1_grid_v1__B_r1__cr0p01__sig1p00__cfa20p00__cws0p05/`

### Data integrity / completeness
- All 5 sweeps are **90/90 FINALIZED**.
- All per-run subdirs have `run_manifest.json`, and all per-run subdirs have `metrics.json`.

### What we changed (if any)
- None. (No code/config/policy/metric changes; only additional holdout runs executed and artifacts written.)

### What we did NOT change (explicit)
- Kept fixed:
  - `configs/locked/exp1_grid_v1/*` (locked grid configs)
  - seed set B definition (30–59)
  - metric implementations and aggregation rules (artifact-derived)

### Next actions
- Continue Seed Set B in 5-point batches until all 54 regime points are covered (next batch: `--start-index 15 --limit-points 5`).
- After coverage is complete, generate/record the Seed Set B grid summary and compare A vs B regime-map stability.

### 2026-01-21 — Experiment 1 (Grid v1): Seed Set B holdout (Batch 4: 5 regime points; indices 15–19) complete (EVAL)

### Date:
2026-01-21

### Phase: EVAL

### Context / intent (1–3 sentences)
Continue Seed Set B holdout (seeds 30–59) with the next 5 regime points (indices 15–19) under the same locked configs and metric code.

### Hypothesis / expectation (pre-run)
Holdout stability check: performance trends should broadly match Seed Set A.

### Runs executed (artifact pointers)
- Command:
  - `.venv\\Scripts\\exp-suite.exe grid-run --sweep-prefix exp1_grid_v1__B_r1 --seed-start 30 --seed-end 59 --start-index 15 --limit-points 5 --resume`
- Git revision recorded in artifacts: `a2b2285`
- Sweep dirs (each 90/90, FINALIZED; each contains `sweep_manifest.json` and per-run `run_manifest.json`):
  - `artifacts/sweep_exp1_grid_v1__B_r1__cr0p01__sig1p00__cfa20p00__cws0p10/`
  - `artifacts/sweep_exp1_grid_v1__B_r1__cr0p01__sig1p00__cfa5p00__cws0p05/`
  - `artifacts/sweep_exp1_grid_v1__B_r1__cr0p01__sig1p00__cfa5p00__cws0p10/`
  - `artifacts/sweep_exp1_grid_v1__B_r1__cr0p10__sig0p25__cfa10p00__cws0p05/`
  - `artifacts/sweep_exp1_grid_v1__B_r1__cr0p10__sig0p25__cfa10p00__cws0p10/`

### Data integrity / completeness
- All 5 sweeps are **90/90 FINALIZED**.
- All per-run subdirs have `run_manifest.json`, and all per-run subdirs have `metrics.json`.

### What we changed (if any)
- None. (No code/config/policy/metric changes; only additional holdout runs executed and artifacts written.)

### What we did NOT change (explicit)
- Kept fixed:
  - `configs/locked/exp1_grid_v1/*` (locked grid configs)
  - seed set B definition (30–59)
  - metric implementations and aggregation rules (artifact-derived)

### Next actions
- Continue Seed Set B in 5-point batches until all 54 regime points are covered (next batch: `--start-index 20 --limit-points 5`).
- After coverage is complete, generate/record the Seed Set B grid summary and compare A vs B regime-map stability.

### 2026-01-21 — Experiment 1 (Grid v1): Seed Set B holdout (Batch 5: 5 regime points; indices 20–24) complete (EVAL)

### Date:
2026-01-21

### Phase: EVAL

### Context / intent (1–3 sentences)
Continue Seed Set B holdout (seeds 30–59) with the next 5 regime points (indices 20–24) under the same locked configs and metric code.

### Hypothesis / expectation (pre-run)
Holdout stability check: performance trends should broadly match Seed Set A.

### Runs executed (artifact pointers)
- Command:
  - `.venv\\Scripts\\exp-suite.exe grid-run --sweep-prefix exp1_grid_v1__B_r1 --seed-start 30 --seed-end 59 --start-index 20 --limit-points 5 --resume`
- Git revision recorded in artifacts: `12f18de`
- Sweep dirs (each 90/90, FINALIZED; each contains `sweep_manifest.json` and per-run `run_manifest.json`):
  - `artifacts/sweep_exp1_grid_v1__B_r1__cr0p10__sig0p25__cfa20p00__cws0p05/`
  - `artifacts/sweep_exp1_grid_v1__B_r1__cr0p10__sig0p25__cfa20p00__cws0p10/`
  - `artifacts/sweep_exp1_grid_v1__B_r1__cr0p10__sig0p25__cfa5p00__cws0p05/`
  - `artifacts/sweep_exp1_grid_v1__B_r1__cr0p10__sig0p25__cfa5p00__cws0p10/`
  - `artifacts/sweep_exp1_grid_v1__B_r1__cr0p10__sig0p50__cfa10p00__cws0p05/`

### Data integrity / completeness
- All 5 sweeps are **90/90 FINALIZED**.
- All per-run subdirs have `run_manifest.json`, and all per-run subdirs have `metrics.json`.

### What we changed (if any)
- None. (No code/config/policy/metric changes; only additional holdout runs executed and artifacts written.)

### What we did NOT change (explicit)
- Kept fixed:
  - `configs/locked/exp1_grid_v1/*` (locked grid configs)
  - seed set B definition (30–59)
  - metric implementations and aggregation rules (artifact-derived)

### Next actions
- Continue Seed Set B in 5-point batches until all 54 regime points are covered (next batch: `--start-index 25 --limit-points 5`).
- After coverage is complete, generate/record the Seed Set B grid summary and compare A vs B regime-map stability.

### 2026-01-22 — Experiment 1 (Grid v1): Seed Set B holdout (Batch 6: 5 regime points; indices 25–29) complete (EVAL)

### Date:
2026-01-22

### Phase: EVAL

### Context / intent (1–3 sentences)
Finish the final Seed Set B holdout chunk (seeds 30–59) over the last 5 regime points (indices 25–29), completing the preregistered `grid_v1` holdout coverage for the `exp1_grid_v1__B_r1` prefix.

### Hypothesis / expectation (pre-run)
Holdout stability check: Seed Set B should broadly agree with Seed Set A regime-map directionality (wins/losses may shift, but no obvious instrumentation/pathology).

### Runs executed (artifact pointers)
- Command:
  - `.venv\\Scripts\\exp-suite.exe grid-run --sweep-prefix exp1_grid_v1__B_r1 --seed-start 30 --seed-end 59 --start-index 25 --limit-points 5 --resume`
- Git revision recorded in artifacts: `e1ce133`
- Sweep dirs (each 90/90, FINALIZED; each contains `sweep_manifest.json` and per-run `run_manifest.json`):
  - `artifacts/sweep_exp1_grid_v1__B_r1__cr0p10__sig0p50__cfa10p00__cws0p10/`
  - `artifacts/sweep_exp1_grid_v1__B_r1__cr0p10__sig0p50__cfa20p00__cws0p05/`
  - `artifacts/sweep_exp1_grid_v1__B_r1__cr0p10__sig0p50__cfa20p00__cws0p10/`
  - `artifacts/sweep_exp1_grid_v1__B_r1__cr0p10__sig0p50__cfa5p00__cws0p05/`
  - `artifacts/sweep_exp1_grid_v1__B_r1__cr0p10__sig0p50__cfa5p00__cws0p10/`

### Data integrity / completeness
- All 5 sweeps are **90/90 FINALIZED** (`sweep_progress.json` has `last_run_id = FINALIZED` and `completed = total = 90`).
- For these sweeps, per-run subdirs have `run_manifest.json`, and per-run subdirs have `metrics.json`.
- Note: during monitoring we observed the CLI’s strictness around incomplete run dirs (missing `run_manifest.json`) while a run is mid-flight; this affected resumability but did not change configs or code during execution.

### What we changed (if any)
- None. (No code/config/policy/metric changes; only additional holdout runs executed and artifacts written.)

### What we did NOT change (explicit)
- Kept fixed:
  - `configs/locked/exp1_grid_v1/*` (locked grid configs)
  - seed set B definition (30–59)
  - metric implementations and aggregation rules (artifact-derived)

### Next actions
- Generate/record the Seed Set B grid summary artifact and compare A vs B regime-map stability.

### 2026-01-22 — Experiment 1 (Grid v1): Seed Set B holdout (`exp1_grid_v1__B_r1`) audit + summary artifact (EVAL)

### Date:
2026-01-22

### Phase: EVAL

### Context / intent (1–3 sentences)
Confirm that the full Seed Set B holdout artifacts for `exp1_grid_v1__B_r1` are complete and non-duplicated (committee-defensible “on disk truth”), then write the grid-level summary artifact for downstream A vs B comparison.

### Runs executed (artifact pointers)
- Sweep dirs: `artifacts/sweep_exp1_grid_v1__B_r1__*/` (30 sweeps total; 54 grid points are covered by Seed Set B only after all batches, but `B_r1` here is the executed holdout subset in this run family)
- Grid-level summary artifact:
  - `artifacts/exp1_grid_v1_summary__B_r1.json` (rows=30; primary metric `M3b_avg_regret_vs_oracle`)

### Data integrity / “is this legit?”
- All `artifacts/sweep_exp1_grid_v1__B_r1__*` sweep dirs contain both `sweep_progress.json` and `sweep_manifest.json`.
- All 30 sweeps are **90/90 FINALIZED** per `sweep_progress.json`.
- All 30 `sweep_manifest.json` files list **90 run entries**, and on disk there are **2700** run directories with `run_manifest.json` (and `metrics.json`).
- One extra directory exists that is explicitly labeled orphaned:
  - `...__baseline_a__seed39.ORPHANED_20260120T161909` (has `metrics.json` but intentionally no `run_manifest.json`; excluded from audit counts and kept for provenance).

### What we changed (if any)
- **Artifact bookkeeping repairs (no config/metric changes)**:
  - Recreated two missing per-run directories using `exp-suite run` with explicit `--run-id` into the correct sweep directories (so the referenced run IDs in sweep manifests now exist on disk).
  - Rebuilt two `sweep_manifest.json` files from per-run `run_manifest.json` (resume bookkeeping had produced incomplete manifests). Backups were saved as `sweep_manifest.json.bak__pre_rebuild`.
  - These changes do not alter locked configs or metric definitions; they repair metadata completeness for auditability and summarization.

### What we did NOT change (explicit)
- Kept fixed:
  - `configs/locked/exp1_grid_v1/*` (locked grid configs)
  - seed set B definition (30–59)
  - metric implementations and aggregation rules (artifact-derived)



### 2026-01-22 — Experiment 1 (Grid v1): Seed Set B holdout (Batch 7: 5 regime points; indices 30–34) complete (EVAL)

### Date:
2026-01-22

### Phase: EVAL

### Context / intent (1–3 sentences)
Continue Seed Set B holdout (seeds 30–59) with the next 5 regime points (indices 30–34) under the same locked configs and metric code.

### Hypothesis / expectation (pre-run)
Holdout stability check: performance trends should broadly match Seed Set A.

### Runs executed (artifact pointers)
- Command:
  - `.venv\\Scripts\\exp-suite.exe grid-run --sweep-prefix exp1_grid_v1__B_r1 --seed-start 30 --seed-end 59 --start-index 30 --limit-points 5 --resume`
- Git revision recorded in artifacts: `7d32691`
- Sweep dirs (each 90/90, FINALIZED; each contains `sweep_manifest.json` and per-run `run_manifest.json`):
  - `artifacts/sweep_exp1_grid_v1__B_r1__cr0p10__sig1p00__cfa10p00__cws0p05/`
  - `artifacts/sweep_exp1_grid_v1__B_r1__cr0p10__sig1p00__cfa10p00__cws0p10/`
  - `artifacts/sweep_exp1_grid_v1__B_r1__cr0p10__sig1p00__cfa20p00__cws0p05/`
  - `artifacts/sweep_exp1_grid_v1__B_r1__cr0p10__sig1p00__cfa20p00__cws0p10/`
  - `artifacts/sweep_exp1_grid_v1__B_r1__cr0p10__sig1p00__cfa5p00__cws0p05/`

### Data integrity / completeness
- All 5 sweeps are **90/90 FINALIZED**.
- All per-run subdirs have `run_manifest.json`, and all per-run subdirs have `metrics.json`.

### What we changed (if any)
- None. (No code/config/policy/metric changes; only additional holdout runs executed and artifacts written.)

### What we did NOT change (explicit)
- Kept fixed:
  - `configs/locked/exp1_grid_v1/*` (locked grid configs)
  - seed set B definition (30–59)
  - metric implementations and aggregation rules (artifact-derived)


