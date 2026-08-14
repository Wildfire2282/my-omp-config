# github-cli

An [Agent Skill](https://agentskills.io) for Oh My Pi (omp), the AI coding harness — operate GitHub from the command line with the official GitHub CLI (`gh`).

## What it covers

- **Auth** — interactive, token, enterprise, multi-account, git integration
- **Core command map** — repos, issues, PRs, releases, workflows, secrets, search, API, codespaces, projects
- **JSON output & scripting** — `--json`/`--jq`/`--template`, non-interactive execution, exit codes
- **`gh api`** — REST and GraphQL, pagination, typed fields
- **Gotchas** — prompts hanging automation, PR merge strategies, secret handling, enterprise/auth ambiguity

## Structure

```
github-cli/
├── SKILL.md                # core instructions: auth, command map, patterns, gotchas
├── references/             # loaded on demand
│   ├── commands.md         # full command reference with flags
│   ├── api.md              # gh api REST/GraphQL deep dive
│   └── environment.md      # env vars, config, exit codes
└── evals/
    └── evals.json          # trigger/eval test cases
```

## Installation

Clone the repository and link the folder into omp's user skills directory:

```bash
git clone https://github.com/Wildfire2282/my-skills.git
mkdir -p ~/.omp/agent/skills
ln -s "$(pwd)/my-skills/github-cli" ~/.omp/agent/skills/github-cli
```

Or copy the folder into `~/.omp/agent/skills/` (user-wide) or `<project>/.omp/skills/` (per-project). omp discovers skills as `<skills-root>/<name>/SKILL.md`; restart omp (or reload skills) to pick them up.

## Usage

Trigger manually — the skill is not auto-invoked:

```
/skill:github-cli
```

## Requirements

Requires the GitHub CLI (`gh`) installed and authenticated:
`brew install gh`, `sudo apt install gh`, or from
https://github.com/cli/cli/releases. Then `gh auth login`.

## Source & verification

Source material: the official manual at https://cli.github.com/manual/
(crawled 2026-08-04).

## License

MIT — see [LICENSE](LICENSE).
