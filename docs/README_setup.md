## Setup (Windows / PowerShell)

This project targets **Python 3.12+**.

### 1) Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

### 2) Install dependencies

Option A (recommended): install as an editable package from `pyproject.toml`

```powershell
pip install -e .[dev]
```

Option B: install from `requirements.txt`

```powershell
pip install -r requirements.txt
```

### 3) Sanity checks

```powershell
python -c "import typer,pydantic,numpy,pandas,pyarrow,matplotlib; print('deps ok')"
exp-suite version
```

### 4) First stub run (proves artifact contract)

```powershell
exp-suite run --config .\configs\example.toml --seed 0 --out .\artifacts
```

### 4) Dependency rationale

See `docs/dependencies.md`.


