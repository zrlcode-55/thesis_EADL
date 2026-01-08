from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Iterable, Literal


Semantics = Literal["baseline_a", "baseline_b", "proposed"]


@dataclass(frozen=True)
class EvidenceItem:
    source_id: str
    receipt_time: str  # ISO string
    value: Any


@dataclass(frozen=True)
class StateView:
    """What the policy is allowed to see at a decision point."""

    semantics: Semantics
    conflict_size: int  # number of candidates represented
    candidates: tuple[Any, ...]  # optional; stable ordering


def parse_evidence_json(evidence_json: str) -> list[EvidenceItem]:
    raw = json.loads(evidence_json)
    return [
        EvidenceItem(
            source_id=str(r.get("source_id")),
            receipt_time=str(r.get("receipt_time")),
            value=r.get("value"),
        )
        for r in raw
    ]


def state_view_from_evidence(
    *,
    semantics: Semantics,
    evidence: Iterable[EvidenceItem],
) -> StateView:
    """Map raw evidence into a semantics-specific representation.

    Baseline A: overwrite to a single candidate (take the last item by receipt_time ordering).
    Baseline B: last-writer-wins by receipt_time (same as A here, but kept distinct for extension).
    Proposed: preserve all unique candidates observed.

    Note: this is intentionally minimal; future snippets can make A vs B diverge.
    """
    ev = list(evidence)
    if not ev:
        return StateView(semantics=semantics, conflict_size=0, candidates=())

    # Stable order by receipt_time then source_id for deterministic selection
    ev_sorted = sorted(ev, key=lambda x: (x.receipt_time, x.source_id))

    if semantics in ("baseline_a", "baseline_b"):
        chosen = ev_sorted[-1].value
        return StateView(semantics=semantics, conflict_size=1, candidates=(chosen,))

    if semantics == "proposed":
        # Preserve all unique values, deterministically ordered by first appearance in ev_sorted.
        seen = []
        for item in ev_sorted:
            if item.value not in seen:
                seen.append(item.value)
        return StateView(semantics=semantics, conflict_size=len(seen), candidates=tuple(seen))

    raise ValueError(f"Unknown semantics: {semantics}")


