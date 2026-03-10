from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any

import numpy as np
import pandas as pd
import pyarrow as pa

from exp_suite.config import DelayModel, Exp1Config
from exp_suite.schemas import event_schema


def _stable_id(*parts: Any) -> str:
    h = hashlib.sha1()
    for p in parts:
        h.update(str(p).encode("utf-8"))
        h.update(b"|")
    return h.hexdigest()


def _sample_delay_seconds(rng: np.random.Generator, delay: DelayModel, n: int) -> np.ndarray:
    fam = delay.family
    params = delay.params

    if fam == "fixed":
        d = float(params.get("seconds", 0.0))
        return np.full(shape=n, fill_value=max(0.0, d), dtype=float)

    if fam == "exponential":
        scale = float(params.get("scale", 1.0))
        scale = max(scale, 0.0)
        return rng.exponential(scale=scale, size=n)

    if fam == "lognormal":
        # numpy lognormal uses mean/sigma of underlying normal (in log-seconds)
        mu = float(params.get("mu", 0.0))
        sigma = float(params.get("sigma", 1.0))
        sigma = max(sigma, 0.0)
        return rng.lognormal(mean=mu, sigma=sigma, size=n)

    raise ValueError(f"Unsupported delay family: {fam}")


def generate_exp1_events(cfg: Exp1Config, *, seed: int) -> pa.Table:
    """Generate a synthetic evidence stream.

    Each entity has `events_per_entity` timepoints. Sources observe each timepoint independently
    (missingness applies per source/timepoint). `conflict_rate` controls how often sources disagree.
    """
    rng = np.random.default_rng(seed)
    base_time = datetime(2020, 1, 1, tzinfo=timezone.utc)
    step = timedelta(seconds=1)

    rows: list[dict[str, Any]] = []

    for e_idx in range(int(cfg.entity_count)):
        entity_id = f"e{e_idx:06d}"

        truth = 0

        for t_idx in range(int(cfg.events_per_entity)):
            event_time = base_time + (t_idx * step)

            conflict_moment = rng.random() < float(cfg.conflict_rate)

            # slow random walk keeps truth from being constant across the episode
            if rng.random() < 0.05:
                truth += int(rng.integers(-2, 3))

            observed_sources = []
            for s_idx in range(int(cfg.source_count)):
                if rng.random() < float(cfg.missingness):
                    continue
                observed_sources.append(s_idx)

            for s_idx in observed_sources:
                source_id = f"s{s_idx:03d}"

                if conflict_moment and len(observed_sources) >= 2:
                    # half the time, flip sign/offset to induce disagreement
                    delta = int(rng.choice([-2, -1, 1, 2]))
                    value = truth + delta
                else:
                    value = truth

                payload = {
                    "value": value,
                    "truth_proxy": truth,
                    "t_idx": t_idx,
                    "conflict_moment": conflict_moment,
                }

                rows.append(
                    {
                        "entity_id": entity_id,
                        "source_id": source_id,
                        "event_time": event_time,
                        # receipt_time filled later (after delay sampling)
                        "receipt_time": event_time,
                        "payload_json": json.dumps(payload, separators=(",", ":"), sort_keys=True),
                        "event_id": _stable_id("event", seed, entity_id, source_id, t_idx),
                    }
                )

    if not rows:
        return pa.Table.from_arrays(
            [pa.array([], type=f.type) for f in event_schema()], schema=event_schema()
        )

    df = pd.DataFrame(rows)
    delays = _sample_delay_seconds(rng, cfg.delay, len(df))
    df["receipt_time"] = df["event_time"] + pd.to_timedelta(delays, unit="s")

    # Ensure UTC-naive timestamps with microsecond precision (Arrow schema uses timestamp("us"))
    df["event_time"] = pd.to_datetime(df["event_time"], utc=True).dt.tz_convert(None)
    df["receipt_time"] = pd.to_datetime(df["receipt_time"], utc=True).dt.tz_convert(None)
    # Coerce to microsecond resolution so Arrow doesn't need to downcast from ns -> us.
    df["event_time"] = df["event_time"].astype("datetime64[us]")
    df["receipt_time"] = df["receipt_time"].astype("datetime64[us]")

    df = df.sort_values(["receipt_time", "entity_id", "source_id"], kind="mergesort").reset_index(
        drop=True
    )

    table = pa.Table.from_pandas(df, schema=event_schema(), preserve_index=False)
    return table


