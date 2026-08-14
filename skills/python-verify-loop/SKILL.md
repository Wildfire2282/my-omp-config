---
name: python-verify-loop
description: >-
  Verify Python code changes through an external layered pipeline (Ruff format and
  lint, Pyright types, targeted and full pytest, Bandit security, git diff sanity,
  architecture import rules), collect structured errors, and iterate fixes until
  PASS or the retry limit is reached. Use when modifying Python code in a
  uv-based project, fixing failing tests or type errors, making changes that must
  pass lint/type/test/security gates before commit, or when the user asks to test,
  verify, or check Python code changes.
license: MIT
compatibility: >-
  Python 3.11+; recommended toolchain: uv, ruff, pyright, pytest, bandit
metadata:
  author: Wildfire2282
  author-url: https://github.com/Wildfire2282
  version: "1.0"
---

# Python Verify Loop

Run an external, layered verification pipeline on Python code changes and iterate fixes until it passes — or stop at the retry limit and hand the failures to a human.

## Core principle: the agent is not the judge

You write the code; the verifier decides. Never self-certify a change:

- Never declare a change "looks fine" or "should pass" — run the pipeline and read its verdict.
- Never commit unless the verifier reports PASS.
- The verifier runs every layer in one invocation (no stop-at-first-error), so you get the full failure picture at once.

## Workflow

1. **Detect changes.** Run `git status --short` and `git diff --name-only`. Form your change claim (which files you intended to touch) — you will compare it against the verifier's changed-file report.
2. **Run the verifier.**

   - Fast (agent loop, after every meaningful edit): `python scripts/agent_verify.py --mode fast`
   - Full (commit gate): `python scripts/agent_verify.py --mode full`
   - Prefer `--json` when feeding results onward; `.agent/last_failure.json` holds the same data across attempts.
   - Layer meanings and failure semantics: `references/pipeline.md`.

3. **On PASS** — the change is verified. Run full verification, then commit (verifier-triggered only: `--mode full --commit "message"`; protocol in `references/pipeline.md`).
4. **On FAIL** — read the structured errors and fix ONLY what is reported. Do not:

   - disable a checker (`# noqa`, `type: ignore`, `skip`, `xfail`, `# nosec`)
   - weaken or delete tests to make them pass
   - remove type annotations
   - modify unrelated files
   - work around security findings (`eval`, `exec`, `shell=True`)

5. **Re-run the verifier.** At most 5 attempts. After the 5th failure: stop, report the remaining errors, and ask for manual review. Never commit a failed state.

## Task-type extras

Different change types need validation beyond the base pipeline. Apply the matching extra check from `references/pipeline.md` before declaring done:

- API changes → OpenAPI/schema validation + API tests
- Database changes → migration test + schema round-trip
- CLI changes → CLI integration test

## Testing policy

- Every behavioral change ships with a test. New code without a test is a defect.
- Targeted tests first — the verifier maps `src/myapp/foo.py` to `tests/test_foo.py`. The full suite runs at the commit gate, not on every edit.
- Never weaken or delete existing tests to pass; never add meaningless tests to inflate coverage. "New code has tests" beats a global coverage percentage.

## Gotchas

- `git diff --check` ignores untracked files. The verifier's git layer scans untracked files directly for conflict markers and trailing whitespace — new files are exactly where conflict markers hide.
- The verifier auto-applies `ruff format` and `ruff check --fix`. Don't re-run them by hand or spend tokens on them.
- If the project has no `scripts/agent_verify.py`, bootstrap it per `references/setup.md` (templates live in `assets/`).
- uv is preferred but not required; without it the verifier falls back to bare tool commands, which must then be on PATH.
- Security findings are hard failures. `eval()`, `exec()`, and `subprocess.run(..., shell=True)` are rejected; do not try to silence them.
- The architecture layer only constrains modules listed in `.agent/architecture.toml`; unlisted modules are free. Adding a module to the rules is a deliberate project decision, not a way to pass.

## References — load on demand

- `references/pipeline.md` — layer-by-layer commands, targeted test mapping, error collector format, commit protocol, task-type extras
- `references/setup.md` — bootstrap the verifier into a project: config, rules, architecture rules, pre-commit hook
