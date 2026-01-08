from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Literal

import pandas as pd


Semantics = Literal["baseline_a", "baseline_b", "proposed"]


@dataclass
class StateSummary:
    total_events: int
    total_entities: int
    # how often we observed disagreement at a timepoint (based on payload field)
    conflict_timepoints: int
    # representation “width” (proxy for conflict set size)
    max_candidates: int
    avg_candidates: float


def summarize_state(events_df: pd.DataFrame, *, semantics: Semantics) -> StateSummary:
    """Summarize how a semantics would represent state under conflicts.

    This does NOT make decisions. It only characterizes representation width.

    Proxy definition (Snippet 4 discipline):
    - Group by (entity_id, t_idx).
    - Candidate set = unique observed `value` across sources at that timepoint.
    - Baseline A/B collapse to 1 candidate; Proposed keeps all candidates.
    """
    if events_df.empty:
        return StateSummary(0, 0, 0, 0, 0.0)

    parsed = events_df["payload_json"].map(json.loads)
    df = events_df.copy()
    df["t_idx"] = parsed.map(lambda p: p.get("t_idx"))
    df["value"] = parsed.map(lambda p: p.get("value"))
    df["conflict_moment"] = parsed.map(lambda p: bool(p.get("conflict_moment", False)))

    g = df.groupby(["entity_id", "t_idx"], sort=False)
    candidate_sizes = g["value"].nunique(dropna=True).astype(int)

    if semantics in ("baseline_a", "baseline_b"):
        effective_sizes = pd.Series(1, index=candidate_sizes.index)
    elif semantics == "proposed":
        effective_sizes = candidate_sizes
    else:
        raise ValueError(f"Unknown semantics: {semantics}")

    return StateSummary(
        total_events=int(len(df)),
        total_entities=int(df["entity_id"].nunique()),
        conflict_timepoints=int(g["conflict_moment"].max().sum()),
        max_candidates=int(effective_sizes.max()),
        avg_candidates=float(effective_sizes.mean()),
    )


