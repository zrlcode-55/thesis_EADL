from __future__ import annotations

import json
from pathlib import Path

from exp_suite.sweep import summarize_sweep


def test_summarize_sweep_basic(tmp_path: Path) -> None:
    sweep_dir = tmp_path / "sweep_test"
    sweep_dir.mkdir(parents=True)

    # Create two fake runs (baseline_a + proposed), each with ok metrics.
    r1 = sweep_dir / "run1"
    r2 = sweep_dir / "run2"
    r1.mkdir()
    r2.mkdir()

    (r1 / "metrics.json").write_text(
        json.dumps({"status": "ok", "metrics": {"M1_correctness_rate": 0.5, "M3_avg_loss": 2.0}}),
        encoding="utf-8",
    )
    (r2 / "metrics.json").write_text(
        json.dumps({"status": "ok", "metrics": {"M1_correctness_rate": 0.6, "M3_avg_loss": 3.0}}),
        encoding="utf-8",
    )

    sweep_manifest = {
        "sweep_id": "sweep_test",
        "created_utc": "2026-01-08T00:00:00Z",
        "git_rev": "deadbee",
        "configs": ["a.toml", "b.toml"],
        "seeds": [0],
        "runs": [
            {
                "run_id": "run1",
                "system": "baseline_a",
                "seed": 0,
                "manifest_path": str((r1 / "run_manifest.json").as_posix()),
                "metrics_path": str((r1 / "metrics.json").as_posix()),
            },
            {
                "run_id": "run2",
                "system": "proposed",
                "seed": 0,
                "manifest_path": str((r2 / "run_manifest.json").as_posix()),
                "metrics_path": str((r2 / "metrics.json").as_posix()),
            },
        ],
    }
    (sweep_dir / "sweep_manifest.json").write_text(json.dumps(sweep_manifest), encoding="utf-8")

    summary = summarize_sweep(sweep_dir)
    assert summary["sweep_id"] == "sweep_test"
    assert len(summary["included_runs"]) == 2
    assert len(summary["excluded_runs"]) == 0

    assert "baseline_a" in summary["systems"]
    assert "proposed" in summary["systems"]

    m = summary["systems"]["baseline_a"]["metrics"]["M3_avg_loss"]
    assert m["count"] == 1
    assert m["mean"] == 2.0


