$ErrorActionPreference = "Stop"

# Runs Exp2 policy sweep v2 (16-point wait-cost coverage) in a resume-safe way.
# - Semantics held fixed (default: system=proposed)
# - Policies vary within each wait-cost curvature point (matched seeds)
# - Curvature points expanded to 16 to extend coverage (linear/quadratic/exponential)
#
# Output is written to a local (non-OneDrive) directory by default for robustness.

$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Resolve-Path (Join-Path $ROOT ".."))

if (Test-Path .\.venv\Scripts\Activate.ps1) { . .\.venv\Scripts\Activate.ps1 }

$OUT = "C:\exp2_policy_v2_16pt_artifacts"
New-Item -ItemType Directory -Force -Path $OUT | Out-Null

Write-Host "exp-suite version:"
exp-suite version

Write-Host "Generating locked Exp2 policy configs (v2, 16 points)..."
exp-suite exp2-policy-generate `
  --out-dir .\configs\locked\exp2_policy_v2_16pt `
  --base-config .\configs\locked\exp2_policy_v2_base.toml `
  --experiment-id exp2_policy_v2_16pt `
  --fixed-system proposed `
  --linear-per-second 0.005 --linear-per-second 0.01 --linear-per-second 0.02 --linear-per-second 0.05 --linear-per-second 0.10 --linear-per-second 0.20 `
  --quadratic-k 0.0005 --quadratic-k 0.001 --quadratic-k 0.002 --quadratic-k 0.005 --quadratic-k 0.01 `
  --exponential "0.25,0.05" --exponential "0.5,0.05" --exponential "1.0,0.05" --exponential "0.5,0.1" --exponential "1.0,0.1"

Write-Host "Smoke test (2 points, 3 seeds) ..."
exp-suite exp2-policy-run `
  --config-dir .\configs\locked\exp2_policy_v2_16pt `
  --experiment-id exp2_policy_v2_16pt `
  --out $OUT `
  --sweep-prefix exp2_policy_v2_16pt__A_smoke `
  --seed-start 0 --seed-end 2 `
  --limit-points 2 `
  --resume `
  --progress-every 1

Write-Host "Full Seed Set A (0-29) ..."
exp-suite exp2-policy-run `
  --config-dir .\configs\locked\exp2_policy_v2_16pt `
  --experiment-id exp2_policy_v2_16pt `
  --out $OUT `
  --sweep-prefix exp2_policy_v2_16pt__A `
  --seed-start 0 --seed-end 29 `
  --resume `
  --progress-every 10

Write-Host "Full Holdout Seed Set B (30-59) ..."
exp-suite exp2-policy-run `
  --config-dir .\configs\locked\exp2_policy_v2_16pt `
  --experiment-id exp2_policy_v2_16pt `
  --out $OUT `
  --sweep-prefix exp2_policy_v2_16pt__B `
  --seed-start 30 --seed-end 59 `
  --resume `
  --progress-every 10

Write-Host "Done. Artifacts root: $OUT"


