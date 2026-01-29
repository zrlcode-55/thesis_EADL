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


def _render_exp2_toml(data: dict[str, Any]) -> str:
    """Render a minimal TOML for Exp2Config (we avoid adding a TOML writer dependency)."""
    delay = data.pop("delay")
    recon_jitter = data.pop("reconciliation_jitter")
    wait_cost = data.pop("wait_cost")

    lines: list[str] = []
    root_order = [
        "kind",
        "phase",
        "experiment_id",
        "system",
        "variant",
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

    # wait_cost table
    lines.append("")
    lines.append("[wait_cost]")
    lines.append(f'family = "{_toml_escape(str(wait_cost["family"]))}"')
    lines.append("[wait_cost.params]")
    for pk, pv in (wait_cost.get("params", {}) or {}).items():
        lines.append(f"{pk} = {pv}")

    # Delay table
    lines.append("")
    lines.append("[delay]")
    lines.append(f'family = "{_toml_escape(str(delay["family"]))}"')
    lines.append("[delay.params]")
    for pk, pv in (delay.get("params", {}) or {}).items():
        lines.append(f"{pk} = {pv}")

    # Reconciliation jitter table
    lines.append("")
    lines.append("[reconciliation_jitter]")
    lines.append(f'family = "{_toml_escape(str(recon_jitter["family"]))}"')
    lines.append("[reconciliation_jitter.params]")
    for pk, pv in (recon_jitter.get("params", {}) or {}).items():
        lines.append(f"{pk} = {pv}")

    lines.append("")
    return "\n".join(lines)


def _render_exp3_toml(data: dict[str, Any]) -> str:
    """Render a minimal TOML for Exp3Config (we avoid adding a TOML writer dependency)."""
    delay = data.pop("delay")
    recon_jitter = data.pop("reconciliation_jitter")
    wait_cost = data.pop("wait_cost")
    shock = data.pop("shock")

    lines: list[str] = []
    root_order = [
        "kind",
        "phase",
        "experiment_id",
        "system",
        "variant",
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
        "correctness_epsilon",
        "inherits_from_exp2_config_path",
        "inherits_from_exp2_config_sha256",
        "enforce_inheritance",
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

    # wait_cost table
    lines.append("")
    lines.append("[wait_cost]")
    lines.append(f'family = "{_toml_escape(str(wait_cost["family"]))}"')
    lines.append("[wait_cost.params]")
    for pk, pv in (wait_cost.get("params", {}) or {}).items():
        lines.append(f"{pk} = {pv}")

    # shock table
    lines.append("")
    lines.append("[shock]")
    lines.append(f'shape = "{_toml_escape(str(shock.get("shape", "identity")))}"')
    lines.append(f"magnitude = {float(shock.get('magnitude', 1.0))}")
    lines.append(f"start_frac = {float(shock.get('start_frac', 0.0))}")
    lines.append(f"duration_frac = {float(shock.get('duration_frac', 0.2))}")
    # TOML array of strings
    apply_to = shock.get("apply_to", []) or []
    apply_to = [str(x) for x in apply_to]
    lines.append(f"apply_to = [{', '.join('\"' + _toml_escape(x) + '\"' for x in apply_to)}]")

    # Delay table
    lines.append("")
    lines.append("[delay]")
    lines.append(f'family = "{_toml_escape(str(delay["family"]))}"')
    lines.append("[delay.params]")
    for pk, pv in (delay.get("params", {}) or {}).items():
        lines.append(f"{pk} = {pv}")

    # Reconciliation jitter table
    lines.append("")
    lines.append("[reconciliation_jitter]")
    lines.append(f'family = "{_toml_escape(str(recon_jitter["family"]))}"')
    lines.append("[reconciliation_jitter.params]")
    for pk, pv in (recon_jitter.get("params", {}) or {}).items():
        lines.append(f"{pk} = {pv}")

    lines.append("")
    return "\n".join(lines)


def load_base_exp1_config(path: Path) -> dict[str, Any]:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    if data.get("kind") != "exp1":
        raise ValueError(f"Expected exp1 config at: {path}")
    return data


def load_base_exp2_config(path: Path) -> dict[str, Any]:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    if data.get("kind") != "exp2":
        raise ValueError(f"Expected exp2 config at: {path}")
    return data


def _slug_shape(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", (s or "unknown")).strip("_")


def _shock_key(shock: dict[str, Any]) -> str:
    shape = _slug_shape(str(shock.get("shape", "identity")))
    mag = float(shock.get("magnitude", 1.0))
    start = float(shock.get("start_frac", 0.0))
    dur = float(shock.get("duration_frac", 0.2))
    return f"shock_{shape}__m{_slug_float(mag)}__s{_slug_float(start)}__d{_slug_float(dur)}"


def generate_exp3_shock_sweep_configs(
    *,
    base_exp2_config_path: Path,
    out_dir: Path,
    experiment_id: str,
    fixed_system: str,
    policies: list[str],
    shock_models: list[dict[str, Any]],
    inherits_from_path: str | None = None,
    inherits_from_sha256: str | None = None,
    enforce_inheritance: bool = False,
) -> list[Path]:
    """Generate locked Exp3 configs where state semantics are fixed, policy varies, and shock varies across points.

    Output naming scheme:
      {experiment_id}__{shock_key}__{policy}.toml
    """
    base = load_base_exp2_config(base_exp2_config_path)
    out_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    for shock in shock_models:
        point_key = _shock_key(shock)
        for pol in policies:
            data = dict(base)
            data["kind"] = "exp3"
            data["phase"] = "eval"
            data["experiment_id"] = experiment_id
            data["system"] = fixed_system
            data["variant"] = pol
            data["policy"] = pol
            data["shock"] = dict(shock)
            data["notes"] = f"Locked exp3 shock sweep {point_key} / {pol} (do not edit)."
            if inherits_from_path is not None:
                data["inherits_from_exp2_config_path"] = str(inherits_from_path)
            if inherits_from_sha256 is not None:
                data["inherits_from_exp2_config_sha256"] = str(inherits_from_sha256)
            data["enforce_inheritance"] = bool(enforce_inheritance)

            fname = f"{experiment_id}__{point_key}__{pol}.toml"
            fname = re.sub(r"[^A-Za-z0-9_.-]", "_", fname)
            path = out_dir / fname
            path.write_text(_render_exp3_toml(dict(data)), encoding="utf-8")
            written.append(path)

    return written


def group_exp3_shock_configs_by_point(config_dir: Path, *, experiment_id: str) -> dict[str, dict[str, Path]]:
    """Group Exp3 shock configs into shock points.

    Expects filenames: {experiment_id}__{point_key}__{policy}.toml
    Returns: {point_key: {policy: path}}
    """
    groups: dict[str, dict[str, Path]] = {}
    for p in sorted(config_dir.glob(f"{experiment_id}__*__*.toml")):
        parts = p.stem.split("__")
        if len(parts) < 3:
            continue
        if parts[0] != experiment_id:
            continue
        point_key = "__".join(parts[1:-1])
        pol = parts[-1]
        groups.setdefault(point_key, {})[pol] = p
    return groups


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


def generate_exp2_grid_configs(
    *,
    base_config_path: Path,
    out_dir: Path,
    experiment_id: str,
    systems: list[str],
    conflict_rates: list[float],
    delay_sigmas: list[float],
    cost_false_acts: list[float],
    wait_cost_per_seconds: list[float],
) -> list[Path]:
    """Generate a preregistered regime grid of locked Exp2 eval configs.

    Exp2 differs from Exp1 primarily in the WAIT cost model (curvature). For grid_v1 we keep
    the same 54-point structure by varying a linear per-second coefficient.
    """
    base = load_base_exp2_config(base_config_path)

    out_dir.mkdir(parents=True, exist_ok=True)
    points = iter_grid_points(
        conflict_rates=conflict_rates,
        delay_sigmas=delay_sigmas,
        cost_false_acts=cost_false_acts,
        cost_wait_per_seconds=wait_cost_per_seconds,
    )

    written: list[Path] = []
    for p in points:
        for sys in systems:
            data = dict(base)
            data["phase"] = "eval"
            data["experiment_id"] = experiment_id
            data["system"] = sys
            data["notes"] = f"Locked exp2 grid point {p.key()} (do not edit)."

            # Vary preregistered regime axes
            data["conflict_rate"] = p.conflict_rate

            delay = dict(data["delay"])
            delay_params = dict(delay.get("params", {}))
            delay["family"] = "lognormal"
            delay_params.setdefault("mu", 0.0)
            delay_params["sigma"] = p.delay_sigma
            delay["params"] = delay_params
            data["delay"] = delay

            data["cost_false_act"] = p.cost_false_act

            # For grid_v1: keep family linear; vary per_second
            wc = dict(data.get("wait_cost", {"family": "linear", "params": {"per_second": 0.1}}))
            wc["family"] = "linear"
            wc_params = dict(wc.get("params", {}) or {})
            wc_params["per_second"] = p.cost_wait_per_second
            wc["params"] = wc_params
            data["wait_cost"] = wc

            fname = f"{experiment_id}__{p.key()}__{sys}.toml"
            fname = re.sub(r"[^A-Za-z0-9_.-]", "_", fname)
            path = out_dir / fname
            path.write_text(_render_exp2_toml(dict(data)), encoding="utf-8")
            written.append(path)

    return written


def _slug_kv(k: str, v: float) -> str:
    return f"{k}{_slug_float(float(v))}"


def _wait_cost_key(wait_cost: dict[str, Any]) -> str:
    fam = str(wait_cost.get("family", "")).strip()
    params = dict(wait_cost.get("params", {}) or {})
    if fam == "linear":
        return f"wc_linear__{_slug_kv('ps', float(params.get('per_second', 0.0)))}"
    if fam == "quadratic":
        return f"wc_quadratic__{_slug_kv('k', float(params.get('k', 0.0)))}"
    if fam == "exponential":
        return f"wc_exponential__{_slug_kv('k', float(params.get('k', 0.0)))}__{_slug_kv('a', float(params.get('alpha', 0.0)))}"
    # Fallback: stable-ish
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", fam or "unknown")
    return f"wc_{safe}"


def generate_exp2_policy_sweep_configs(
    *,
    base_config_path: Path,
    out_dir: Path,
    experiment_id: str,
    fixed_system: str,
    policies: list[str],
    wait_cost_models: list[dict[str, Any]],
) -> list[Path]:
    """Generate locked Exp2 configs where **state semantics are fixed** and **policy varies**.

    Output naming scheme:
      {experiment_id}__{wait_cost_key}__{policy}.toml

    Each file sets:
      - system = fixed_system
      - variant = policy   (so sweeps compare policies as "systems" in summaries)
      - policy = policy
      - wait_cost = one of wait_cost_models
    """
    base = load_base_exp2_config(base_config_path)
    out_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    for wc in wait_cost_models:
        point_key = _wait_cost_key(wc)
        for pol in policies:
            data = dict(base)
            data["phase"] = "eval"
            data["experiment_id"] = experiment_id
            data["system"] = fixed_system
            data["variant"] = pol
            data["policy"] = pol
            data["wait_cost"] = dict(wc)
            data["notes"] = f"Locked exp2 policy sweep {point_key} / {pol} (do not edit)."

            fname = f"{experiment_id}__{point_key}__{pol}.toml"
            fname = re.sub(r"[^A-Za-z0-9_.-]", "_", fname)
            path = out_dir / fname
            path.write_text(_render_exp2_toml(dict(data)), encoding="utf-8")
            written.append(path)

    return written


def group_exp2_policy_configs_by_point(config_dir: Path, *, experiment_id: str) -> dict[str, dict[str, Path]]:
    """Group Exp2 policy configs into regime points.

    Expects filenames: {experiment_id}__{point_key}__{policy}.toml
    Returns: {point_key: {policy: path}}
    """
    groups: dict[str, dict[str, Path]] = {}
    for p in sorted(config_dir.glob(f"{experiment_id}__*__*.toml")):
        parts = p.stem.split("__")
        if len(parts) < 3:
            continue
        if parts[0] != experiment_id:
            continue
        point_key = "__".join(parts[1:-1])
        pol = parts[-1]
        groups.setdefault(point_key, {})[pol] = p
    return groups


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


def summarize_grid_from_multiple_prefixes(
    *,
    artifacts_dir: Path,
    sweep_prefixes: list[str],
    out_json: Path,
    primary_metric: str = "M3b_avg_regret_vs_oracle",
    compare_against: tuple[str, ...] = ("baseline_a", "baseline_b"),
) -> dict[str, Any]:
    """Aggregate multiple sweep-id prefixes into one grid-level summary artifact.

    Useful when Seed Set A is run in multiple chunks / prefixes (e.g., A_1h, A_r3).
    """
    rows: list[dict[str, Any]] = []
    for pref in sweep_prefixes:
        sub = summarize_grid_from_summaries(
            artifacts_dir=artifacts_dir,
            sweep_prefix=pref,
            out_json=out_json.parent / f".tmp__{pref.replace(':','_').replace('/','_')}.json",
            primary_metric=primary_metric,
            compare_against=compare_against,
        )
        rows.extend(sub.get("rows", []))

    # Deduplicate by sweep_id (should be unique across prefixes)
    by_id: dict[str, dict[str, Any]] = {}
    for r in rows:
        sid = r.get("sweep_id")
        if not sid:
            continue
        by_id[sid] = r
    rows = [by_id[k] for k in sorted(by_id.keys())]

    summary: dict[str, Any] = {
        "sweep_prefixes": sweep_prefixes,
        "primary_metric": primary_metric,
        "rows": rows,
        "counts": {},
    }
    for b in compare_against:
        deltas = [r.get(f"delta_proposed_minus_{b}") for r in rows if r.get(f"delta_proposed_minus_{b}") is not None]
        wins = sum(1 for x in deltas if float(x) < 0.0)
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


