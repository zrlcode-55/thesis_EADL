from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field


class ExperimentConfig(BaseModel):
    """Top-level experiment configuration.

    Intentionally minimal: enough to validate + appear in manifests before we add semantics.
    """

    experiment_id: str = Field(..., min_length=1, description="Human-readable experiment identifier.")
    system: Literal["baseline_a", "baseline_b", "proposed"] = Field(
        ...,
        description="Which system semantics to run (placeholder selection for now).",
    )
    notes: str | None = Field(default=None, description="Optional free-form notes (pre-execution).")

    # Future: workload params, delay distributions, conflict/missingness knobs, etc.
    params: dict[str, Any] = Field(default_factory=dict, description="Free-form parameters (typed later).")


def load_config_toml(path: Path) -> ExperimentConfig:
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    if path.suffix.lower() not in {".toml"}:
        raise ValueError("Config must be a .toml file (uses Python 3.12 built-in tomllib).")

    data = tomllib.loads(path.read_text(encoding="utf-8"))
    return ExperimentConfig.model_validate(data)


