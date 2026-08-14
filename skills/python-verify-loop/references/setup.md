# Setup — bootstrap the pipeline into a project

Load this when the target project has no verifier yet. Result: `scripts/agent_verify.py` plus the project rules the plan requires — all config centralized in `pyproject.toml`, agent rules in `.agent/rules.md`, architecture rules in `.agent/architecture.toml`, and a git pre-commit hook as the final gate.

## 1. Copy the verifier

```bash
cp <skill>/scripts/agent_verify.py scripts/agent_verify.py
```

The script is self-contained (Python 3.11+ stdlib only, `tomllib` for architecture rules).

## 2. Install the toolchain

```bash
uv add --dev ruff pyright pytest pytest-cov bandit
```

First version: Ruff, Pyright, pytest, Bandit — enough coverage for most agent-written code. Add `semgrep` only when the team needs rule-based scanning beyond Bandit. Skip `pytest-cov` until the coverage policy is decided (see §5).

## 3. Merge verifier config into pyproject.toml

Copy the blocks from `assets/pyproject-verifier.toml` into the project's `pyproject.toml`:

- `[tool.ruff]` — line-length 100, target py312, lint select `E,F,W,I,UP,B,SIM`, double quotes
- `[tool.pyright]` — include `src` + `tests`, `typeCheckingMode: standard`
- `[tool.pytest.ini_options]` — `testpaths = ["tests"]`, `addopts = ["-ra", "--strict-markers"]`

Two additions beyond a bare lint setup that make src-layout verification work without an installed package:

- `[tool.pyright] extraPaths = ["src"]` — pyright resolves `import myapp` from the src layout
- `[tool.pytest.ini_options] pythonpath = ["src"]` — pytest imports the package under test (pytest 7+)

## 4. Agent rules file

Copy `assets/rules.md` to `.agent/rules.md`. This is the contract the agent codes against — short, normative, one page:

- Architecture dependency flow (`api → services → repositories → models` in the template; adjust per project)
- Python rules: 3.12+, type hints, no `Any` unless necessary, no `eval`/`exec`, no `shell=True`
- Every behavioral change must have tests
- No dependencies unless necessary
- Keep changes minimal; do not modify unrelated files

Principle: the rules tell the agent how to write; the verifier decides whether it obeyed.

## 5. Architecture rules (optional)

Copy `assets/architecture.toml` to `.agent/architecture.toml` and adjust for the project's real module layout. Semantics:

```toml
[rules]
api = ["services"]          # api may import from services
services = ["repositories"] # services may import from repositories
repositories = ["models"]
models = []
```

- Keys are the first path component under the package root (`src/<pkg>/api/...` → `api`).
- A module may import from its own list plus itself; anything else under the package is a violation (reverse dependencies fail).
- Modules not listed are unconstrained. Only list modules with real dependency constraints.
- Imports of stdlib/third-party packages are ignored.

The check runs in full mode only (it is a commit-gate concern, not an edit-loop one).

## 6. Pre-commit hook (final gate)

Copy `assets/pre-commit.sh` to `.git/hooks/pre-commit` (git repo root) and make it executable. It runs the full verification so a commit is rejected even if the agent tries to commit directly — the verifier's authority is enforced at the git level too.

## 7. First full run

```bash
python scripts/agent_verify.py --mode full
```

Expect a first-run FAIL: the repo starts with existing lint/type/test debt. Fix the reported issues once, deliberately, and let the commit gate stay green from there. If the project intentionally has debt, curate `.agent/rules.md` and pyproject rules rather than adding `noqa`/`type: ignore` noise.

## 8. Coverage policy

Prefer "new code must have tests" over a global coverage percentage — the second encourages meaningless tests. Add `pytest --cov` reporting only when the team explicitly wants a gate, and keep the threshold below what pushes agents into test-inflation.
