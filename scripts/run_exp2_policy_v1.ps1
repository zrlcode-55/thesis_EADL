$ErrorActionPreference = "Stop"

# Runs Exp2 policy sweep v1 in a resume-safe way.
# - Semantics held fixed (default: system=proposed)
# - Policies vary within each wait-cost curvature point (matched seeds)
#
# Output is written to a local (non-OneDrive) directory by default for robustness.

$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Resolve-Path (Join-Path $ROOT ".."))

if (Test-Path .\.venv\Scripts\Activate.ps1) { . .\.venv\Scripts\Activate.ps1 }

$OUT = "C:\exp2_policy_artifacts"
New-Item -ItemType Directory -Force -Path $OUT | Out-Null

Write-Host "exp-suite version:"
exp-suite version

Write-Host "Generating locked Exp2 policy configs..."
exp-suite exp2-policy-generate --out-dir .\configs\locked\exp2_policy_v1 --experiment-id exp2_policy_v1 --base-config .\configs\locked\exp2_policy_v1_base.toml

Write-Host "Smoke test (2 wait-cost points, 3 seeds) ..."
exp-suite exp2-policy-run --config-dir .\configs\locked\exp2_policy_v1 --experiment-id exp2_policy_v1 --out $OUT --sweep-prefix exp2_policy_v1__A_smoke --seed-start 0 --seed-end 2 --limit-points 2 --resume --progress-every 1

Write-Host "Full Seed Set A (0-29) ..."
exp-suite exp2-policy-run --config-dir .\configs\locked\exp2_policy_v1 --experiment-id exp2_policy_v1 --out $OUT --sweep-prefix exp2_policy_v1__A --seed-start 0 --seed-end 29 --resume --progress-every 10

Write-Host "Full Holdout Seed Set B (30-59) ..."
exp-suite exp2-policy-run --config-dir .\configs\locked\exp2_policy_v1 --experiment-id exp2_policy_v1 --out $OUT --sweep-prefix exp2_policy_v1__B --seed-start 30 --seed-end 59 --resume --progress-every 10

Write-Host "Done. Artifacts root: $OUT"


