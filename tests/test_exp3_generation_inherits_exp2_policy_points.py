from __future__ import annotations

from pathlib import Path

from exp_suite.grid import generate_exp3_shock_sweep_configs


def test_exp3_generate_from_exp2_policy_dir_produces_pointwise_lineage(tmp_path: Path) -> None:
    exp2_dir = Path("configs/locked/exp2_policy_v2_16pt")
    assert exp2_dir.exists()

    policies = ["always_act", "always_wait", "wait_on_conflict", "risk_threshold"]
    shocks = [
        {
            "shape": "identity",
            "magnitude": 1.0,
            "start_frac": 0.2,
            "duration_frac": 0.2,
            "apply_to": ["cost_false_act", "cost_false_wait", "wait_cost"],
        }
    ]

    written = generate_exp3_shock_sweep_configs(
        base_exp2_config_path=Path("configs/locked/exp2_policy_v2_base.toml"),
        out_dir=tmp_path,
        experiment_id="unit_exp3_from_exp2_policy",
        fixed_system="proposed",
        policies=policies,
        shock_models=shocks,
        exp2_policy_config_dir=exp2_dir,
        exp2_policy_experiment_id="exp2_policy_v2_16pt",
        enforce_inheritance=True,
    )

    # 12 exp2 points × 4 policies × 1 shock = 48 configs
    assert len(written) == 48

    stems = sorted(p.stem for p in written)
    assert any("__wc_linear__ps0p05__shock_identity__m1p00__s0p20__d0p20__always_act" in s for s in stems)

    sample = written[0].read_text(encoding="utf-8")
    assert 'kind = "exp3"' in sample
    assert "inherits_from_exp2_config_path" in sample
    assert "inherits_from_exp2_config_sha256" in sample
    assert "enforce_inheritance = true" in sample


