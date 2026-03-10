from __future__ import annotations

from typing import Any

from exp_suite.config import ShockModel


def clamp01(x: float) -> float:
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    return float(x)


def shock_multiplier(shock: ShockModel, t_frac: float) -> float:
    """Compute shock multiplier m(t) for normalized t in [0,1]."""
    t = clamp01(float(t_frac))
    shape = shock.shape
    mag = float(shock.magnitude)
    if shape == "identity":
        return 1.0

    start = clamp01(float(shock.start_frac))
    dur = clamp01(float(shock.duration_frac))
    end = clamp01(start + dur) if dur > 0.0 else start

    if shape == "step":
        return mag if t >= start else 1.0
    if shape == "impulse":
        return mag if (t >= start and t <= end) else 1.0
    if shape == "ramp":
        if t <= start:
            return 1.0
        if t >= end:
            return mag
        # Linear interpolation from 1 -> mag over [start,end]
        span = max(1e-12, (end - start))
        alpha = (t - start) / span
        return (1.0 - alpha) * 1.0 + alpha * mag
    return 1.0


def shock_scales_for_components(shock: ShockModel, t_frac: float) -> dict[str, float]:
    """Return per-component scale factors (defaults to 1.0 when not targeted)."""
    m = shock_multiplier(shock, t_frac)
    apply = set(shock.apply_to or [])
    return {
        "cost_false_act": (m if "cost_false_act" in apply else 1.0),
        "cost_false_wait": (m if "cost_false_wait" in apply else 1.0),
        "wait_cost": (m if "wait_cost" in apply else 1.0),
    }


def normalized_time_from_t_idx(*, t_idx: int, events_per_entity: int | None) -> float:
    """Map an integer time index to [0,1] using events_per_entity when available."""
    if events_per_entity is None or int(events_per_entity) <= 1:
        return 0.0
    denom = max(1, int(events_per_entity) - 1)
    return clamp01(float(int(t_idx)) / float(denom))


def maybe_get_shock(cfg: Any) -> ShockModel | None:
    """Duck-typed access to cfg.shock for Exp3Config without importing Exp3Config here."""
    s = getattr(cfg, "shock", None)
    if isinstance(s, ShockModel):
        return s
    return None


