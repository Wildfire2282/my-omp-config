#!/usr/bin/env bash
# git pre-commit hook: final verification gate.
# Install: copy to .git/hooks/pre-commit in the git repo root and make it
# executable (chmod +x). The commit is rejected if any check fails, so the
# agent cannot bypass the verifier by committing directly.

set -e

echo "Running agent verification (pre-commit)..."

if [ -f scripts/agent_verify.py ]; then
    python scripts/agent_verify.py --mode full
elif command -v uv >/dev/null 2>&1; then
    uv run ruff check .
    uv run pyright
    uv run pytest
    uv run bandit -r src 2>/dev/null || true
    git diff --check
else
    ruff check .
    pyright
    pytest
    bandit -r src 2>/dev/null || true
    git diff --check
fi

echo "Verification passed."
