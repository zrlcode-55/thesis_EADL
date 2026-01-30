$ErrorActionPreference = "Stop"

# Runs Exp3 shock sweep v1, inheriting regime points from the Exp2 policy v2 16pt sweep.
# This enforces the thesis contract:
#   Exp3 == Exp2 apparatus (per-point) + shock only
#
# Output is written to a local (non-OneDrive) directory by default for robustness.

$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Resolve-Path (Join-Path $ROOT ".."))

if (Test-Path .\.venv\Scripts\Activate.ps1) { . .\.venv\Scripts\Activate.ps1 }

$OUT = "C:\exp3_shock_v1_artifacts"
New-Item -ItemType Directory -Force -Path $OUT | Out-Null

Write-Host "exp-suite version:"
exp-suite version

Write-Host "Generating locked Exp3 shock configs from Exp2 v2 16pt policy points..."
exp-suite exp3-shock-generate `
  --out-dir .\configs\locked\exp3_shock_v1 `
  --experiment-id exp3_shock_v1 `
  --fixed-system proposed `
  --exp2-policy-config-dir .\configs\locked\exp2_policy_v2_16pt `
  --exp2-policy-experiment-id exp2_policy_v2_16pt `
  --shock-shape identity --shock-shape step --shock-shape impulse --shock-shape ramp `
  --shock-magnitude 1.0 --shock-magnitude 2.0 --shock-magnitude 5.0 --shock-magnitude 10.0 `
  --shock-timing early --shock-timing late `
  --shock-duration-frac 0.2 `
  --apply-to cost_false_act --apply-to cost_false_wait --apply-to wait_cost `
  --enforce-inheritance

Write-Host "Smoke test (2 points, 3 seeds) ..."
exp-suite exp3-shock-run `
  --config-dir .\configs\locked\exp3_shock_v1 `
  --experiment-id exp3_shock_v1 `
  --out $OUT `
  --sweep-prefix exp3_shock_v1__A_smoke `
  --seed-start 0 --seed-end 2 `
  --limit-points 2 `
  --resume `
  --progress-every 1

Write-Host "Full Seed Set A (0-29) ..."
exp-suite exp3-shock-run `
  --config-dir .\configs\locked\exp3_shock_v1 `
  --experiment-id exp3_shock_v1 `
  --out $OUT `
  --sweep-prefix exp3_shock_v1__A `
  --seed-start 0 --seed-end 29 `
  --resume `
  --progress-every 10

Write-Host "Full Holdout Seed Set B (30-59) ..."
exp-suite exp3-shock-run `
  --config-dir .\configs\locked\exp3_shock_v1 `
  --experiment-id exp3_shock_v1 `
  --out $OUT `
  --sweep-prefix exp3_shock_v1__B `
  --seed-start 30 --seed-end 59 `
  --resume `
  --progress-every 10

Write-Host "Done. Artifacts root: $OUT"


