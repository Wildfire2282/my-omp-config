# install-skill

An [Agent Skill](https://agentskills.io) for Oh My Pi (omp), the AI coding harness — install a skill by symlinking the skills collection into omp and verifying discoverability.

## What it covers

- Ensure the collection link `~/.omp/agent/skills -> ../../workspace/my-omp-config/skills` (or `<project>/.omp/skills` for per-project)
- Verify `test -f ~/.omp/agent/skills/<name>/SKILL.md` and report resolved target
- Instruct to restart omp (or reload skills) to pick up the new directory

## Structure

```text
install-skill/
├── SKILL.md                    # Core workflow: pre-check → ensure link → verify → gate
├── LICENSE                     # MIT
├── README.md
├── .gitignore
├── references/
│   └── install.md              # Link semantics, relative target rationale
└── evals/
    └── evals.json
```

`SKILL.md` stays under 500 lines; detail lives in `references/` and is loaded on demand.

## Installation

Clone the repository and link the `skills` folder into omp's agent directory (same pattern as `extensions` and `rules`):

```bash
git clone https://github.com/Wildfire2282/my-omp-config.git ~/workspace/my-omp-config
ln -s ~/workspace/my-omp-config/skills ~/.omp/agent/skills
```

For a per-project install, link into `<project>/.omp/skills` instead. omp discovers skills as `<skills-root>/<name>/SKILL.md`; restart omp (or reload skills) to pick up new skills.

Tip: keep the link target relative to the home directory (`../../workspace/my-omp-config/skills` from `~/.omp/agent`) so it survives username changes — never bake `/home/<user>/...` into the link.

## Usage

Trigger manually — the skill is not auto-invoked:

```
/skill:install-skill
```

## License

MIT — see [LICENSE](LICENSE).
