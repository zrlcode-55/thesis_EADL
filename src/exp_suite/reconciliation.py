from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd
import pyarrow as pa

from exp_suite.config import DelayModel, Exp1Config
from exp_suite.schemas import reconciliation_schema
from exp_suite.workload import _sample_delay_seconds


def generate_exp1_reconciliation(
    events: pa.Table,
    cfg: Exp1Config,
    *,
    seed: int,
) -> pa.Table:
    """Generate late-truth reconciliation signals aligned to the generated events stream.

    Discipline for Snippet 3:
    - Truth is derived from the generator’s own latent `truth_proxy` embedded in `payload_json`.
    - One reconciliation signal per (entity_id, t_idx) timepoint.
    - Truth window is a 1-second interval starting at the underlying event_time.
    - Arrival time = truth_window_end + reconciliation_lag_seconds + jitter (non-negative).
    """
    if events.num_rows == 0:
        return pa.Table.from_arrays(
            [pa.array([], type=f.type) for f in reconciliation_schema()], schema=reconciliation_schema()
        )

    df = events.to_pandas()
    # Parse out truth_proxy + t_idx from payload_json.
    parsed = df["payload_json"].map(json.loads)
    df["truth_proxy"] = parsed.map(lambda p: p.get("truth_proxy"))
    df["t_idx"] = parsed.map(lambda p: p.get("t_idx"))

    # Deduplicate to one truth per (entity_id, t_idx)
    g = (
        df[["entity_id", "t_idx", "event_time", "truth_proxy"]]
        .sort_values(["entity_id", "t_idx", "event_time"], kind="mergesort")
        .drop_duplicates(subset=["entity_id", "t_idx"], keep="first")
        .reset_index(drop=True)
    )

    # Define truth windows as [event_time, event_time + 1s)
    g["truth_window_start"] = pd.to_datetime(g["event_time"], utc=False)
    g["truth_window_end"] = g["truth_window_start"] + pd.to_timedelta(1, unit="s")

    rng = np.random.default_rng(seed + 10_000)  # deterministic, but separated from evidence RNG
    jitter = _sample_delay_seconds(rng, cfg.reconciliation_jitter, len(g))
    base_lag = float(cfg.reconciliation_lag_seconds)
    arrival = g["truth_window_end"] + pd.to_timedelta(base_lag + jitter, unit="s")

    def outcome_json(row: pd.Series) -> str:
        truth_value = row["truth_proxy"]
        label = "needs_act" if truth_value not in (0, 0.0, None) else "ok"
        out: dict[str, Any] = {
            "outcome": label,
            "truth_value": truth_value,
            "t_idx": int(row["t_idx"]),
        }
        return json.dumps(out, separators=(",", ":"), sort_keys=True)

    out_df = pd.DataFrame(
        {
            "entity_id": g["entity_id"].astype(str),
            "truth_window_start": g["truth_window_start"],
            "truth_window_end": g["truth_window_end"],
            "authoritative_outcome_json": g.apply(outcome_json, axis=1),
            "arrival_time": arrival,
        }
    )

    # Coerce to microsecond resolution to match schema (timestamp[us])
    for col in ["truth_window_start", "truth_window_end", "arrival_time"]:
        out_df[col] = pd.to_datetime(out_df[col], utc=False).astype("datetime64[us]")

    # Stable ordering
    out_df = out_df.sort_values(["arrival_time", "entity_id"], kind="mergesort").reset_index(drop=True)

    return pa.Table.from_pandas(out_df, schema=reconciliation_schema(), preserve_index=False)


