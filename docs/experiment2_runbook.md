### Experiment 2 (Exp2) — Runbook (Cost-Aware Decision Policies)

Exp2 is preregistered in `readme_baseline.md` as **“Cost-Aware Decision Policies”** and is intentionally **very similar** to Exp1:

- **Reuses** the same synthetic evidence stream generator and reconciliation alignment (so we can make matched comparisons)
- **Varies** decision policies and **WAIT cost curvature** (linear vs nonlinear waiting penalty)

> **Thesis note (defensibility)**: The preregistered Exp2 isolation principle is **state semantics fixed; policy varies**.
> The earlier `exp2_grid_v1` “3 systems × 54 regimes” run is useful as a legacy comparison, but it is **not** the strict Exp2 isolation design.
> For the thesis-defensible Exp2, use **`exp2_policy_v1`** (policy sweep) below.

### Where Exp2 lives (organization)

- **Configs**:
  - `configs/exp2_minimal.toml` (dev/smoke)
  - `configs/locked/exp2_eval_v1_*.toml` (eval, locked)
- **Artifacts**:
  - Use `--out .\\artifacts\\exp2` to keep Exp2 outputs separate from Exp1.

### Running a single Exp2 config

```powershell
exp-suite run --config .\configs\exp2_minimal.toml --seed 0 --out .\artifacts\exp2
```

### Running Exp2 as a matched-seed sweep (like Exp1)

Example: compare semantics across the same seeds:

```powershell
exp-suite sweep `
  --config .\configs\locked\exp2_eval_v1_baseline_a.toml `
  --config .\configs\locked\exp2_eval_v1_baseline_b.toml `
  --config .\configs\locked\exp2_eval_v1_proposed.toml `
  --seed-start 0 --seed-end 29 `
  --out .\artifacts\exp2 `
  --sweep-id exp2_eval_v1__A
```

Then summarize:

```powershell
exp-suite summarize-sweep --sweep-dir .\artifacts\exp2\sweep_exp2_eval_v1__A
```

### Running Exp2 over the full preregistered regime grid (Run A smoke → then full)

#### 0) Generate the locked grid configs

Default grid_v1 uses the same 54-point structure as Exp1 (3×3×3×2), but applies the axis to `wait_cost.params.per_second`.

```powershell
exp-suite exp2-grid-generate --out-dir .\configs\locked\exp2_grid_v1 --experiment-id exp2_grid_v1
```

#### 1) Run A smoke test (5 regime points)

This runs only the first 5 regime points (but still runs **all 3 systems × all seeds** for each point).

```powershell
exp-suite grid-run `
  --config-dir .\configs\locked\exp2_grid_v1 `
  --experiment-id exp2_grid_v1 `
  --out .\artifacts\exp2 `
  --sweep-prefix exp2_grid_v1__A_smoke `
  --seed-start 0 --seed-end 29 `
  --limit-points 5 `
  --resume
```

#### 2) Run A full grid (all regime points)

```powershell
exp-suite grid-run `
  --config-dir .\configs\locked\exp2_grid_v1 `
  --experiment-id exp2_grid_v1 `
  --out .\artifacts\exp2 `
  --sweep-prefix exp2_grid_v1__A `
  --seed-start 0 --seed-end 29 `
  --resume
```

#### 3) Holdout (Run B full grid)

```powershell
exp-suite grid-run `
  --config-dir .\configs\locked\exp2_grid_v1 `
  --experiment-id exp2_grid_v1 `
  --out .\artifacts\exp2 `
  --sweep-prefix exp2_grid_v1__B `
  --seed-start 30 --seed-end 59 `
  --resume
```

### Running Exp2 as a thesis-defensible policy sweep (Exp2 Policy v1)

This is the **recommended** Exp2 execution for the thesis:

- **Semantics held fixed**: `system="proposed"` by default
- **Policies vary** within each sweep: `always_act`, `always_wait`, `wait_on_conflict`, `risk_threshold`
- **Curvature varies** across regime points: linear/quadratic/exponential wait-cost families (preregistered defaults)

#### 0) Generate locked policy-sweep configs

```powershell
exp-suite exp2-policy-generate --out-dir .\configs\locked\exp2_policy_v1 --experiment-id exp2_policy_v1
```

#### 1) Smoke test

```powershell
exp-suite exp2-policy-run `
  --config-dir .\configs\locked\exp2_policy_v1 `
  --experiment-id exp2_policy_v1 `
  --out C:\exp2_policy_artifacts `
  --sweep-prefix exp2_policy_v1__A_smoke `
  --seed-start 0 --seed-end 2 `
  --limit-points 2 `
  --resume `
  --progress-every 1
```

#### 2) Seed Set A (analysis)

```powershell
exp-suite exp2-policy-run `
  --config-dir .\configs\locked\exp2_policy_v1 `
  --experiment-id exp2_policy_v1 `
  --out C:\exp2_policy_artifacts `
  --sweep-prefix exp2_policy_v1__A `
  --seed-start 0 --seed-end 29 `
  --resume
```

#### 3) Seed Set B (holdout)

```powershell
exp-suite exp2-policy-run `
  --config-dir .\configs\locked\exp2_policy_v1 `
  --experiment-id exp2_policy_v1 `
  --out C:\exp2_policy_artifacts `
  --sweep-prefix exp2_policy_v1__B `
  --seed-start 30 --seed-end 59 `
  --resume
```

#### One-click runner

If you want a single “do it all” script (generate + smoke + A + B), use:

- `scripts/run_exp2_policy_v1.ps1`

### WAIT cost curvature (the Exp2 axis)

Exp2 configs use:

```toml
[wait_cost]
family = "linear" # or "quadratic", "exponential"
[wait_cost.params]
per_second = 0.1   # linear
```

Suggested alternatives (examples):

- Quadratic:
  - `family="quadratic"`, `k=0.001` where cost \(= k \cdot t^2\)
- Exponential:
  - `family="exponential"`, `k=1.0`, `alpha=0.01` where cost \(= k \cdot (\exp(\alpha t) - 1)\)


