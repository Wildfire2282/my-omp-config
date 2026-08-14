# Pipeline reference

Layer-by-layer detail for `scripts/agent_verify.py`. Load this when the verifier output is unclear, when a layer's failure needs interpretation, or when applying task-type extras.

## Layers

The verifier always runs every layer in one invocation and aggregates results — never stop-at-first-error. Each layer's failures become structured errors.

| # | Layer | Command (via `uv run` when uv present) | Auto-fix? | Fails when | Mode |
|---|-------|----------------------------------------|-----------|------------|------|
| 1 | format | `ruff format .` | yes (always) | ruff cannot run | fast + full |
| 2 | lint | `ruff check . --fix`, then `ruff check .` | yes (violations it can fix) | remaining lint violations (E/F/W/I/UP/B/SIM…) | fast + full |
| 3 | types | `pyright` | no | any pyright error (`reportOptionalMemberAccess`, `reportAssignmentType`, …) | fast + full |
| 4 | tests | `pytest <targeted files>` (fast) / `pytest` (full) | no | any failed test; parseable as `FAILED tests/x.py::test_y - message` | fast + full |
| 5 | security | `bandit -r src` | no | any Bandit issue (B404 subprocess, B602 shell=True, B608 SQL, B301 pickle, …) | full only |
| 6 | git | `git diff --check` + `git diff --cached --check` + direct scan of untracked files | no | trailing whitespace, conflict markers, whitespace errors | fast + full |
| 7 | arch | internal AST import-graph check against `.agent/architecture.toml` | no | a module imports from a module not in its allowed list | full only |

## Failure semantics

- **format**: never fails on style — it applies formatting. A failure here means the tool itself errored (misconfigured ruff, unreadable file). Treat as infrastructure, not code.
- **lint**: remaining violations after `--fix` are real code issues (unused imports, shadowing, complexity). Fix them; do not add `# noqa` to pass.
- **types**: the most agent-valuable layer. Pyright messages point at exact file:line and usually name the fix ("Object of type None has no attribute X" → handle the None case).
- **tests**: a failure means a behavioral contract broke. The error carries `tests/file.py::test_name - message`. Read the failing test to learn the expected behavior — the test is the spec.
- **security**: hard failures by design. `eval`, `exec`, `subprocess.run(shell=True)`, hardcoded SQL, pickle of untrusted data are rejected. Do not add `# nosec`.
- **git**: `git diff --check` misses untracked files, so the verifier scans untracked files directly for conflict markers (`<<<<<<<`, `=======`, `>>>>>>>` with marker side lines) and trailing whitespace.
- **arch**: only modules listed in `.agent/architecture.toml` are constrained; imports of third-party and stdlib modules are ignored; intra-package imports are resolved to the first component after the package root (`from myapp.api.x import y` → module `api`).

## Targeted test mapping

The fast-mode tests layer selects tests for changed files, then runs only those:

1. Changed file itself starts with `test_` or contains `_test` → run it directly.
2. Convention candidates (if they exist): `tests/test_<stem>.py`, `tests/unit/test_<stem>.py`, `tests/integration/test_<stem>.py`.
3. Fallback: any `tests/**/test_<stem>.py` under the tests tree.

`src/myapp/parser.py` → `tests/test_parser.py` or `tests/unit/test_parser.py`. No matching tests → the layer is SKIPped (full mode covers the suite at the commit gate).

If you changed a test file, the verifier includes it. If the targeted selection misses a test you know covers the change, pass it explicitly: `--changed-files src/myapp/foo.py tests/regression/test_foo_case.py`.

## Structured error format

Human output: `[PASS]|[FAIL]|`[SKIP]` per layer, then numbered failed checks:

```text
VERIFICATION FAILED

Failed checks:

1. types

src/myapp/user.py:42
"None" is not assignable to "User"
```

`--json` emits:

```json
{
  "status": "failed",
  "mode": "fast",
  "checks": {"format": "pass", "lint": "pass", "types": "fail", "tests": "pass", "git": "pass"},
  "errors": [
    {"tool": "types", "severity": "error", "file": "src/myapp/user.py", "line": 42, "message": "\"None\" is not assignable to \"User\""}
  ],
  "changed_files": ["src/myapp/user.py"],
  "targeted_tests": ["tests/test_user.py"]
}
```

The same errors are written to `.agent/last_failure.json` on failure, with an `attempt` counter incremented per run. The agent loop should consume either the JSON stdout or that file — never raw terminal dumps.

Exit codes: `0` = PASS, `1` = FAIL, `2` = usage/configuration error.

## Commit protocol

- Commit is the verifier's privilege, never yours. The verifier commits only when `--mode full` passes:
  `python scripts/agent_verify.py --mode full --commit "message"`
- The verifier refuses to commit on failure or in fast mode.
- After 5 failed attempts, stop: report the remaining errors and request manual review. Never commit a failed state, never bypass the verifier with a direct `git commit`.

## Task-type extras

Beyond the base pipeline, match the change type to extra validation (project conventions may differ — confirm with the repo):

| Change type | Extra validation |
|---|---|
| API changes | OpenAPI/schema validation; API-level tests (auth, status codes, payload shapes) |
| Database changes | Migration test (up/down/round-trip); schema change test; seed/teardown hygiene |
| CLI changes | CLI integration test: parse args, run end-to-end, assert stdout/stderr/exit code |
| New module/package | Architecture rules still apply — add the module to `.agent/architecture.toml` if it has dependency constraints |
