from __future__ import annotations

import json
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class GridPoint:
    conflict_rate: float
    delay_sigma: float
    cost_false_act: float
    cost_wait_per_second: float

    def key(self) -> str:
        return (
            f"cr{_slug_float(self.conflict_rate)}__"
            f"sig{_slug_float(self.delay_sigma)}__"
            f"cfa{_slug_float(self.cost_false_act)}__"
            f"cws{_slug_float(self.cost_wait_per_second)}"
        )


def _slug_float(x: float) -> str:
    # 0.10 -> 0p10, 1.0 -> 1p00
    return f"{x:.2f}".replace(".", "p")


def _toml_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def _render_exp1_toml(data: dict[str, Any]) -> str:
    """Render a minimal TOML for Exp1Config (we avoid adding a TOML writer dependency)."""
    delay = data.pop("delay")
    recon_jitter = data.pop("reconciliation_jitter")

    lines: list[str] = []
    # Root scalars first (stable ordering)
    root_order = [
        "kind",
        "phase",
        "experiment_id",
        "system",
        "notes",
        "entity_count",
        "source_count",
        "events_per_entity",
        "conflict_rate",
        "missingness",
        "decision_lag_seconds",
        "policy",
        "reconciliation_lag_seconds",
        "cost_false_act",
        "cost_false_wait",
        "cost_wait_per_second",
        "correctness_epsilon",
        "overhead_quantile",
        "overhead_max_state_bytes",
        "overhead_max_stateview_ms",
        "overhead_sample_limit",
    ]
    for k in root_order:
        if k not in data:
            continue
        v = data[k]
        if v is None:
            continue
        if isinstance(v, str):
            lines.append(f'{k} = "{_toml_escape(v)}"')
        elif isinstance(v, bool):
            lines.append(f"{k} = {'true' if v else 'false'}")
        else:
            lines.append(f"{k} = {v}")

    # Delay table
    lines.append("")
    lines.append("[delay]")
    lines.append(f'family = "{_toml_escape(str(delay["family"]))}"')
    lines.append("[delay.params]")
    for pk, pv in delay.get("params", {}).items():
        lines.append(f"{pk} = {pv}")

    # Reconciliation jitter table
    lines.append("")
    lines.append("[reconciliation_jitter]")
    lines.append(f'family = "{_toml_escape(str(recon_jitter["family"]))}"')
    lines.append("[reconciliation_jitter.params]")
    for pk, pv in recon_jitter.get("params", {}).items():
        lines.append(f"{pk} = {pv}")

    lines.append("")
    return "\n".join(lines)


def load_base_exp1_config(path: Path) -> dict[str, Any]:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    if data.get("kind") != "exp1":
        raise ValueError(f"Expected exp1 config at: {path}")
    return data


def iter_grid_points(
    *,
    conflict_rates: Iterable[float],
    delay_sigmas: Iterable[float],
    cost_false_acts: Iterable[float],
    cost_wait_per_seconds: Iterable[float],
) -> list[GridPoint]:
    pts: list[GridPoint] = []
    for cr in conflict_rates:
        for sig in delay_sigmas:
            for cfa in cost_false_acts:
                for cws in cost_wait_per_seconds:
                    pts.append(
                        GridPoint(
                            conflict_rate=float(cr),
                            delay_sigma=float(sig),
                            cost_false_act=float(cfa),
                            cost_wait_per_second=float(cws),
                        )
                    )
    return pts


def generate_grid_configs(
    *,
    base_config_path: Path,
    out_dir: Path,
    experiment_id: str,
    systems: list[str],
    conflict_rates: list[float],
    delay_sigmas: list[float],
    cost_false_acts: list[float],
    cost_wait_per_seconds: list[float],
) -> list[Path]:
    base = load_base_exp1_config(base_config_path)

    out_dir.mkdir(parents=True, exist_ok=True)
    points = iter_grid_points(
        conflict_rates=conflict_rates,
        delay_sigmas=delay_sigmas,
        cost_false_acts=cost_false_acts,
        cost_wait_per_seconds=cost_wait_per_seconds,
    )

    written: list[Path] = []
    for p in points:
        for sys in systems:
            data = dict(base)
            data["phase"] = "eval"
            data["experiment_id"] = experiment_id
            data["system"] = sys
            data["notes"] = f"Locked grid point {p.key()} (do not edit)."

            # Vary preregistered regime axes
            data["conflict_rate"] = p.conflict_rate
            delay = dict(data["delay"])
            delay_params = dict(delay.get("params", {}))
            # Keep mu fixed; vary sigma.
            delay["family"] = "lognormal"
            delay_params.setdefault("mu", 0.0)
            delay_params["sigma"] = p.delay_sigma
            delay["params"] = delay_params
            data["delay"] = delay

            data["cost_false_act"] = p.cost_false_act
            data["cost_wait_per_second"] = p.cost_wait_per_second

            # Filename encodes the regime point + system
            fname = f"{experiment_id}__{p.key()}__{sys}.toml"
            # Guard: only safe characters
            fname = re.sub(r"[^A-Za-z0-9_.-]", "_", fname)
            path = out_dir / fname
            path.write_text(_render_exp1_toml(dict(data)), encoding="utf-8")
            written.append(path)

    return written


def summarize_grid_from_summaries(
    *,
    artifacts_dir: Path,
    sweep_prefix: str,
    out_json: Path,
    primary_metric: str = "M3b_avg_regret_vs_oracle",
    compare_against: tuple[str, ...] = ("baseline_a", "baseline_b"),
) -> dict[str, Any]:
    """Aggregate many sweep_summary.json files into a grid-level summary artifact.

    `sweep_prefix` is the sweep id prefix, e.g. "exp1_grid_v1__A".
    We look for directories under artifacts/ named: sweep_{sweep_id} where sweep_id startswith sweep_prefix.
    """
    rows: list[dict[str, Any]] = []

    for d in sorted(artifacts_dir.glob(f"sweep_{sweep_prefix}*")):
        summary_path = d / "sweep_summary.json"
        if not summary_path.exists():
            continue
        s = json.loads(summary_path.read_text(encoding="utf-8"))
        systems = s.get("systems", {})
        if "proposed" not in systems:
            continue

        def mean(sys: str, metric: str) -> float | None:
            try:
                return float(systems[sys]["metrics"][metric]["mean"])
            except Exception:
                return None

        proposed_primary = mean("proposed", primary_metric)
        if proposed_primary is None:
            continue

        row: dict[str, Any] = {
            "sweep_id": s.get("sweep_id"),
            "git_rev": s.get("git_rev"),
            "primary_metric": primary_metric,
            "proposed_mean": proposed_primary,
        }
        for b in compare_against:
            b_mean = mean(b, primary_metric)
            row[f"{b}_mean"] = b_mean
            row[f"delta_proposed_minus_{b}"] = None if b_mean is None else proposed_primary - b_mean
        rows.append(row)

    # Summarize wins/losses against baselines
    summary: dict[str, Any] = {
        "sweep_prefix": sweep_prefix,
        "primary_metric": primary_metric,
        "rows": rows,
        "counts": {},
    }
    for b in compare_against:
        deltas = [r.get(f"delta_proposed_minus_{b}") for r in rows if r.get(f"delta_proposed_minus_{b}") is not None]
        wins = sum(1 for x in deltas if float(x) < 0.0)  # lower regret is better
        losses = sum(1 for x in deltas if float(x) > 0.0)
        ties = sum(1 for x in deltas if float(x) == 0.0)
        summary["counts"][b] = {"n": len(deltas), "wins": wins, "losses": losses, "ties": ties}

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return summary


def group_grid_configs_by_point(config_dir: Path, *, experiment_id: str) -> dict[str, dict[str, Path]]:
    """Group grid configs by regime point key.

    Expects filenames like:
      {experiment_id}__{point_key}__{system}.toml

    Returns:
      {point_key: {system: path}}
    """
    groups: dict[str, dict[str, Path]] = {}
    for p in sorted(config_dir.glob(f"{experiment_id}__*__*.toml")):
        stem = p.stem
        parts = stem.split("__")
        if len(parts) < 3:
            continue
        # parts[0] is experiment_id, parts[-1] is system, middle join is point_key
        sys = parts[-1]
        point_key = "__".join(parts[1:-1])
        groups.setdefault(point_key, {})[sys] = p
    return groups


