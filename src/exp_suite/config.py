from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, Field, PositiveInt, TypeAdapter


class DelayModel(BaseModel):
    """Receipt-time delay model for evidence (event_time -> receipt_time)."""

    family: Literal["fixed", "exponential", "lognormal"] = Field(
        ...,
        description="Delay distribution family.",
    )
    params: dict[str, float] = Field(
        default_factory=dict,
        description="Family parameters (typed later; preregistered in configs).",
    )


class StubConfig(BaseModel):
    """Minimal config used to validate the artifact + manifest contract."""

    kind: Literal["stub"] = "stub"
    phase: Literal["dev", "eval"] = Field(
        default="dev",
        description="DEV for mechanics; EVAL for outcome measurement with locked configs.",
    )
    experiment_id: str = Field(..., min_length=1, description="Human-readable experiment identifier.")
    system: Literal["baseline_a", "baseline_b", "proposed"] = Field(
        ...,
        description="Which system semantics to run (placeholder selection for now).",
    )
    notes: str | None = Field(default=None, description="Optional free-form notes (pre-execution).")
    params: dict[str, Any] = Field(default_factory=dict, description="Free-form parameters (typed later).")


class Exp1Config(BaseModel):
    """Experiment 1: Conflict & Delay Correctness (typed, preregisterable knobs)."""

    kind: Literal["exp1"] = "exp1"
    phase: Literal["dev", "eval"] = Field(
        default="dev",
        description="DEV for mechanics; EVAL for outcome measurement with locked configs.",
    )
    experiment_id: str = Field(..., min_length=1)
    system: Literal["baseline_a", "baseline_b", "proposed"]
    notes: str | None = None

    # Minimal workload knobs (kept small; extend in later snippets).
    entity_count: PositiveInt = Field(..., description="Number of entities in the synthetic workload.")
    source_count: PositiveInt = Field(..., description="Number of sources producing observations.")
    events_per_entity: PositiveInt = Field(..., description="Number of events per entity (synthetic stream length).")

    conflict_rate: float = Field(..., ge=0.0, le=1.0, description="Probability of disagreement across sources.")
    missingness: float = Field(..., ge=0.0, le=1.0, description="Probability an observation is missing.")
    delay: DelayModel = Field(..., description="Receipt-time delay model for evidence.")

    # Reconciliation (late truth) timing knobs: kept simple and defaulted for Snippet 3.
    reconciliation_lag_seconds: float = Field(
        default=30.0,
        ge=0.0,
        description="Base lag between truth window end and reconciliation arrival.",
    )
    reconciliation_jitter: DelayModel = Field(
        default_factory=lambda: DelayModel(family="fixed", params={"seconds": 0.0}),
        description="Additional non-negative jitter added to reconciliation arrival.",
    )


ExperimentConfig = Annotated[
    Union[StubConfig, Exp1Config],
    Field(discriminator="kind"),
]

def load_config_toml(path: Path) -> ExperimentConfig:
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    if path.suffix.lower() not in {".toml"}:
        raise ValueError("Config must be a .toml file (uses Python 3.12 built-in tomllib).")

    data = tomllib.loads(path.read_text(encoding="utf-8"))
    # Back-compat: older stub configs may omit the discriminator.
    if "kind" not in data:
        data["kind"] = "stub"
    return TypeAdapter(ExperimentConfig).validate_python(data)


