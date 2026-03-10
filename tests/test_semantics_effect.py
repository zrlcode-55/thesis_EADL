from __future__ import annotations

import json
from pathlib import Path

import pyarrow.parquet as pq

from exp_suite.config import load_config_toml
from exp_suite.decisions import generate_exp1_decisions
from exp_suite.workload import generate_exp1_events


def test_same_evidence_different_decisions_between_semantics(tmp_path: Path) -> None:
    cfg = load_config_toml(Path("configs/exp1_minimal.toml"))
    assert cfg.kind == "exp1"

    events = generate_exp1_events(cfg, seed=0)

    cfg_a = cfg.model_copy(update={"system": "baseline_a"})
    dec_a = generate_exp1_decisions(events, cfg_a, seed=0, policy="wait_on_conflict")

    cfg_b = cfg.model_copy(update={"system": "baseline_b"})
    dec_b = generate_exp1_decisions(events, cfg_b, seed=0, policy="wait_on_conflict")

    # proposed preserves conflicts, so wait_on_conflict defers more often
    cfg_p = cfg.model_copy(update={"system": "proposed"})
    dec_p = generate_exp1_decisions(events, cfg_p, seed=0, policy="wait_on_conflict")

    a_df = dec_a.decisions.to_pandas()
    b_df = dec_b.decisions.to_pandas()
    p_df = dec_p.decisions.to_pandas()

    assert len(a_df) == len(b_df) == len(p_df) > 0

    a_wait = (a_df["action_id"] == "WAIT").mean()
    b_wait = (b_df["action_id"] == "WAIT").mean()
    p_wait = (p_df["action_id"] == "WAIT").mean()
    assert p_wait >= a_wait
    assert p_wait >= b_wait


