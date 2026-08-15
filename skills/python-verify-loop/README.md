# python-verify-loop

An [Agent Skill](https://agentskills.io) for Oh My Pi (omp), the AI coding harness — run an external layered verification pipeline on Python code changes and iterate fixes until PASS or the retry limit is reached.

## What it covers

- External judge loop: the agent edits, the verifier decides, the agent fixes — never self-certifies
- Layered pipeline: Ruff format/lint (auto-fix), Pyright types, targeted + full pytest, Bandit security, git diff sanity, architecture import rules
- Structured error collection (tool/file/line/message) into `.agent/last_failure.json` with an attempt counter
- Verifier-triggered commit, hard retry limit (5), no commit on failure
- Task-type extras for API, database, and CLI changes
- Project bootstrap: `pyproject.toml` blocks, `.agent/rules.md`, `.agent/architecture.toml`, git pre-commit hook

## Structure

```text
python-verify-loop/
├── SKILL.md                # Core workflow: the verify-fix loop
├── LICENSE                 # MIT
├── README.md
├── .gitignore
├── scripts/
│   └── agent_verify.py     # Executable verifier (fast/full, JSON, --commit)
├── references/
│   ├── pipeline.md         # Layers, targeted test mapping, error format, commit protocol
│   └── setup.md            # Bootstrapping the pipeline into a project
├── assets/
│   ├── pyproject-verifier.toml   # [tool.ruff]/[tool.pyright]/[tool.pytest] blocks
│   ├── rules.md                  # .agent/rules.md template
│   ├── architecture.toml         # .agent/architecture.toml example
│   └── pre-commit.sh             # git pre-commit hook template
└── evals/
    └── evals.json
```

## Installation

Clone the repository and link the folder into omp's user skills directory:

```bash
git clone https://github.com/Wildfire2282/my-omp-config.git ~/workspace/my-omp-config
ln -s ~/workspace/my-omp-config/skills ~/.omp/agent/skills
```

Per-project: link into `<project>/.omp/skills` instead. omp discovers skills as `<skills-root>/<name>/SKILL.md`; restart omp (or reload skills) to pick up new skills.

## Usage

The skill auto-invokes when the task matches its description — Python code changes, failing tests or type errors, work that must pass lint/type/test/security gates. It can also be triggered manually:

```
/skill:python-verify-loop
```

Then run the workflow:

```bash
python scripts/agent_verify.py --mode fast     # agent loop
python scripts/agent_verify.py --mode full     # commit gate
python scripts/agent_verify.py --mode full --json
```

## Requirements

- Python 3.11+ (the verifier uses stdlib `tomllib`)
- Recommended toolchain: `uv`, `ruff`, `pyright`, `pytest`, `bandit`
- `git` for change detection, the git layer, and verifier-triggered commit
- Without `uv`, tools must be on PATH (the verifier falls back to bare commands)

## Source & verification

Design derived from the author's design document "Agent Self-Repair Loop" (a verification closed loop for Python coding agents): external verifier, layered checks, structured error collection, bounded fix loop, verifier-triggered commit. The `scripts/agent_verify.py` verifier was smoke-tested against a scratch project: FAIL path (all layers reporting structured errors), PASS path, targeted test selection, attempt counter, commit refusal on failure, and verifier-triggered commit.

## License

MIT — see [LICENSE](LICENSE).
