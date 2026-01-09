from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Literal

import numpy as np
import pandas as pd
import pyarrow as pa

from exp_suite.config import Exp1Config
from exp_suite.schemas import decision_schema, evidence_set_schema
from exp_suite.state_view import parse_evidence_json, state_view_from_evidence


PolicyId = Literal["always_wait", "always_act", "wait_on_conflict", "risk_threshold"]


@dataclass(frozen=True)
class DecisionArtifacts:
    decisions: pa.Table
    evidence_sets: pa.Table


def _evidence_set_id(*parts: Any) -> str:
    h = hashlib.sha1()
    for p in parts:
        h.update(str(p).encode("utf-8"))
        h.update(b"|")
    return h.hexdigest()


def _extract_timepoint_evidence(events_df: pd.DataFrame) -> pd.DataFrame:
    """Parse payload_json into columns we need for decision opportunities."""
    parsed = events_df["payload_json"].map(json.loads)
    df = events_df.copy()
    df["t_idx"] = parsed.map(lambda p: int(p.get("t_idx")))
    df["value"] = parsed.map(lambda p: p.get("value"))
    df["truth_proxy"] = parsed.map(lambda p: p.get("truth_proxy"))
    return df


def generate_exp1_decisions(
    events: pa.Table,
    cfg: Exp1Config,
    *,
    seed: int,
    policy: PolicyId = "wait_on_conflict",
) -> DecisionArtifacts:
    """Generate DecisionRecord + referenced evidence sets.

    Discipline for Snippet 5:
    - Decision opportunity = every (entity_id, t_idx) timepoint.
    - Decision time = max receipt_time within that (entity_id, t_idx) + decision_lag_seconds.
      This ensures the decision is based on evidence that has arrived, not on event time.
    - Action space is minimal: "ACT" or "WAIT".
    - Evidence sets are persisted (evidence_sets.parquet) and referenced by ID.
    """
    if events.num_rows == 0:
        empty_decisions = pa.Table.from_arrays(
            [pa.array([], type=f.type) for f in decision_schema()], schema=decision_schema()
        )
        empty_sets = pa.Table.from_arrays(
            [pa.array([], type=f.type) for f in evidence_set_schema()], schema=evidence_set_schema()
        )
        return DecisionArtifacts(decisions=empty_decisions, evidence_sets=empty_sets)

    rng = np.random.default_rng(seed + 20_000)

    df = _extract_timepoint_evidence(events.to_pandas())
    g = df.groupby(["entity_id", "t_idx"], sort=False)

    # Decision time: after evidence has arrived for the timepoint
    decision_time = g["receipt_time"].max()
    decision_time = pd.to_datetime(decision_time, utc=False).astype("datetime64[us]")

    decision_lag = float(getattr(cfg, "decision_lag_seconds", 0.0))
    decision_time = decision_time + pd.to_timedelta(decision_lag, unit="s")

    decisions_rows: list[dict[str, Any]] = []
    set_rows: list[dict[str, Any]] = []

    for (entity_id, t_idx), sub in g:
        dt = decision_time.loc[(entity_id, t_idx)]

        # Evidence available at decision time (by receipt_time)
        available = sub[sub["receipt_time"] <= dt]

        # Canonical evidence representation (sorted, minimal fields)
        ev_items = (
            available[["source_id", "event_time", "receipt_time", "value"]]
            .sort_values(["receipt_time", "source_id"], kind="mergesort")
            .assign(receipt_time=lambda x: pd.to_datetime(x["receipt_time"], utc=False).astype("datetime64[us]"))
            .assign(event_time=lambda x: pd.to_datetime(x["event_time"], utc=False).astype("datetime64[us]"))
        )

        ev_list = [
            {
                "source_id": str(r.source_id),
                "event_time": pd.Timestamp(r.event_time).isoformat(),
                "receipt_time": pd.Timestamp(r.receipt_time).isoformat(),
                "value": r.value,
            }
            for r in ev_items.itertuples(index=False)
        ]

        evid_id = _evidence_set_id("exp1", seed, entity_id, t_idx, json.dumps(ev_list, sort_keys=True))

        # Semantics-specific state view derived from the same evidence set.
        sv = state_view_from_evidence(
            semantics=cfg.system,
            evidence=parse_evidence_json(json.dumps(ev_list, separators=(",", ":"), sort_keys=True)),
        )

        confidence = None
        expected_cost = None

        if policy == "always_wait":
            action = "WAIT"
        elif policy == "always_act":
            action = "ACT"
        elif policy == "wait_on_conflict":
            action = "WAIT" if sv.conflict_size > 1 else "ACT"
        elif policy == "risk_threshold":
            # Expected-loss threshold rule:
            # p = proxy probability that outcome is needs_act, based on conflict size.
            # E[L(ACT)]  = (1 - p) * cost_false_act
            # E[L(WAIT)] = p * cost_false_wait + cost_wait_per_second * E[wait_seconds]
            # Choose ACT iff E[L(ACT)] <= E[L(WAIT)]

            # Proxy p: how much disagreement exists, normalized by max possible.
            denom = max(1, int(cfg.source_count) - 1)
            p = (max(0, sv.conflict_size - 1)) / denom
            p = float(min(1.0, max(0.0, p)))

            # E[wait_seconds]: reconciliation lag + expected jitter (non-negative)
            base_lag = float(getattr(cfg, "reconciliation_lag_seconds", 0.0))
            jitter = getattr(cfg, "reconciliation_jitter", None)
            exp_jitter = 0.0
            if jitter is not None:
                fam = getattr(jitter, "family", "fixed")
                params = getattr(jitter, "params", {}) or {}
                if fam == "fixed":
                    exp_jitter = float(params.get("seconds", 0.0))
                elif fam == "exponential":
                    exp_jitter = float(params.get("scale", 0.0))
                elif fam == "lognormal":
                    mu = float(params.get("mu", 0.0))
                    sigma = float(params.get("sigma", 0.0))
                    exp_jitter = float(np.exp(mu + 0.5 * (sigma**2)))
            e_wait_seconds = max(0.0, base_lag + exp_jitter)

            e_act = (1.0 - p) * float(cfg.cost_false_act)
            e_wait = (p * float(cfg.cost_false_wait)) + (float(cfg.cost_wait_per_second) * e_wait_seconds)

            action = "ACT" if e_act <= e_wait else "WAIT"
            confidence = p
            expected_cost = float(min(e_act, e_wait))
        else:
            raise ValueError(f"Unknown policy: {policy}")

        decisions_rows.append(
            {
                "decision_time": dt,
                "action_id": action,
                "evidence_set_id": evid_id,
                "confidence": confidence,
                "expected_cost": expected_cost,
                "policy_id": policy,
            }
        )
        set_rows.append(
            {
                "evidence_set_id": evid_id,
                "entity_id": entity_id,
                "t_idx": int(t_idx),
                "decision_time": dt,
                "evidence_json": json.dumps(ev_list, separators=(",", ":"), sort_keys=True),
            }
        )

    dec_df = pd.DataFrame(decisions_rows)
    set_df = pd.DataFrame(set_rows)

    # Stable ordering
    dec_df = dec_df.sort_values(["decision_time", "policy_id"], kind="mergesort").reset_index(drop=True)
    set_df = set_df.sort_values(["decision_time", "entity_id", "t_idx"], kind="mergesort").reset_index(drop=True)

    return DecisionArtifacts(
        decisions=pa.Table.from_pandas(dec_df, schema=decision_schema(), preserve_index=False),
        evidence_sets=pa.Table.from_pandas(set_df, schema=evidence_set_schema(), preserve_index=False),
    )


