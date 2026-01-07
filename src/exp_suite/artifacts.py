from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_empty_parquet(path: Path, schema: pa.Schema) -> None:
    """Write an empty Parquet file with a declared schema.

    This gives us a stable artifact contract before we generate real data.
    """
    table = pa.Table.from_arrays([pa.array([], type=f.type) for f in schema], schema=schema)
    pq.write_table(table, path)


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


