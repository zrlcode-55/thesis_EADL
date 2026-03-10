from __future__ import annotations

import json

import pyarrow as pa
import pytest

from exp_suite.config import DelayModel, Exp2Config, Exp3Config, ShockModel, WaitCostModel
from exp_suite.metrics import compute_exp2_metrics, compute_exp3_metrics
from exp_suite.schemas import decision_schema, evidence_set_schema, reconciliation_schema


def _mk_tables(*, action_id: str) -> tuple[pa.Table, pa.Table, pa.Table]:
    # Two entities, three timepoints each — keeps churn metrics well-defined.
    evidence_rows = []
    decision_rows = []
    recon_rows = []

    for entity_id in ["e0", "e1"]:
        for t_idx in [0, 1, 2]:
            evid = f"es::{entity_id}::{t_idx}"
            decision_time = pa.scalar(1_700_000_000_000_000 + (t_idx * 1_000_000), type=pa.timestamp("us"))
            arrival_time = pa.scalar(1_700_000_000_000_000 + (t_idx * 1_000_000) + 30_000_000, type=pa.timestamp("us"))

            evidence_rows.append({
                "evidence_set_id": evid,
                "entity_id": entity_id,
                "t_idx": t_idx,
                "decision_time": decision_time.as_py(),
                "evidence_json": "[]",
            })
            decision_rows.append({
                "decision_time": decision_time.as_py(),
                "action_id": action_id,
                "evidence_set_id": evid,
                "confidence": None,
                "expected_cost": None,
                "policy_id": "always_act" if action_id == "ACT" else "always_wait",
            })
            # Alternate ok/needs_act so both loss types are exercised.
            outcome = "ok" if (t_idx % 2 == 0) else "needs_act"
            recon_rows.append({
                "entity_id": entity_id,
                "truth_window_start": decision_time.as_py(),
                "truth_window_end": decision_time.as_py(),
                "authoritative_outcome_json": json.dumps({"outcome": outcome, "t_idx": int(t_idx)}),
                "arrival_time": arrival_time.as_py(),
            })

    decisions = pa.Table.from_pylist(decision_rows, schema=decision_schema())
    evidence_sets = pa.Table.from_pylist(evidence_rows, schema=evidence_set_schema())
    reconciliation = pa.Table.from_pylist(recon_rows, schema=reconciliation_schema())
    return decisions, evidence_sets, reconciliation


def _base_exp2_cfg(*, policy: str) -> Exp2Config:
    return Exp2Config(
        phase="eval",
        experiment_id="unit_test",
        system="proposed",
        variant=policy,
        notes=None,
        entity_count=2,
        source_count=3,
        events_per_entity=3,
        conflict_rate=0.1,
        missingness=0.0,
        delay=DelayModel(family="fixed", params={"seconds": 0.0}),
        decision_lag_seconds=0.0,
        policy=policy,
        cost_false_act=10.0,
        cost_false_wait=10.0,
        correctness_epsilon=0.0,
        wait_cost=WaitCostModel(family="linear", params={"per_second": 0.05}),
        reconciliation_lag_seconds=30.0,
        reconciliation_jitter=DelayModel(family="fixed", params={"seconds": 0.0}),
    )


def _exp3_cfg_identity(*, policy: str) -> Exp3Config:
    base = _base_exp2_cfg(policy=policy).model_dump()
    return Exp3Config.model_validate({
        **base,
        "kind": "exp3",
        "shock": ShockModel(shape="identity", magnitude=1.0, start_frac=0.2, duration_frac=0.2).model_dump(),
    })


def test_exp3_identity_matches_exp2_cost_metrics() -> None:
    decisions, evidence_sets, reconciliation = _mk_tables(action_id="ACT")
    cfg2 = _base_exp2_cfg(policy="always_act")
    cfg3 = _exp3_cfg_identity(policy="always_act")

    m2 = compute_exp2_metrics(decisions=decisions, evidence_sets=evidence_sets, reconciliation=reconciliation, cfg=cfg2)
    m3 = compute_exp3_metrics(decisions=decisions, evidence_sets=evidence_sets, reconciliation=reconciliation, cfg=cfg3)

    assert m2["status"] == "ok"
    assert m3["status"] == "ok"

    for k in ["M3_avg_cost", "M4_p95_cost", "M4_p99_cost", "M5_deferral_rate", "M2_mean_wait_seconds_when_wait"]:
        assert m3["metrics"][k] == pytest.approx(m2["metrics"][k], rel=0.0, abs=0.0)

    assert m3["metrics"]["E3_delta_avg_cost_vs_noshock"] == pytest.approx(0.0, abs=0.0)
    assert m3["metrics"]["E3_p99_amplification"] == pytest.approx(1.0, abs=0.0)


def test_exp3_churn_zero_for_always_act() -> None:
    decisions, evidence_sets, reconciliation = _mk_tables(action_id="ACT")
    cfg3 = _exp3_cfg_identity(policy="always_act")
    m3 = compute_exp3_metrics(decisions=decisions, evidence_sets=evidence_sets, reconciliation=reconciliation, cfg=cfg3)
    assert m3["status"] == "ok"
    assert m3["metrics"]["E3_policy_flips_per_entity_mean"] == pytest.approx(0.0, abs=0.0)
    assert m3["metrics"]["E3_policy_churn_rate_mean"] == pytest.approx(0.0, abs=0.0)
