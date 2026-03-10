from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Iterable, Literal


Semantics = Literal["baseline_a", "baseline_b", "proposed"]


@dataclass(frozen=True)
class EvidenceItem:
    source_id: str
    event_time: str   # ISO string
    receipt_time: str # ISO string
    value: Any


@dataclass(frozen=True)
class StateView:
    """What the policy is allowed to see at a decision point."""

    semantics: Semantics
    conflict_size: int       # number of distinct candidates
    candidates: tuple[Any, ...]


def parse_evidence_json(evidence_json: str) -> list[EvidenceItem]:
    raw = json.loads(evidence_json)
    return [
        EvidenceItem(
            source_id=str(r.get("source_id")),
            event_time=str(r.get("event_time")),
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
    """Map raw evidence into a semantics-specific state representation.

    baseline_a: last value by event_time (source clock), collapses to one candidate.
    baseline_b: last value by receipt_time (arrival order), collapses to one candidate.
    proposed:   all unique values in receipt order — exposes conflict_size > 1 when sources disagree.
    """
    ev = list(evidence)
    if not ev:
        return StateView(semantics=semantics, conflict_size=0, candidates=())

    by_receipt = sorted(ev, key=lambda x: (x.receipt_time, x.source_id))
    by_event   = sorted(ev, key=lambda x: (x.event_time, x.source_id))

    if semantics == "baseline_a":
        chosen = by_event[-1].value
        return StateView(semantics=semantics, conflict_size=1, candidates=(chosen,))

    if semantics == "baseline_b":
        chosen = by_receipt[-1].value
        return StateView(semantics=semantics, conflict_size=1, candidates=(chosen,))

    if semantics == "proposed":
        seen: list[Any] = []
        for item in by_receipt:
            if item.value not in seen:
                seen.append(item.value)
        return StateView(semantics=semantics, conflict_size=len(seen), candidates=tuple(seen))

    raise ValueError(f"Unknown semantics: {semantics}")
