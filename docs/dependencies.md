## Dependency Rationale (Committee-Defensible)

This project intentionally uses a **small** set of mature dependencies. Each one exists to enforce measurement rigor, not to “add features.”

### Runtime dependencies

- **`typer`**: Provides a clean, reproducible CLI entrypoint so experiments can be run and re-run identically from the command line (no manual notebook steps).
- **`pydantic`**: Enforces schema validation for canonical objects (Event, DecisionRecord, ReconciliationSignal) and for configurations; prevents “silent shape drift.”
- **`numpy`**: Deterministic numerical computation and random generation (when seeded).
- **`pandas`**: Alignment/aggregation of traces and episode-level summaries; standard tooling for tabular analysis.
- **`pyarrow`**: Durable, columnar, immutable artifact storage (e.g., Parquet); supports large traces and stable typing.
- **`matplotlib`**: Figure generation **only from saved artifacts**, supporting the reproducibility contract.
- **`rich`**: Improves CLI readability (structured logs). Optional in spirit, but small and stable.

### Dev-only dependencies

- **`pytest`**: Ensures core invariants (schema validity, determinism under seeds, artifact completeness).
- **`ruff`**: Fast linting/format checks; keeps the codebase consistent and reduces review friction.

### Explicit non-dependencies (on purpose)

- **No heavyweight workflow/orchestration frameworks** (Airflow, Prefect, etc.): too much surface area for this thesis scope.
- **No distributed compute dependencies** (Spark, Ray): add complexity and failure modes without improving measurement validity here.
- **No deep learning stacks** (PyTorch, TensorFlow): not required for the measurement posture.

