# omp-guide

An [Agent Skill](https://agentskills.io) for Oh My Pi (omp), the AI coding harness — tiny hint that reminds the agent to use built-in harness docs via `omp://` when operating on omp itself.

## What it covers

- Detects omp-related intents (skills/extensions/rules/config)
- Points the agent to `read("omp://")` and `read("omp://<file>")` instead of web search

## Structure

```
omp-guide/
├── SKILL.md
├── LICENSE
├── README.md
├── .gitignore
└── evals/evals.json
```

## Installation

Clone the repository and link the `skills` folder into omp's agent directory (same pattern as `extensions` and `rules`):

```bash
git clone https://github.com/Wildfire2282/my-omp-config.git ~/workspace/my-omp-config
ln -s ~/workspace/my-omp-config/skills ~/.omp/agent/skills
```

For a per-project install, link into `<project>/.omp/skills` instead. omp discovers skills as `<skills-root>/<name>/SKILL.md`; restart omp (or reload skills) to pick up new skills.

Tip: keep the link target relative to the home directory (`../../workspace/my-omp-config/skills` from `~/.omp/agent`) so it survives username changes — never bake `/home/<user>/...` into the link.

## Usage

Auto-triggers on omp-related operations. The agent will run `read("omp://")` and cite the relevant doc.

Manual:

```
/skill:omp-guide
```

## License

MIT — see [LICENSE](LICENSE).
