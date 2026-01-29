from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass
from typing import Any, Literal

import numpy as np
import pandas as pd
import pyarrow as pa

from exp_suite.config import Exp1Config, Exp2Config
from exp_suite.state_view import parse_evidence_json, state_view_from_evidence


Action = Literal["ACT", "WAIT"]


@dataclass(frozen=True)
class Exp1Metrics:
    decisions_total: int
    correctness_rate: float
    avg_loss: float
    avg_regret_vs_oracle: float


def _loss_for_action(
    *,
    action: Action,
    outcome: str,
    wait_seconds: float,
    cfg: Exp1Config,
) -> float:
    # Base classification losses
    if outcome == "ok":
        base = cfg.cost_false_act if action == "ACT" else 0.0
    elif outcome == "needs_act":
        base = cfg.cost_false_wait if action == "WAIT" else 0.0
    else:
        # Unknown outcome label: treat as unevaluable (NaN)
        return float("nan")

    # Waiting cost only applies if the chosen action is WAIT
    delay_cost = cfg.cost_wait_per_second * max(0.0, wait_seconds) if action == "WAIT" else 0.0
    return float(base + delay_cost)


def compute_exp1_metrics(
    *,
    decisions: pa.Table,
    evidence_sets: pa.Table,
    reconciliation: pa.Table,
    cfg: Exp1Config,
) -> dict[str, Any]:
    """Compute artifact-derived metrics for Exp1 (no results tuning).

    Correctness definition (decision-theoretic):
    - An action is correct if its realized loss is within epsilon of the minimum realized loss
      among {ACT, WAIT} under the observed outcome and waiting duration.
    """
    if decisions.num_rows == 0:
        return {
            "status": "no_decisions",
            "metrics": {},
        }

    dec = decisions.to_pandas()
    es = evidence_sets.to_pandas()
    rec = reconciliation.to_pandas()

    # Join decisions -> evidence_sets to recover entity_id/t_idx
    dec2 = dec.merge(es[["evidence_set_id", "entity_id", "t_idx"]], on="evidence_set_id", how="left")

    # Parse reconciliation outcome label from authoritative_outcome_json
    rec_parsed = rec["authoritative_outcome_json"].map(json.loads)
    rec2 = rec.copy()
    rec2["outcome"] = rec_parsed.map(lambda p: p.get("outcome"))
    rec2["truth_value"] = rec_parsed.map(lambda p: p.get("truth_value"))
    rec2["t_idx"] = rec_parsed.map(lambda p: int(p.get("t_idx")))

    # Join on (entity_id, t_idx)
    joined = dec2.merge(
        rec2[["entity_id", "t_idx", "arrival_time", "outcome"]],
        on=["entity_id", "t_idx"],
        how="left",
    )

    # Waiting duration is until reconciliation arrival (a conservative “labels arrive late” model).
    joined["wait_seconds"] = (
        (pd.to_datetime(joined["arrival_time"]) - pd.to_datetime(joined["decision_time"]))
        .dt.total_seconds()
        .clip(lower=0.0)
    )

    # Compute realized losses for the chosen action and for the oracle.
    losses = []
    regrets = []
    correct_flags = []

    for r in joined.itertuples(index=False):
        if pd.isna(r.outcome):
            losses.append(float("nan"))
            regrets.append(float("nan"))
            correct_flags.append(False)
            continue

        action: Action = r.action_id
        wait_s = float(r.wait_seconds) if not pd.isna(r.wait_seconds) else 0.0
        chosen = _loss_for_action(action=action, outcome=r.outcome, wait_seconds=wait_s, cfg=cfg)
        alt = _loss_for_action(action=("WAIT" if action == "ACT" else "ACT"), outcome=r.outcome, wait_seconds=wait_s, cfg=cfg)
        oracle = min(chosen, alt)
        regret = chosen - oracle

        correct = chosen <= oracle + float(cfg.correctness_epsilon)

        losses.append(chosen)
        regrets.append(regret)
        correct_flags.append(bool(correct))

    joined["loss"] = losses
    joined["regret_vs_oracle"] = regrets
    joined["correct"] = correct_flags

    # Aggregate (episode/run-level)
    valid = joined[~pd.isna(joined["loss"])]
    total = int(len(joined))
    correctness_rate = float(valid["correct"].mean()) if len(valid) else 0.0
    avg_loss = float(valid["loss"].mean()) if len(valid) else float("nan")
    avg_regret = float(valid["regret_vs_oracle"].mean()) if len(valid) else float("nan")

    em = Exp1Metrics(
        decisions_total=total,
        correctness_rate=correctness_rate,
        avg_loss=avg_loss,
        avg_regret_vs_oracle=avg_regret,
    )

    # --- Overhead / conflict budget (M7–M9) ---
    # Deterministic sampling to keep overhead measurement stable and bounded.
    sample_limit = int(getattr(cfg, "overhead_sample_limit", 1000))
    q = float(getattr(cfg, "overhead_quantile", 0.95))
    q = min(1.0, max(0.0, q))
    max_bytes = int(getattr(cfg, "overhead_max_state_bytes", 5000))
    max_ms = float(getattr(cfg, "overhead_max_stateview_ms", 2.0))

    es2 = es[["evidence_set_id", "evidence_json"]].copy()
    n_es = len(es2)
    if n_es > sample_limit:
        es2 = es2.sort_values("evidence_set_id", kind="mergesort").reset_index(drop=True)
        idx = np.linspace(0, n_es - 1, sample_limit, dtype=int)
        es2 = es2.iloc[idx].reset_index(drop=True)

    state_bytes = []
    state_ms = []
    conflict_sizes = []

    for row in es2.itertuples(index=False):
        evidence = parse_evidence_json(row.evidence_json)

        t0 = time.perf_counter()
        sv = state_view_from_evidence(semantics=cfg.system, evidence=evidence)
        dt_ms = (time.perf_counter() - t0) * 1000.0

        # Approximate state memory footprint (bytes):
        # container sizes + values (best-effort; deterministic).
        b = sys.getsizeof(sv) + sys.getsizeof(sv.candidates) + sys.getsizeof(sv.semantics) + sys.getsizeof(sv.conflict_size)
        for v in sv.candidates:
            b += sys.getsizeof(v)

        state_ms.append(float(dt_ms))
        state_bytes.append(int(b))
        conflict_sizes.append(int(sv.conflict_size))

    def _q(v: list[float], quant: float) -> float | None:
        if not v:
            return None
        return float(np.quantile(np.array(v, dtype=float), quant))

    m7_mean = float(np.mean(state_bytes)) if state_bytes else None
    m7_p = _q([float(x) for x in state_bytes], q)
    m7_max = int(max(state_bytes)) if state_bytes else None

    m8_mean = float(np.mean(state_ms)) if state_ms else None
    m8_p = _q(state_ms, q)
    m8_max = float(max(state_ms)) if state_ms else None

    # Conflict budget: largest conflict_size where both byte+ms quantiles are under thresholds.
    budget = None
    if conflict_sizes:
        df_over = pd.DataFrame({"k": conflict_sizes, "bytes": state_bytes, "ms": state_ms})
        ok_sizes = []
        for k, sub in df_over.groupby("k"):
            bq = float(np.quantile(sub["bytes"], q))
            tq = float(np.quantile(sub["ms"], q))
            if bq <= max_bytes and tq <= max_ms:
                ok_sizes.append(int(k))
        budget = max(ok_sizes) if ok_sizes else 0

    return {
        "status": "ok",
        "definitions": {
            "correctness": "Action is correct if its realized loss is within epsilon of the minimum loss among {ACT, WAIT}.",
            "loss_model": {
                "cost_false_act": cfg.cost_false_act,
                "cost_false_wait": cfg.cost_false_wait,
                "cost_wait_per_second": cfg.cost_wait_per_second,
                "epsilon": cfg.correctness_epsilon,
            },
            "overhead": {
                "sample_limit": sample_limit,
                "quantile": q,
                "thresholds": {
                    "max_state_bytes": max_bytes,
                    "max_stateview_ms": max_ms,
                },
                "note": "State bytes are an approximate Python object size proxy; ms is wall-clock on this host.",
            },
        },
        "metrics": {
            "M1_correctness_rate": em.correctness_rate,
            "M3_avg_loss": em.avg_loss,
            "M3b_avg_regret_vs_oracle": em.avg_regret_vs_oracle,
            "decisions_total": em.decisions_total,
            "M7_state_bytes_mean": m7_mean,
            f"M7_state_bytes_q{int(q*100)}": m7_p,
            "M7_state_bytes_max": m7_max,
            "M8_stateview_ms_mean": m8_mean,
            f"M8_stateview_ms_q{int(q*100)}": m8_p,
            "M8_stateview_ms_max": m8_max,
            "M9_conflict_budget_size": budget,
            "M8_sampled_decision_points": int(len(es2)),
        },
    }


def _loss_for_action_exp2(
    *,
    action: Action,
    outcome: str,
    wait_seconds: float,
    cfg: Exp2Config,
) -> float:
    # Base classification losses
    if outcome == "ok":
        base = cfg.cost_false_act if action == "ACT" else 0.0
    elif outcome == "needs_act":
        base = cfg.cost_false_wait if action == "WAIT" else 0.0
    else:
        return float("nan")

    delay_cost = cfg.wait_cost.cost(wait_seconds) if action == "WAIT" else 0.0
    return float(base + delay_cost)


def compute_exp2_metrics(
    *,
    decisions: pa.Table,
    evidence_sets: pa.Table,
    reconciliation: pa.Table,
    cfg: Exp2Config,
) -> dict[str, Any]:
    """Compute artifact-derived metrics for Exp2 (cost-aware timing policies).

    Exp2 focuses on cost aggregates + tail behavior + induced delay:
    - total/avg cost
    - tail costs (p95/p99)
    - deferral rate (WAIT fraction)
    - waiting time distributions
    """
    if decisions.num_rows == 0:
        return {
            "status": "no_decisions",
            "metrics": {},
        }

    dec = decisions.to_pandas()
    es = evidence_sets.to_pandas()
    rec = reconciliation.to_pandas()

    dec2 = dec.merge(es[["evidence_set_id", "entity_id", "t_idx"]], on="evidence_set_id", how="left")

    rec_parsed = rec["authoritative_outcome_json"].map(json.loads)
    rec2 = rec.copy()
    rec2["outcome"] = rec_parsed.map(lambda p: p.get("outcome"))
    rec2["t_idx"] = rec_parsed.map(lambda p: int(p.get("t_idx")))

    joined = dec2.merge(
        rec2[["entity_id", "t_idx", "arrival_time", "outcome"]],
        on=["entity_id", "t_idx"],
        how="left",
    )

    joined["wait_seconds"] = (
        (pd.to_datetime(joined["arrival_time"]) - pd.to_datetime(joined["decision_time"]))
        .dt.total_seconds()
        .clip(lower=0.0)
    )

    losses: list[float] = []
    regrets: list[float] = []
    correct_flags: list[bool] = []
    for r in joined.itertuples(index=False):
        if pd.isna(r.outcome):
            losses.append(float("nan"))
            regrets.append(float("nan"))
            correct_flags.append(False)
            continue
        action: Action = r.action_id
        wait_s = float(r.wait_seconds) if not pd.isna(r.wait_seconds) else 0.0
        chosen = _loss_for_action_exp2(action=action, outcome=r.outcome, wait_seconds=wait_s, cfg=cfg)
        alt = _loss_for_action_exp2(
            action=("WAIT" if action == "ACT" else "ACT"),
            outcome=r.outcome,
            wait_seconds=wait_s,
            cfg=cfg,
        )
        oracle = min(chosen, alt)
        regret = chosen - oracle

        eps = float(getattr(cfg, "correctness_epsilon", 0.0))
        correct = chosen <= oracle + eps

        losses.append(chosen)
        regrets.append(regret)
        correct_flags.append(bool(correct))

    joined["loss"] = losses
    joined["regret_vs_oracle"] = regrets
    joined["correct"] = correct_flags

    valid = joined[~pd.isna(joined["loss"])].copy()
    total_decisions = int(len(joined))
    n_valid = int(len(valid))
    if n_valid == 0:
        return {
            "status": "no_labeled_decisions",
            "definitions": {"note": "No reconciliation labels joined to decisions."},
            "metrics": {"decisions_total": total_decisions},
        }

    # Deferral (WAIT) rate is computed over labeled decisions.
    valid["is_wait"] = valid["action_id"].astype(str).eq("WAIT")

    total_cost = float(valid["loss"].sum())
    avg_cost = float(valid["loss"].mean())
    p95_cost = float(np.quantile(valid["loss"].to_numpy(dtype=float), 0.95))
    p99_cost = float(np.quantile(valid["loss"].to_numpy(dtype=float), 0.99))

    deferral_rate = float(valid["is_wait"].mean())
    mean_wait_all = float(valid["wait_seconds"].mean())
    mean_wait_when_wait = float(valid.loc[valid["is_wait"], "wait_seconds"].mean()) if valid["is_wait"].any() else 0.0
    correctness_rate = float(valid["correct"].mean()) if len(valid) else 0.0
    avg_regret = float(valid["regret_vs_oracle"].mean()) if len(valid) else float("nan")

    return {
        "status": "ok",
        "definitions": {
            "loss_model": {
                "cost_false_act": cfg.cost_false_act,
                "cost_false_wait": cfg.cost_false_wait,
                "wait_cost": {"family": cfg.wait_cost.family, "params": dict(cfg.wait_cost.params)},
            },
            "induced_delay": "wait_seconds = reconciliation_arrival_time - decision_time (clipped at 0).",
            "correctness": (
                "Action is correct if its realized loss is within epsilon of the minimum realized loss among {ACT, WAIT} "
                "under the observed outcome and realized wait duration."
            ),
        },
        "metrics": {
            "decisions_total": total_decisions,
            "decisions_labeled": n_valid,
            "M3_total_cost": total_cost,
            "M3_avg_cost": avg_cost,
            "M1_correctness_rate": correctness_rate,
            "M3b_avg_regret_vs_oracle": avg_regret,
            "M4_p95_cost": p95_cost,
            "M4_p99_cost": p99_cost,
            "M5_deferral_rate": deferral_rate,
            "M2_mean_wait_seconds": mean_wait_all,
            "M2_mean_wait_seconds_when_wait": mean_wait_when_wait,
        },
    }


