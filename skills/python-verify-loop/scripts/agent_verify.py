#!/usr/bin/env python3
"""agent_verify.py - external layered verifier for Python code changes.

Part of the ``python-verify-loop`` skill. Division of labor:

- The coding agent edits the working tree.
- THIS script is the judge: it runs the verification pipeline, collects
  structured errors, and reports PASS or FAIL. The agent never declares
  success itself and never commits unless this script reports PASS.

Pipeline layers (fast mode unless noted):

    1. format      ruff format .                 (auto-applies; no reasoning needed)
    2. lint        ruff check . --fix            (auto-fixes; final check validates)
    3. types       pyright                       (type errors are agent-fixable)
    4. tests       pytest <targeted files>       (fast) | pytest (full)
    5. security    bandit -r src                 (full only)
    6. git         git diff --check              (whitespace / conflict markers)
    7. arch        .agent/architecture.toml      (full only; import-graph rules)

All layers run in every invocation so the agent gets the full failure picture
in one shot, never a stop-at-first-error stream.

Output
------
Human-readable by default:

    [PASS] format
    [FAIL] types

    VERIFICATION FAILED

    Failed checks:

    1. types

    src/myapp/user.py:42
    "None" is not assignable to "User"

Use --json for machine-readable output:

    {"status": "failed", "mode": "fast", "checks": {...}, "errors": [...],
     "changed_files": [...], "targeted_tests": [...]}

On failure the structured errors are also written to .agent/last_failure.json
(attempt counter is read and incremented there) so a fix loop can consume the
same data every iteration.

Exit codes: 0 = PASS, 1 = FAIL, 2 = usage/configuration error.

Tool invocation
---------------
If ``uv`` is on PATH, tools run via ``uv run <tool>`` (project environment is
used). Otherwise tools run directly and must be on PATH. ``uv`` is preferred
but not required.

Python 3.11+ (uses stdlib tomllib for the architecture rules).
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

try:
    import tomllib
except ImportError:  # pragma: no cover - Python < 3.11
    tomllib = None


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

class Err:
    """One structured verification error (plan: tool/file/line/message)."""

    __slots__ = ("tool", "severity", "file", "line", "message")

    def __init__(self, tool, message, file=None, line=None, severity="error"):
        self.tool = tool
        self.severity = severity
        self.file = file
        self.line = line
        self.message = message

    def to_dict(self):
        return {
            "tool": self.tool,
            "severity": self.severity,
            "file": self.file,
            "line": self.line,
            "message": self.message,
        }

    def __str__(self):
        loc = ""
        if self.file:
            loc = self.file + (f":{self.line}" if self.line else "")
        return f"{loc}: {self.message}".strip(": ")


class LayerResult:
    __slots__ = ("status", "errors", "note")

    def __init__(self, status, errors=None, note=""):
        self.status = status          # "pass" | "fail" | "skip"
        self.errors = errors or []
        self.note = note


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run(cmd, cwd, timeout):
    """Run one command; return (returncode, combined_output)."""
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except FileNotFoundError:
        return 127, f"command not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return 124, f"timed out after {timeout}s: {' '.join(cmd)}"
    out = proc.stdout or ""
    err = proc.stderr or ""
    return proc.returncode, (out + err)


def tool_cmd(name, args):
    """Prefer `uv run <tool> ...`; fall back to bare `<tool> ...`."""
    if shutil.which("uv"):
        return ["uv", "run", name, *args]
    return [name, *args]


def is_tool_missing(returncode, output, name):
    return returncode == 127 or (returncode != 0 and "command not found" in output.lower())


def find_root(cwd, explicit):
    if explicit:
        return Path(explicit).resolve()
    try:
        top = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(cwd), capture_output=True, text=True,
        )
        if top.returncode == 0:
            return Path(top.stdout.strip()).resolve()
    except FileNotFoundError:
        pass
    return Path(cwd).resolve()


def changed_files(root):
    """Detect staged + unstaged + untracked files via `git status --porcelain`.

    Returns (files, note). files is empty when the project is not a git repo.
    """
    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(root), capture_output=True, text=True, encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError:
        return [], "git not found; change detection disabled"
    if proc.returncode != 0:
        return [], "not a git repository; change detection disabled"
    files = []
    ignored = ("__pycache__", "last_failure.json")
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        path = line[3:].strip()
        if path.startswith('"') and path.endswith('"'):
            path = path[1:-1].encode().decode("unicode_escape")
        if path.endswith(".pyc") or any(part in path for part in ignored):
            continue
        files.append(path)
    return files, ""


# ---------------------------------------------------------------------------
# Targeted test selection (plan: src/myapp/foo.py -> tests/test_foo.py)
# ---------------------------------------------------------------------------

def _test_candidates(changed, root):
    """Map changed Python files to existing test files."""
    tests_dir = root / "tests"
    candidates = set()
    for rel in changed:
        p = Path(rel)
        if not p.suffix == ".py":
            continue
        stem = p.stem
        if "test_" in p.name or p.name.startswith("test_"):
            candidates.add(p)
            continue
        for cand in (
            tests_dir / f"test_{stem}.py",
            tests_dir / "unit" / f"test_{stem}.py",
            tests_dir / "integration" / f"test_{stem}.py",
        ):
            if cand.exists():
                candidates.add(Path(os.path.relpath(cand, root)))
    # Fallback: any tests/**/test_<stem>.py file anywhere under tests/.
    if tests_dir.is_dir():
        stems = {Path(rel).stem for rel in changed if rel.endswith(".py")}
        for stem in sorted(stems):
            for cand in sorted(tests_dir.rglob(f"test_{stem}.py")):
                candidates.add(Path(os.path.relpath(cand, root)))
    return sorted(str(c) for c in candidates)


# ---------------------------------------------------------------------------
# Layers
# ---------------------------------------------------------------------------

def layer_format(root, timeout, auto_fix):
    code, out = run(tool_cmd("ruff", ["format", "."]), root, timeout)
    if is_tool_missing(code, out, "ruff"):
        return LayerResult("fail", [Err("format", "ruff not found - install it or add it to dev dependencies")])
    if code == 0:
        return LayerResult("pass", note="formatting applied" if auto_fix else "")
    return LayerResult("fail", [Err("format", out.strip()[:2000])])


def layer_lint(root, timeout, auto_fix):
    if auto_fix:
        run(tool_cmd("ruff", ["check", ".", "--fix"]), root, timeout)
    code, out = run(tool_cmd("ruff", ["check", "."]), root, timeout)
    if is_tool_missing(code, out, "ruff"):
        return LayerResult("fail", [Err("lint", "ruff not found - install it or add it to dev dependencies")])
    if code == 0:
        return LayerResult("pass")
    errors = []
    for m in re.finditer(r"^(.+?):(\d+):(\d+):\s+(\S+)\s+(.+)$", out, re.M):
        errors.append(Err("lint", f"{m.group(4)} {m.group(5)}", m.group(1), int(m.group(2))))
    if not errors:
        errors = [Err("lint", out.strip()[:2000])]
    return LayerResult("fail", errors)


def layer_types(root, timeout):
    code, out = run(tool_cmd("pyright", []), root, timeout)
    if is_tool_missing(code, out, "pyright"):
        return LayerResult("fail", [Err("types", "pyright not found - install it or add it to dev dependencies")])
    errors = []
    for m in re.finditer(r"^\s*(.+?):(\d+):(\d+)\s+-\s+(error|warning|information):\s+(.+)$", out, re.M):
        sev = m.group(4)
        if sev != "error":
            continue
        errors.append(Err("types", m.group(5), m.group(1).strip(), int(m.group(2))))
    if code == 0:
        return LayerResult("pass")
    if not errors:
        errors = [Err("types", out.strip()[:2000])]
    return LayerResult("fail", errors)


def layer_tests(root, timeout, mode, targeted):
    if mode == "fast" and not targeted:
        return LayerResult("skip", note="no targeted tests for changed files")
    cmd = tool_cmd("pytest", ["-q", "--no-header", "-p", "no:cacheprovider", *targeted] if targeted else
                   ["-q", "--no-header", "-p", "no:cacheprovider"])
    code, out = run(cmd, root, timeout)
    if is_tool_missing(code, out, "pytest"):
        return LayerResult("fail", [Err("tests", "pytest not found - install it or add it to dev dependencies")])
    if code == 0:
        return LayerResult("pass")
    if code == 5:  # pytest: no tests collected
        return LayerResult("skip", note="no tests collected")
    errors = []
    for m in re.finditer(r"^FAILED\s+(.+?)(?:::([^\s]+))?\s+-\s+(.+)$", out, re.M):
        errors.append(Err("tests", m.group(3), m.group(1), None))
    if not errors:
        # Pull the first failing test location from the traceback header.
        for m in re.finditer(r"^_+ ([\w./\\-]+\.py):(\d+): in (\w+)$", out, re.M):
            errors.append(Err("tests", f"test failed at {m.group(3)}", m.group(1), int(m.group(2))))
            break
    if not errors:
        errors = [Err("tests", out.strip()[:2000])]
    return LayerResult("fail", errors)


def layer_security(root, timeout):
    src = root / "src"
    if not src.is_dir():
        return LayerResult("skip", note="no src/ directory")
    code, out = run(tool_cmd("bandit", ["-r", "src", "-q"]), root, timeout)
    if is_tool_missing(code, out, "bandit"):
        return LayerResult("fail", [Err("security", "bandit not found - install it or add it to dev dependencies")])
    if code == 0:
        return LayerResult("pass")
    errors = []
    lines = out.splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"^>> Issue: \[([A-Za-z0-9_]+):([^\]]+)\] (.+)$", line.strip())
        if not m:
            continue
        bandit_id, detail, desc = m.group(1), m.group(2), m.group(3)
        severity = "error"
        loc = None
        for j in range(i + 1, min(i + 8, len(lines))):
            sm = re.match(r"^\s*Severity:\s*(\w+)", lines[j].strip())
            if sm and severity == "error":
                severity = sm.group(1).lower()
            lm = re.match(r"^\s*Location:\s*(.+?):(\d+):\d+$", lines[j].strip())
            if lm:
                loc = (lm.group(1), int(lm.group(2)))
                break
        msg = f"{detail} ({bandit_id})"
        if desc and desc not in detail:
            msg = f"{detail}: {desc} ({bandit_id})"
        if loc:
            errors.append(Err("security", msg, loc[0], loc[1], severity=severity))
        else:
            errors.append(Err("security", msg, severity=severity))
    if not errors:
        errors = [Err("security", out.strip()[:2000])]
    return LayerResult("fail", errors)


def layer_git(root, timeout):
    errors = []
    code, out = run(["git", "diff", "--check"], root, timeout)
    if code == 127:
        return LayerResult("fail", [Err("git", "git not found")])
    code_cached, out_cached = run(["git", "diff", "--cached", "--check"], root, timeout)
    if code == 0 and code_cached != 0:
        code, out = code_cached, out_cached
    if code != 0:
        for m in re.finditer(r"^(.+?):(\d+):\s+(.+)$", out, re.M):
            errors.append(Err("git", m.group(3), m.group(1), int(m.group(2))))
    # Untracked files are invisible to `git diff --check`; scan them directly
    # for trailing whitespace and conflict markers.
    try:
        proc = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=str(root), capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
    except FileNotFoundError:
        proc = None
    if proc is not None and proc.returncode == 0:
        for rel in proc.stdout.splitlines():
            p = root / rel
            try:
                if not p.is_file() or p.stat().st_size > 1_000_000:
                    continue
                text = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            lines = text.splitlines()
            has_side_marker = any(
                re.match(r"^(<{7}|>{7})[ \t]", ln) for ln in lines
            )
            for lineno, line in enumerate(lines, start=1):
                if re.search(r"[ \t]+$", line):
                    errors.append(Err("git", "trailing whitespace", rel, lineno))
                if re.match(r"^(<{7}|>{7})[ \t]", line):
                    errors.append(Err("git", "conflict marker", rel, lineno))
                elif has_side_marker and re.match(r"^={7}$", line):
                    errors.append(Err("git", "conflict marker", rel, lineno))
    if errors:
        return LayerResult("fail", errors)
    return LayerResult("pass")


def _package_root(src):
    """First directory under src/ is the import package root (e.g. myapp)."""
    try:
        return next(p for p in sorted(src.iterdir()) if p.is_dir())
    except StopIteration:
        return None


def _module_of(rel_path):
    """First path component under the package root = architecture module id.

    src/myapp/api/x.py (rel: api/x.py) -> 'api'; a file directly in the
    package root (rel: __init__.py) -> ''.
    """
    if len(rel_path.parts) <= 1:
        return ""
    return rel_path.parts[0]


def layer_arch(root, timeout=60):
    cfg = root / ".agent" / "architecture.toml"
    if not cfg.is_file():
        return LayerResult("skip", note="no .agent/architecture.toml")
    if tomllib is None:
        return LayerResult("fail", [Err("arch", "architecture check requires Python 3.11+ (tomllib)")])
    try:
        with open(cfg, "rb") as fh:
            data = tomllib.load(fh)
    except Exception as exc:  # noqa: BLE001 - config is project-owned
        return LayerResult("fail", [Err("arch", f"cannot parse {cfg}: {exc}")])
    rules = data.get("rules", {})
    if not rules:
        return LayerResult("skip", note="architecture.toml has no [rules]")
    src = root / "src"
    pkg_root = _package_root(src) if src.is_dir() else None
    if pkg_root is None:
        return LayerResult("skip", note="no src/<package>/ layout")
    pkg = pkg_root.name
    errors = []
    for py in sorted(pkg_root.rglob("*.py")):
        rel = py.relative_to(pkg_root)
        module = _module_of(rel)
        if module not in rules:
            continue
        allowed = set(rules[module]) | {module}
        try:
            tree = compile(py.read_text(encoding="utf-8", errors="replace"), str(py), "exec", ast.PyCF_ONLY_AST)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                if node.module == pkg or node.module.startswith(pkg + "."):
                    target = node.module[len(pkg) + 1:].split(".")[0] if len(node.module) > len(pkg) else ""
                    if target and target not in allowed:
                        errors.append(Err("arch",
                                          f"'{module}' must not import from '{target}' (allowed: {sorted(allowed)})",
                                          str(py), node.lineno))
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == pkg or alias.name.startswith(pkg + "."):
                        target = alias.name[len(pkg) + 1:].split(".")[0] if len(alias.name) > len(pkg) else ""
                        if target and target not in allowed:
                            errors.append(Err("arch",
                                              f"'{module}' must not import from '{target}' (allowed: {sorted(allowed)})",
                                              str(py), node.lineno))
    if errors:
        return LayerResult("fail", errors)
    return LayerResult("pass")


def layer_git_scope(root, timeout):
    """Report changed files; used by the agent to confirm its change claim."""
    files, note = changed_files(root)
    return LayerResult("pass", note=(note or ", ".join(files) or "no changes detected"))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args(argv):
    ap = argparse.ArgumentParser(
        prog="agent_verify.py",
        description="External layered verifier for Python code changes (python-verify-loop skill).",
    )
    ap.add_argument("--mode", choices=["fast", "full"], default="fast",
                    help="fast = format/lint/types/targeted tests/git (agent loop); "
                         "full = + full pytest + bandit + architecture (commit gate)")
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON on stdout")
    ap.add_argument("--changed-files", nargs="*", default=None,
                    help="explicit list of changed files (default: auto-detect via git status)")
    ap.add_argument("--no-auto-fix", action="store_true",
                    help="do not run ruff format / ruff check --fix")
    ap.add_argument("--failure-file", default=".agent/last_failure.json",
                    help="where structured failures are written (default: .agent/last_failure.json)")
    ap.add_argument("--commit", action="store_true",
                    help="after FULL verification PASS, git add + commit (verifier-triggered commit)")
    ap.add_argument("--commit-message", default="Verified by agent_verify.py")
    ap.add_argument("--root", default=None, help="project root (default: git root or cwd)")
    ap.add_argument("--timeout", type=int, default=900, help="per-layer timeout in seconds")
    return ap.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    root = find_root(Path.cwd(), args.root)
    auto_fix = not args.no_auto_fix

    if args.changed_files is not None:
        changed = list(args.changed_files)
        scope_note = ", ".join(changed) or "no files given"
    else:
        changed, scope_note = changed_files(root)
        if not changed:
            scope_note += " (no changed files detected)"

    targeted = _test_candidates(changed, root) if args.mode == "fast" else []

    results = {}
    results["format"] = layer_format(root, args.timeout, auto_fix)
    results["lint"] = layer_lint(root, args.timeout, auto_fix)
    results["types"] = layer_types(root, args.timeout)
    if args.mode == "full":
        results["tests"] = layer_tests(root, args.timeout, "full", [])
        results["security"] = layer_security(root, args.timeout)
        results["arch"] = layer_arch(root)
    else:
        results["tests"] = layer_tests(root, args.timeout, "fast", targeted)
    results["git"] = layer_git(root, args.timeout)

    failures = []
    for name, res in results.items():
        if res.status == "fail":
            failures.extend(res.errors)

    status = "passed" if not failures else "failed"

    # Error collector (plan: .agent/last_failure.json, attempt counter).
    if failures:
        attempt = 0
        fpath = root / args.failure_file
        try:
            with open(fpath, "r", encoding="utf-8") as fh:
                attempt = int(json.load(fh).get("attempt", 0))
        except Exception:  # noqa: BLE001 - file may not exist yet
            pass
        payload = {
            "status": "failed",
            "attempt": attempt + 1,
            "mode": args.mode,
            "checks": {n: r.status for n, r in results.items()},
            "errors": [e.to_dict() for e in failures],
            "changed_files": changed,
            "targeted_tests": targeted,
        }
        try:
            fpath.parent.mkdir(parents=True, exist_ok=True)
            with open(fpath, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, indent=2)
        except OSError as exc:
            failures.append(Err("verifier", f"cannot write {fpath}: {exc}"))

    # Commit gate: only verifier-triggered, only on full PASS.
    if args.commit:
        if failures or args.mode != "full":
            failures.append(Err("verifier",
                                "--commit requires full-mode PASS; refusing to commit on failure"))
            status = "failed"
        else:
            code, out = run(["git", "add", "-A"], root, args.timeout)
            if code != 0:
                failures.append(Err("verifier", f"git add failed: {out.strip()[:500]}"))
                status = "failed"
            else:
                code, out = run(["git", "commit", "-m", args.commit_message], root, args.timeout)
                if code != 0:
                    failures.append(Err("verifier", f"git commit failed: {out.strip()[:500]}"))
                    status = "failed"

    if args.json:
        payload = {
            "status": status,
            "mode": args.mode,
            "checks": {n: r.status for n, r in results.items()},
            "errors": [e.to_dict() for e in failures],
            "changed_files": changed,
            "targeted_tests": targeted,
            "scope": scope_note,
        }
        print(json.dumps(payload, indent=2))
    else:
        for name, res in results.items():
            label = {"pass": "PASS", "fail": "FAIL", "skip": "SKIP"}[res.status]
            suffix = f" ({res.note})" if res.note and len(res.note) < 120 else ""
            print(f"[{label}] {name}{suffix}")
        print()
        if failures:
            print("VERIFICATION FAILED")
            print()
            print("Failed checks:")
            print()
            seen = set()
            shown = 0
            for e in failures:
                key = (e.tool, e.file, e.line, e.message)
                if key in seen:
                    continue
                seen.add(key)
                shown += 1
                print(f"{shown}. {e.tool}")
                print()
                if e.file:
                    print(f"{e.file}" + (f":{e.line}" if e.line else ""))
                print(e.message)
                print()
        else:
            print("VERIFICATION PASSED")
        if changed:
            print(f"Changed files ({len(changed)}): {', '.join(changed[:20])}")
        if targeted:
            print(f"Targeted tests: {', '.join(targeted)}")

    return 1 if status == "failed" else 0


if __name__ == "__main__":
    sys.exit(main())
