# create-skill

An [Agent Skill](https://agentskills.io) for Oh My Pi (omp), the AI coding harness — create a new Agent Skill from scratch with spec-compliant SKILL.md, LICENSE, README and evals, including self-check against the skill standard.

## What it covers

- Scaffold a new skill at `~/workspace/my-omp-config/skills/<name>/` (via `~`, never hardcoded username)
- Gather real expertise from hands-on tasks or project artifacts, never fabricate
- Draft spec-compliant frontmatter (`name`/`description`/`license`/`metadata`) and body under 500 lines with progressive disclosure
- Self-check against the §8 acceptance checklist in `references/standard.md` and fix in place until all PASS
- Gate — stop without auto-installing; ask whether to run `/skill:install-skill`

## Structure

```text
create-skill/
├── SKILL.md                    # Core workflow: gather → draft → self-check → gate
├── LICENSE                     # MIT, copyright matches metadata.author
├── README.md
├── .gitignore
├── references/
│   ├── standard.md             # Skill standard, §8 checklist
│   ├── frontmatter.md          # Frontmatter fields and constraints
│   └── writing-guidelines.md   # Context budgeting, control calibration, patterns
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
/skill:create-skill
```

## License

MIT — see [LICENSE](LICENSE).
