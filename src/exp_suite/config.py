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
    decision_lag_seconds: float = Field(
        default=0.0,
        ge=0.0,
        description="Lag added after the last receipt_time in a timepoint before emitting a decision opportunity.",
    )
    policy: Literal["always_wait", "always_act", "wait_on_conflict", "risk_threshold"] = Field(
        default="wait_on_conflict",
        description="Decision policy identifier (minimal ACT/WAIT policies for early scaffolding).",
    )

    # Cost model (preregistered; drives “correctness” via realized loss)
    cost_false_act: float = Field(
        default=5.0,
        ge=0.0,
        description="Loss if ACT is taken when truth indicates no intervention needed.",
    )
    cost_false_wait: float = Field(
        default=10.0,
        ge=0.0,
        description="Loss if WAIT is taken when truth indicates intervention was needed.",
    )
    cost_wait_per_second: float = Field(
        default=0.1,
        ge=0.0,
        description="Linear delay cost per second when choosing WAIT (waiting is not free).",
    )
    correctness_epsilon: float = Field(
        default=0.0,
        ge=0.0,
        description="Treat actions within epsilon of the minimum loss as correct.",
    )

    # Overhead / conflict budget measurement knobs (preregistered thresholds)
    overhead_quantile: float = Field(
        default=0.95,
        ge=0.0,
        le=1.0,
        description="Quantile used for conflict budget thresholds (e.g., 0.95 for p95).",
    )
    overhead_max_state_bytes: int = Field(
        default=5000,
        ge=0,
        description="Max allowable state representation bytes (per decision point) at overhead_quantile.",
    )
    overhead_max_stateview_ms: float = Field(
        default=2.0,
        ge=0.0,
        description="Max allowable state-view construction time in ms (per decision point) at overhead_quantile.",
    )
    overhead_sample_limit: int = Field(
        default=1000,
        ge=1,
        description="Max number of decision points to sample for overhead measurement per run (deterministic sampling).",
    )

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


class WaitCostModel(BaseModel):
    """Cost model for choosing WAIT as a function of realized wait duration (seconds)."""

    family: Literal["linear", "quadratic", "exponential"] = Field(..., description="Wait-cost function family.")
    params: dict[str, float] = Field(default_factory=dict, description="Family parameters.")

    def cost(self, wait_seconds: float) -> float:
        t = max(0.0, float(wait_seconds))
        fam = self.family
        p = self.params or {}
        if fam == "linear":
            per_s = float(p.get("per_second", 0.0))
            return per_s * t
        if fam == "quadratic":
            k = float(p.get("k", 0.0))
            return k * (t**2)
        if fam == "exponential":
            k = float(p.get("k", 0.0))
            alpha = float(p.get("alpha", 0.0))
            # k * (exp(alpha * t) - 1), stable for alpha=0
            return k * ((float(__import__("math").exp(alpha * t))) - 1.0) if alpha != 0.0 else 0.0
        raise ValueError(f"Unsupported wait cost family: {fam}")


class Exp2Config(BaseModel):
    """Experiment 2: Cost-Aware Decision Policies (reuses Exp1 evidence streams + semantics)."""

    kind: Literal["exp2"] = "exp2"
    phase: Literal["dev", "eval"] = Field(
        default="dev",
        description="DEV for mechanics; EVAL for outcome measurement with locked configs.",
    )
    experiment_id: str = Field(..., min_length=1)
    system: Literal["baseline_a", "baseline_b", "proposed"]
    notes: str | None = None
    variant: str | None = Field(
        default=None,
        description="Optional label for sweep grouping (e.g., policy id) without changing state semantics.",
    )

    # Workload knobs (intentionally aligned with Exp1 to allow shared evidence streams)
    entity_count: PositiveInt = Field(..., description="Number of entities in the synthetic workload.")
    source_count: PositiveInt = Field(..., description="Number of sources producing observations.")
    events_per_entity: PositiveInt = Field(..., description="Number of events per entity (synthetic stream length).")

    conflict_rate: float = Field(..., ge=0.0, le=1.0, description="Probability of disagreement across sources.")
    missingness: float = Field(..., ge=0.0, le=1.0, description="Probability an observation is missing.")
    delay: DelayModel = Field(..., description="Receipt-time delay model for evidence.")
    decision_lag_seconds: float = Field(
        default=0.0,
        ge=0.0,
        description="Lag added after the last receipt_time in a timepoint before emitting a decision opportunity.",
    )

    # Policies are the primary axis for Exp2.
    policy: Literal["always_wait", "always_act", "wait_on_conflict", "risk_threshold"] = Field(
        default="wait_on_conflict",
        description="Decision policy identifier (Exp2 varies policy definitions).",
    )

    # Outcome-dependent losses (classification component)
    cost_false_act: float = Field(default=5.0, ge=0.0, description="Loss if ACT is taken when truth indicates ok.")
    cost_false_wait: float = Field(default=10.0, ge=0.0, description="Loss if WAIT is taken when truth indicates needs_act.")

    # WAIT delay cost curvature (the key Exp2 axis)
    wait_cost: WaitCostModel = Field(
        default_factory=lambda: WaitCostModel(family="linear", params={"per_second": 0.1}),
        description="Cost incurred when choosing WAIT as a function of wait duration.",
    )

    # Reconciliation (late truth) timing knobs (shared interpretation with Exp1)
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
    Union[StubConfig, Exp1Config, Exp2Config],
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


