$ErrorActionPreference = "Stop"

# Advisor Go/No-Go gate for Exp3:
# - Runs a small-but-real identity reduction check on the actual Exp2 base-point set
# - Writes a JSON report you can attach in prereg notes
#
# This is intended to be run BEFORE any Exp3 shock sweep.

$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Resolve-Path (Join-Path $ROOT ".."))

if (Test-Path .\.venv\Scripts\Activate.ps1) { . .\.venv\Scripts\Activate.ps1 }

$GATE_OUT = "C:\exp3_go_nogo_gate_artifacts"
New-Item -ItemType Directory -Force -Path $GATE_OUT | Out-Null
New-Item -ItemType Directory -Force -Path ".\artifacts" | Out-Null

Write-Host "exp-suite version:"
exp-suite version

Write-Host "Gate Step 1: generate identity configs for Exp3 (inherits Exp2 base points) ..."
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

Write-Host "Gate Step 2: run Exp2 base-point sweeps (3 seeds, all base points) ..."
exp-suite exp2-policy-run `
  --config-dir .\configs\locked\exp2_policy_v2_16pt `
  --experiment-id exp2_policy_v2_16pt `
  --out $GATE_OUT `
  --sweep-prefix exp2_policy_v2_16pt__GATE `
  --seed-start 0 --seed-end 2 `
  --limit-points 12 `
  --resume `
  --progress-every 10

Write-Host "Gate Step 3: run Exp3 identity sweeps (same seeds, same base points) ..."
exp-suite exp3-shock-run `
  --config-dir .\configs\locked\exp3_shock_v1_gate `
  --experiment-id exp3_shock_v1_gate `
  --out $GATE_OUT `
  --sweep-prefix exp3_shock_v1_gate__GATE `
  --seed-start 0 --seed-end 2 `
  --limit-points 12 `
  --resume `
  --progress-every 10

Write-Host "Gate Step 4: compare Exp2 vs Exp3(identity) and write report ..."
python .\scripts\exp3_identity_reduction_gate_report.py `
  --exp2-artifacts-dir $GATE_OUT `
  --exp2-sweep-prefix exp2_policy_v2_16pt__GATE `
  --exp3-artifacts-dir $GATE_OUT `
  --exp3-sweep-prefix exp3_shock_v1_gate__GATE `
  --abs-tol 1e-9 `
  --rel-tol 0.0 `
  --out-json .\artifacts\exp3_identity_reduction_gate.json

Write-Host "Done. Gate artifacts: $GATE_OUT"
Write-Host "Gate report: artifacts\\exp3_identity_reduction_gate.json"


