# Using scripts in skills

Skills can instruct agents to run shell commands and bundle reusable scripts in `scripts/`. Covers one-off commands, self-contained scripts with inline dependencies, and script interfaces designed for agentic use.

## One-off commands

When an existing package does what you need, reference it directly in `SKILL.md` — no `scripts/` directory required. Prefer tools that auto-resolve dependencies at runtime:

| Tool | Example | Notes |
| --- | --- | --- |
| `uvx` | `uvx ruff@0.8.0 check .` | Python packages in isolated envs; aggressive caching; ships with uv |
| `pipx` | `pipx run 'black==24.10.0' .` | Mature `uvx` alternative; available via OS package managers |
| `npx` | `npx eslint@9 --fix .` | npm packages on demand; ships with Node.js; pin with `package@version` |
| `bunx` | `bunx eslint@9 --fix .` | Bun's `npx` equivalent; only when the environment has Bun |
| `deno run` | `deno run npm:create-vite@6 my-app` | Runs from URLs/specifiers; needs `--allow-*` permission flags; use `--` to separate Deno flags |
| `go run` | `go run golang.org/x/tools/cmd/goimports@v0.28.0 .` | Built into the `go` command |

Tips:

- **Pin versions** (`npx eslint@9.0.0`) so behavior is stable over time.
- **State prerequisites** in `SKILL.md` ("Requires Node.js 18+"); use the `compatibility` frontmatter field for runtime-level requirements.
- **Move complex commands into scripts.** A one-off works for a tool with a few flags; anything hard to get right on the first try belongs in a tested script.

## Referencing scripts from SKILL.md

Use **relative paths from the skill directory root**. The agent resolves them automatically. List available scripts so the agent knows they exist:

```markdown
## Available scripts

- **`scripts/validate.sh`** — Validates configuration files
- **`scripts/process.py`** — Processes input data
```

Then instruct the agent to run them. The same relative-path convention works in `references/*.md` — script execution paths in code blocks are relative to the skill directory root, because the agent runs commands from there.

## Self-contained scripts

Bundle reusable logic in `scripts/` with dependencies declared inline — the agent runs one command, no manifest or install step. Several languages support this:

- **Python (PEP 723)** — TOML block inside `# ///` markers; run with `uv run scripts/extract.py` (or `pipx run`). Pin with PEP 508 specifiers (`"beautifulsoup4>=4.12,<5"`), use `requires-python` to constrain versions, `uv lock --script` for full reproducibility.
- **Deno** — `npm:` and `jsr:` import specifiers make every script self-contained by default; version specifiers follow semver (`@1.0.0`, `@^1.0.0`).
- **Bun** — auto-installs missing packages at runtime when no `node_modules` is found; pin versions in the import path (`import * as cheerio from "cheerio@1.0.0"`).
- **Ruby** — `bundler/inline` declares gems in the script; pin explicitly (`gem 'nokogiri', '~> 1.16'`) since there's no lockfile.

## Designing scripts for agentic use

The agent reads stdout and stderr to decide what to do next. Design choices that make scripts dramatically easier to use:

### Avoid interactive prompts (hard requirement)

Agents run in non-interactive shells — they cannot answer TTY prompts, password dialogs, or confirmation menus. A script that blocks on input hangs indefinitely. Accept input via flags, environment variables, or stdin:

```text
# Bad: hangs waiting for input
$ python scripts/deploy.py
Target environment: _

# Good: clear error with guidance
$ python scripts/deploy.py
Error: --env is required. Options: development, staging, production.
Usage: python scripts/deploy.py --env staging --tag v1.2.3
```

### Document usage with `--help`

`--help` is how the agent learns the interface. Include a brief description, available flags, and usage examples. Keep it concise — it enters the agent's context window.

### Write helpful error messages

The error message directly shapes the agent's next attempt. Say what went wrong, what was expected, and what to try:

```text
Error: --format must be one of: json, csv, table.
       Received: "xml"
```

### Use structured output

Prefer JSON/CSV/TSV over free-form text — consumable by both the agent and standard tools (`jq`, `cut`, `awk`). **Separate data from diagnostics**: structured data to stdout, progress/warnings to stderr.

### Further considerations

- **Idempotency.** Agents may retry commands. "Create if not exists" is safer than "create and fail on duplicate".
- **Input constraints.** Reject ambiguous input with a clear error rather than guessing; use enums and closed sets.
- **Dry-run support.** `--dry-run` lets the agent preview destructive/stateful operations.
- **Meaningful exit codes.** Distinct codes for different failure types (not found, invalid args, auth failure), documented in `--help`.
- **Safe defaults.** Destructive operations may require explicit confirmation flags (`--confirm`, `--force`).
- **Predictable output size.** Harnesses truncate large tool output (often 10-30K chars). Default to a summary or reasonable limit; support `--offset` for pagination, or require `--output` to opt into stdout for large outputs.

## Sources

Synthesized from the Agent Skills documentation on using scripts in skills (agentskills.io/skill-creation/using-scripts).
