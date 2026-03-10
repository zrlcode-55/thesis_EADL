from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, Field, PositiveInt, TypeAdapter


class DelayModel(BaseModel):
    """Receipt-time delay model for evidence (event_time -> receipt_time)."""

    family: Literal["fixed", "exponential", "lognormal"]
    params: dict[str, float] = Field(default_factory=dict)


class StubConfig(BaseModel):
    """Minimal config used to validate the artifact + manifest contract."""

    kind: Literal["stub"] = "stub"
    phase: Literal["dev", "eval"] = "dev"
    experiment_id: str = Field(..., min_length=1)
    system: Literal["baseline_a", "baseline_b", "proposed"]
    notes: str | None = None
    params: dict[str, Any] = Field(default_factory=dict)


class Exp1Config(BaseModel):
    """Experiment 1: Conflict & Delay Correctness."""

    kind: Literal["exp1"] = "exp1"
    phase: Literal["dev", "eval"] = "dev"
    experiment_id: str = Field(..., min_length=1)
    system: Literal["baseline_a", "baseline_b", "proposed"]
    notes: str | None = None

    entity_count: PositiveInt
    source_count: PositiveInt
    events_per_entity: PositiveInt

    conflict_rate: float = Field(..., ge=0.0, le=1.0)
    missingness: float = Field(..., ge=0.0, le=1.0)
    delay: DelayModel
    decision_lag_seconds: float = Field(default=0.0, ge=0.0)
    policy: Literal["always_wait", "always_act", "wait_on_conflict", "risk_threshold"] = "wait_on_conflict"

    cost_false_act: float = Field(default=5.0, ge=0.0)
    cost_false_wait: float = Field(default=10.0, ge=0.0)
    cost_wait_per_second: float = Field(default=0.1, ge=0.0)
    correctness_epsilon: float = Field(default=0.0, ge=0.0)

    overhead_quantile: float = Field(default=0.95, ge=0.0, le=1.0)
    overhead_max_state_bytes: int = Field(default=5000, ge=0)
    overhead_max_stateview_ms: float = Field(default=2.0, ge=0.0)
    overhead_sample_limit: int = Field(default=1000, ge=1)

    reconciliation_lag_seconds: float = Field(default=30.0, ge=0.0)
    reconciliation_jitter: DelayModel = Field(
        default_factory=lambda: DelayModel(family="fixed", params={"seconds": 0.0})
    )


class WaitCostModel(BaseModel):
    """Cost model for choosing WAIT as a function of realized wait duration (seconds)."""

    family: Literal["linear", "quadratic", "exponential"]
    params: dict[str, float] = Field(default_factory=dict)

    def cost(self, wait_seconds: float) -> float:
        t = max(0.0, float(wait_seconds))
        fam = self.family
        p = self.params or {}
        if fam == "linear":
            return float(p.get("per_second", 0.0)) * t
        if fam == "quadratic":
            k = float(p.get("k", 0.0))
            return k * (t**2)
        if fam == "exponential":
            k = float(p.get("k", 0.0))
            alpha = float(p.get("alpha", 0.0))
            return k * ((float(__import__("math").exp(alpha * t))) - 1.0) if alpha != 0.0 else 0.0
        raise ValueError(f"Unsupported wait cost family: {fam}")


class Exp2Config(BaseModel):
    """Experiment 2: Cost-Aware Decision Policies."""

    kind: Literal["exp2"] = "exp2"
    phase: Literal["dev", "eval"] = "dev"
    experiment_id: str = Field(..., min_length=1)
    system: Literal["baseline_a", "baseline_b", "proposed"]
    notes: str | None = None
    variant: str | None = None

    entity_count: PositiveInt
    source_count: PositiveInt
    events_per_entity: PositiveInt

    conflict_rate: float = Field(..., ge=0.0, le=1.0)
    missingness: float = Field(..., ge=0.0, le=1.0)
    delay: DelayModel
    decision_lag_seconds: float = Field(default=0.0, ge=0.0)
    policy: Literal["always_wait", "always_act", "wait_on_conflict", "risk_threshold"] = "wait_on_conflict"

    cost_false_act: float = Field(default=5.0, ge=0.0)
    cost_false_wait: float = Field(default=10.0, ge=0.0)
    correctness_epsilon: float = Field(default=0.0, ge=0.0)

    wait_cost: WaitCostModel = Field(
        default_factory=lambda: WaitCostModel(family="linear", params={"per_second": 0.1})
    )

    reconciliation_lag_seconds: float = Field(default=30.0, ge=0.0)
    reconciliation_jitter: DelayModel = Field(
        default_factory=lambda: DelayModel(family="fixed", params={"seconds": 0.0})
    )


class ShockModel(BaseModel):
    """Time-varying cost multiplier applied over a normalized episode in [0,1]."""

    shape: Literal["identity", "step", "impulse", "ramp"] = "identity"
    magnitude: float = Field(default=1.0, ge=0.0)
    start_frac: float = Field(default=0.0, ge=0.0, le=1.0)
    duration_frac: float = Field(default=0.2, ge=0.0, le=1.0)
    apply_to: list[Literal["cost_false_act", "cost_false_wait", "wait_cost"]] = Field(
        default_factory=lambda: ["cost_false_act", "cost_false_wait", "wait_cost"]
    )


class Exp3Config(Exp2Config):
    """Experiment 3: Exogenous Shock Stress Test.

    Reuses Exp2 apparatus and introduces a time-varying shock schedule over cost parameters.
    Semantics and evidence generation are expected to match the inherited Exp2 config exactly.
    """

    kind: Literal["exp3"] = "exp3"
    shock: ShockModel = Field(default_factory=ShockModel)
    inherits_from_exp2_config_path: str | None = None
    inherits_from_exp2_config_sha256: str | None = None
    enforce_inheritance: bool = False


ExperimentConfig = Annotated[
    Union[StubConfig, Exp1Config, Exp2Config, Exp3Config],
    Field(discriminator="kind"),
]

def load_config_toml(path: Path) -> ExperimentConfig:
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    if path.suffix.lower() not in {".toml"}:
        raise ValueError("Config must be a .toml file.")

    data = tomllib.loads(path.read_text(encoding="utf-8"))
    if "kind" not in data:
        data["kind"] = "stub"
    return TypeAdapter(ExperimentConfig).validate_python(data)
