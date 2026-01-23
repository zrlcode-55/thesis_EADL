### Experiment 2 (Exp2) — Runbook (Cost-Aware Decision Policies)

Exp2 is preregistered in `readme_baseline.md` as **“Cost-Aware Decision Policies”** and is intentionally **very similar** to Exp1:

- **Reuses** the same synthetic evidence stream generator and reconciliation alignment (so we can make matched comparisons)
- **Varies** decision policies and **WAIT cost curvature** (linear vs nonlinear waiting penalty)

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


