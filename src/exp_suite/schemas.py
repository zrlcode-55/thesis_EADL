from __future__ import annotations

import pyarrow as pa


def event_schema() -> pa.Schema:
    return pa.schema(
        [
            pa.field("entity_id", pa.string(), nullable=False),
            pa.field("source_id", pa.string(), nullable=False),
            pa.field("event_time", pa.timestamp("us"), nullable=False),
            pa.field("receipt_time", pa.timestamp("us"), nullable=False),
            pa.field("payload_json", pa.string(), nullable=False),
            pa.field("event_id", pa.string(), nullable=False),
        ]
    )


def decision_schema() -> pa.Schema:
    return pa.schema(
        [
            pa.field("decision_time", pa.timestamp("us"), nullable=False),
            pa.field("action_id", pa.string(), nullable=False),
            pa.field("evidence_set_id", pa.string(), nullable=False),
            pa.field("confidence", pa.float64(), nullable=True),
            pa.field("expected_cost", pa.float64(), nullable=True),
            pa.field("policy_id", pa.string(), nullable=False),
        ]
    )


def reconciliation_schema() -> pa.Schema:
    return pa.schema(
        [
            pa.field("entity_id", pa.string(), nullable=False),
            pa.field("truth_window_start", pa.timestamp("us"), nullable=False),
            pa.field("truth_window_end", pa.timestamp("us"), nullable=False),
            pa.field("authoritative_outcome_json", pa.string(), nullable=False),
            pa.field("arrival_time", pa.timestamp("us"), nullable=False),
        ]
    )


