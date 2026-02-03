# Thesis: Decision-Making Under Delayed Reconciliation

**Author:** Zachary Larkin (Vanderbilt CS Master's Thesis)  
**Advisor:** [Dr. Aniruddha Gokhale ]

---

## What this repo is

This is the **complete experimental apparatus** for my thesis on timing decisions when you have conflicting evidence and reconciliation takes time. The core question: if you have multiple data sources that disagree, and you know reconciliation will eventually tell you the truth (but not yet), when do you act vs wait?

**The work:** I built three state-tracking semantics (two baselines, one proposed) and four timing policies, then ran them through ~5000+ synthetic scenarios across three experiments to measure when waiting helps vs hurts.

**The punchline:** The proposed method isn't "always better" — it wins on about 2/3 of the tested regimes and loses on 1/3. That's the honest story, and this repo has the code + data to back it up.

---

## Start here (for committee / peer reviewers)

If you're reviewing this thesis, **read these in order:**

1. **`docs/final_claims.md`** ← **Single source of truth**  
   This is where every claim lives. Every number, every table, every algorithm. It's 786 lines of:
   - What each experiment tested (bounded scope)
   - What the data shows (win/loss counts, holdout stability, delta statistics)
   - What the code does (6 algorithms in pseudocode, anchored to source files)
   - What we're NOT claiming (no "always better", no statistical significance without separate analysis)

2. **This README** ← Overview + map  
   You're reading it. It's the poster.

3. **`docs/experiment1_full_summary.md`** / **`experiment_2_policy_summary__v2_policy.md`** / **`experiment3_full_summary.md`**  
   Artifact-derived experiment summaries (generated from on-disk results via `scripts/generate_*`). These are what fed into `final_claims.md`.

4. **`src/exp_suite/`** ← Implementation  
   The Python package that runs everything. CLI-first, artifact-first. Every run writes Parquet tables + JSON metadata that the analysis scripts read.

---

## What went right (things I'm confident about)

### Reproducibility apparatus
- **Locked configs** (`configs/locked/`): Every experiment point is a preregistered TOML file
- **Artifact-first design**: Metrics are computed from persisted Parquet tables, not "invented" in analysis scripts
- **Deterministic inclusion rules**: Only finalized sweeps with exact seed sets are included (see `scripts/generate_exp1_paper_summary.py` line 107: "This excludes smokes / partial seed sweeps")
- **Code-anchored claims**: Every metric definition in `final_claims.md` points to the exact Python function that computes it

### Holdout stability
- Seed Set A (0–29) vs Seed Set B (30–59) reproduce per-point deltas with Pearson r > 0.999 across all experiments
- This wasn't guaranteed — I split the seeds upfront and didn't peek at B until A was done

### Honest about losses
- Exp1: `proposed` loses on 15/54 points (A) and 18/54 points (B)
- I didn't cherry-pick regimes — these are the preregistered 54-point grid results
- The "Known imperfections" sections in the summaries call out duplicated sweeps, incomplete manifests, and how we handled them deterministically

---

## What was messy (things I'm transparent about)

### External artifacts (Exp2/Exp3)
- The raw sweep directories for Exp2/Exp3 are **not committed** to this repo (they're 10s of GB)
- They live on disk at `C:\exp2_policy_v2_16pt_artifacts` and `C:\exp3_shock_v1_48sweeps_artifacts`
- The in-repo `artifacts/` directory has only **summary CSVs/JSONs** derived from those sweeps
- This is called out explicitly in `final_claims.md` (line 296, line 553)

### Reruns / duplicates (Exp1)
- Seed Set A includes 1 duplicated full sweep (same regime point, rerun)
- I handled this with a deterministic selection rule (newest `created_utc`, ties by directory name)
- 1 sweep had an incomplete `sweep_manifest.json` (I rebuilt it from per-run `run_manifest.json` files)
- These are documented in `final_claims.md` lines 262-263 and `experiment1_full_summary.md`

### Shock scaling limitation (Exp3)
- In the Exp3 v1 sweep, shocks multiply **all** cost components by the same factor
- This makes `risk_threshold` decision boundaries invariant to shocks (both sides scale equally)
- This is **not** a fundamental limitation of the method — it's a design choice for this sweep
- Future work could scale components independently
- Called out as C12 in `final_claims.md` (line 516)

---

## The three experiments (quick summary)

### Experiment 1: Grid v1 (54 regime points)
**Question:** Does conflict-aware state tracking (`proposed`) reduce regret vs baselines that collapse to a single value?  
**Answer:** On 39/54 points (A) and 36/54 points (B), yes. On 15/54 (A) and 18/54 (B), no.  
**Why it's not universal:** High conflict rates + low false-act costs favor baselines (acting fast beats waiting).

### Experiment 2: Policy sweep (12 wait-cost points, 4 policies)
**Question:** Which timing policy wins across different wait-cost regimes?  
**Answer:** `always_act` wins on 12/12 points (both A and B). The other policies pay too much for waiting in these regimes.  
**Why this matters:** Shows the proposed state semantics alone don't determine policy performance — the cost model matters.

### Experiment 3: Shock robustness (48 sweeps = 12 base points × 4 shock types)
**Question:** Do policies remain stable under time-varying cost shocks?  
**Answer:** Yes — holdout stability remains r > 0.999. Identity shock reduces exactly to Exp2 (gate passed). Shock severity dominates tail amplification (step 10× >> ramp 2×).  
**Limitation:** All costs scaled equally in this sweep, so `risk_threshold` boundaries were invariant.

---

## How to regenerate the summaries

All three experiment summaries are **deterministically generated** from on-disk artifacts:

```powershell
# Exp1 (reads from sweep directories under your Exp1 artifact root)
python scripts/generate_exp1_paper_summary.py

# Exp2 (reads from sweep_summary.json per sweep)
python scripts/generate_exp2_policy_summary.py

# Exp3 (reads from sweep directories + generates CSVs/JSONs in artifacts/)
python scripts/analyze_exp3_results.py
```

**Important:** These scripts read from **external artifact directories** for Exp2/Exp3 (default `C:\exp2_policy_v2_16pt_artifacts`, `C:\exp3_shock_v1_48sweeps_artifacts`). If you're reproducing this on a different machine, you'll need those sweep directories or equivalent.

---

## Repository structure (detailed)

```
configs/locked/           # Preregistered, immutable experiment definitions
  exp1_grid_v1/           # 162 configs (54 points × 3 systems)
  exp2_policy_v2_16pt/    # 48 configs (12 base × 4 policies)
  exp3_shock_v1_48sweeps/ # 192 configs (12 base × 4 shocks × 4 policies)

artifacts/                # In-repo summaries + audits (NOT raw sweep dirs)
  audit_*.json            # Completeness checks (finalized sweeps, seed counts)
  exp1_grid_v1_table__*.csv    # Exp1 point-level means per system
  exp3_shock_v1_*__metrics.csv # Exp3 long-form metrics
  exp3_*.json             # Exp3 scenario aggregates + gate reports

scripts/                  # Deterministic report generators
  generate_exp1_paper_summary.py
  generate_exp2_policy_summary.py
  analyze_exp3_results.py
  run_exp*.ps1            # PowerShell sweep runners

docs/                     # Markdown summaries (thesis-ready)
  final_claims.md         # ← SINGLE SOURCE OF TRUTH (start here)
  experiment1_full_summary.md
  experiment_2_policy_summary__v2_policy.md
  experiment3_full_summary.md

src/exp_suite/            # Implementation (see below)
```

---

## Implementation modules (`src/exp_suite/`)

Each module has a single responsibility:

- **`workload.py`**: Generates synthetic conflict + reconciliation event streams
- **`state.py`**: Implements the three state semantics (baseline_a, baseline_b, proposed)
- **`state_view.py`**: Constructs conflict-aware state views for policies
- **`decisions.py`**: Implements the four timing policies (always_act, always_wait, wait_on_conflict, risk_threshold)
- **`reconciliation.py`**: Generates ground-truth outcome labels + arrival times
- **`metrics.py`**: Computes all artifact-derived metrics (M1–M9, E3)
- **`shocks.py`**: Defines time-varying shock schedules for Exp3
- **`config.py`**: Pydantic schemas for TOML configs
- **`runner.py`**: Single-run orchestrator (workload → state → decisions → reconciliation → metrics → artifacts)
- **`cli.py`**: CLI commands (`exp-suite run`, `exp-suite exp2-policy-run`, `exp-suite exp3-shock-run`)
- **`sweep.py`**: Sweep-level aggregation (per-policy mean/CI from per-seed runs)
- **`manifest.py`**: Sweep/run manifest JSON generation + git-rev tracking
- **`artifacts.py`**: Writes per-run Parquet tables + JSON metadata

**Workflow:** `workload.py` → `state.py` + `state_view.py` → `decisions.py` → `reconciliation.py` → `metrics.py` → artifacts written

---

## What you won't find in this repo (and why)

### No p-values / confidence intervals across regimes
I didn't preregister a hypothesis test for "regret is lower across all regimes." I have **per-regime-point win/loss counts** and **holdout stability** (Pearson r > 0.999), but I'm not claiming statistical significance without a separate inferential analysis.

### No real-world deployment claims
This is a synthetic evaluation. The workload generator (`workload.py`) creates controlled conflict scenarios, not real production data. External validity requires separate validation.

### No "always better" claims
Exp1 explicitly shows `proposed` loses on 15-18 points (depending on seed set). Any universal superiority claim is false.

---

## Setup (if you want to run it)

See `docs/README_setup.md` for full instructions. Quick version:

```powershell
# Install dependencies
pip install -r requirements.txt

# Install package in editable mode
pip install -e .

# Verify install
exp-suite version

# Run a minimal test
exp-suite run --config configs/example.toml --seed 0 --out artifacts
```

**OS:** Developed on Windows 10/11 with PowerShell. The Python code is platform-agnostic, but the sweep runner scripts (`scripts/run_exp*.ps1`) are PowerShell.

---

## Tests (smoke checks, not exhaustive)

```powershell
pytest tests/
```

These are **sanity checks**, not a full test suite:
- `test_semantics_effect.py`: Verifies `proposed` exposes conflict_size > 1 when baselines don't
- `test_exp3_shock_identity.py`: Verifies identity shock is a no-op
- `test_matched_seed_events.py`: Verifies Exp2 inherits Exp3 workload generation (same seed → same events)
- `test_exp3_generation_inherits_exp2_policy_points.py`: Verifies Exp3 configs inherit Exp2 base points

---

## For peer reviewers / committee members

### If you want to audit a specific claim:
1. Look up the claim number (C1–C13) in `docs/final_claims.md`
2. See the evidence anchor (artifact file path or code path)
3. For artifact files: check `artifacts/` (in-repo) or external sweep dirs (noted in `final_claims.md`)
4. For code paths: see `src/exp_suite/` (e.g., `metrics.py`, `shocks.py`, `decisions.py`)

### If you want to verify a metric definition:
1. Go to `docs/final_claims.md` → "Shared metric definitions"
2. See the code anchor (e.g., `src/exp_suite/metrics.py`, line 68-82)
3. Read the verbatim code snippet or check the source file

### If you want to understand a policy:
1. Go to `docs/final_claims.md` → "Decision algorithms (policy definitions)"
2. See Algorithm 1-3 (pseudocode + code anchors)
3. For full implementation: `src/exp_suite/decisions.py` (lines 120-175)

### If you want to reproduce the experiment summaries:
1. Make sure you have the external artifact directories (Exp2/Exp3) or equivalent
2. Run the generator scripts (`python scripts/generate_exp1_paper_summary.py`, etc.)
3. Compare output to `docs/experiment*_summary.md`

---

## Acknowledgments

This was harder than I expected. The apparatus is solid, but I made mistakes:
- I reran some Exp1 sweeps when I shouldn't have (handled with deterministic selection)
- I didn't realize Exp2's external artifacts wouldn't fit in the repo until I had 40 GB of Parquet files
- I underestimated how long it would take to document every claim's evidence trail

**What I'd do differently:** 
- Commit a subset of raw sweeps to the repo (e.g., 1 point per experiment) so reviewers can audit the full pipeline end-to-end
- Preregister the Exp2/Exp3 summaries before running (I generated them after, which is fine but less rigorous)
- Write `final_claims.md` earlier in the process (it would have caught gaps sooner)

**What I'm extremely proud of:**
- The inclusion rules are code-anchored and deterministic
- Holdout stability is extremely high (r > 0.999) without cherry-picking
- Every claim is traceable to an artifact or code path
- I didn't hide the losses

---

## Contact

**Zach Larkin** — [zachary.larkin@vanderbilt.edu]  
 
**Thesis defense:** [May 2nd, 2026]

If you're reviewing this and something doesn't make sense, email me. I'd rather clarify now than have you waste time.

