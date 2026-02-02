$ErrorActionPreference = "Stop"

# Runs Exp3 shock sweep v1, inheriting regime points from the Exp2 policy v2 16pt sweep.
# This enforces the thesis contract:
#   Exp3 == Exp2 apparatus (per-point) + shock only
#
# Output is written to a local (non-OneDrive) directory by default for robustness.

$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Resolve-Path (Join-Path $ROOT ".."))

if (Test-Path .\.venv\Scripts\Activate.ps1) { . .\.venv\Scripts\Activate.ps1 }

$OUT = "C:\exp3_shock_v1_48sweeps_artifacts"
New-Item -ItemType Directory -Force -Path $OUT | Out-Null

# Quick disk sanity (fails later if full; this is just an early warning)
try {
  $c = Get-PSDrive -Name C
  Write-Host ("C: free space: {0:N2} GB" -f ($c.Free/1GB))
} catch {}

Write-Host "exp-suite version:"
exp-suite version

Write-Host "Pre-run gate: Exp3(identity) reduces to Exp2 (fast check) ..."
if (Get-Command exp-suite -ErrorAction SilentlyContinue) {
  exp-suite exp3-verify-identity
} else {
  python -m exp_suite.cli exp3-verify-identity
}

Write-Host "Advisor Go/No-Go gate (recorded): Exp3(identity) reduces to Exp2 on the real base-point set ..."
Write-Host "See docs/exp3_go_no_go_prereg.md and artifacts/exp3_identity_reduction_gate.json"
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\run_exp3_go_nogo_gate.ps1

Write-Host "Generating IDENTITY gate configs (no-shock equivalence) ..."
exp-suite exp3-shock-generate `
  --out-dir .\configs\locked\exp3_shock_v1_gate `
  --experiment-id exp3_shock_v1_gate `
  --fixed-system proposed `
  --exp2-policy-config-dir .\configs\locked\exp2_policy_v2_16pt `
  --exp2-policy-experiment-id exp2_policy_v2_16pt `
  --shock-shape identity `
  --shock-magnitude 1.0 `
  --shock-timing early `
  --shock-duration-frac 0.2 `
  --apply-to cost_false_act --apply-to cost_false_wait --apply-to wait_cost `
  --enforce-inheritance

Write-Host "Smoke test (identity gate; 2 points, 3 seeds) ..."
exp-suite exp3-shock-run `
  --config-dir .\configs\locked\exp3_shock_v1_gate `
  --experiment-id exp3_shock_v1_gate `
  --out $OUT `
  --sweep-prefix exp3_shock_v1_gate__A_smoke `
  --seed-start 0 --seed-end 2 `
  --limit-points 2 `
  --resume `
  --progress-every 1

Write-Host "Generating FULL Exp3 shock configs (48 sweeps = 12 Exp2 base points × 4 hypothesis-driven shock keys) ..."
# IMPORTANT: We delete and regenerate to avoid stale configs from older, larger grids.
$FULL_CFG_DIR = ".\configs\locked\exp3_shock_v1_48sweeps"
if (Test-Path $FULL_CFG_DIR) { Remove-Item -Recurse -Force $FULL_CFG_DIR }

# Shock set (deterministic, minimal, defensible):
#  - identity control (1x, early)  [records the 'Exp3 reduces to Exp2 when shocks are disabled' claim]
#  - step, early, high severity (10x)
#  - step, late, high severity (10x)
#  - ramp, early, moderate severity (2x)
#
# This covers: control + phase sensitivity + severity + shape without cartesian blowup.

exp-suite exp3-shock-generate `
  --out-dir $FULL_CFG_DIR `
  --experiment-id exp3_shock_v1_48sweeps `
  --fixed-system proposed `
  --exp2-policy-config-dir .\configs\locked\exp2_policy_v2_16pt `
  --exp2-policy-experiment-id exp2_policy_v2_16pt `
  --shock-shape identity `
  --shock-magnitude 1.0 `
  --shock-timing early `
  --shock-duration-frac 0.2 `
  --apply-to cost_false_act --apply-to cost_false_wait --apply-to wait_cost `
  --enforce-inheritance

exp-suite exp3-shock-generate `
  --out-dir $FULL_CFG_DIR `
  --experiment-id exp3_shock_v1_48sweeps `
  --fixed-system proposed `
  --exp2-policy-config-dir .\configs\locked\exp2_policy_v2_16pt `
  --exp2-policy-experiment-id exp2_policy_v2_16pt `
  --shock-shape step `
  --shock-magnitude 10.0 `
  --shock-timing early `
  --shock-duration-frac 0.2 `
  --apply-to cost_false_act --apply-to cost_false_wait --apply-to wait_cost `
  --enforce-inheritance

exp-suite exp3-shock-generate `
  --out-dir $FULL_CFG_DIR `
  --experiment-id exp3_shock_v1_48sweeps `
  --fixed-system proposed `
  --exp2-policy-config-dir .\configs\locked\exp2_policy_v2_16pt `
  --exp2-policy-experiment-id exp2_policy_v2_16pt `
  --shock-shape step `
  --shock-magnitude 10.0 `
  --shock-timing late `
  --shock-duration-frac 0.2 `
  --apply-to cost_false_act --apply-to cost_false_wait --apply-to wait_cost `
  --enforce-inheritance

exp-suite exp3-shock-generate `
  --out-dir $FULL_CFG_DIR `
  --experiment-id exp3_shock_v1_48sweeps `
  --fixed-system proposed `
  --exp2-policy-config-dir .\configs\locked\exp2_policy_v2_16pt `
  --exp2-policy-experiment-id exp2_policy_v2_16pt `
  --shock-shape ramp `
  --shock-magnitude 2.0 `
  --shock-timing early `
  --shock-duration-frac 0.2 `
  --apply-to cost_false_act --apply-to cost_false_wait --apply-to wait_cost `
  --enforce-inheritance

Write-Host "Full Seed Set A (0-29) ..."
exp-suite exp3-shock-run `
  --config-dir $FULL_CFG_DIR `
  --experiment-id exp3_shock_v1_48sweeps `
  --out $OUT `
  --sweep-prefix exp3_shock_v1_48sweeps__A `
  --seed-start 0 --seed-end 29 `
  --resume `
  --progress-every 10

Write-Host "Full Holdout Seed Set B (30-59) ..."
exp-suite exp3-shock-run `
  --config-dir $FULL_CFG_DIR `
  --experiment-id exp3_shock_v1_48sweeps `
  --out $OUT `
  --sweep-prefix exp3_shock_v1_48sweeps__B `
  --seed-start 30 --seed-end 59 `
  --resume `
  --progress-every 10

Write-Host "Done. Artifacts root: $OUT"


