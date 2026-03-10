from __future__ import annotations

from pathlib import Path

from exp_suite.config import load_config_toml
from exp_suite.workload import generate_exp1_events


def test_matched_seed_generates_identical_events_across_systems() -> None:
    cfg_a = load_config_toml(Path("configs/locked/exp1_eval_v1_baseline_a.toml"))
    cfg_p = load_config_toml(Path("configs/locked/exp1_eval_v1_proposed.toml"))

    assert cfg_a.kind == "exp1"
    assert cfg_p.kind == "exp1"

    # semantics must not affect workload generation — same seed must produce identical events
    events_a = generate_exp1_events(cfg_a, seed=0)
    events_p = generate_exp1_events(cfg_p, seed=0)

    assert events_a.equals(events_p)


