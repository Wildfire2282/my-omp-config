# review-skill

An [Agent Skill](https://agentskills.io) for Oh My Pi (omp), the AI coding harness — audit and normalize an existing Agent Skill not created by create-skill, validating against the skill standard, reviewing writing quality, optimizing description triggering and fixing evals.

## What it covers

- Static validation against the §8 acceptance checklist with PASS/FAIL evidence
- Semantic review per `writing-guidelines.md` (context budgeting, control calibration, progressive disclosure)
- Description optimization per `description-optimization.md` (20 queries ×3, train/validation, threshold 0.5)
- Evals review per `evals.md` and `standard.md §5` (schema, negative control, verifiable assertions)
- Read-only report with unified diff; write-back only after explicit user confirmation

## Structure

```text
review-skill/
├── SKILL.md                    # Core workflow: validate → review → optimize → report → gate
├── LICENSE                     # MIT
├── README.md
├── .gitignore
├── references/
│   ├── standard.md             # Full skill standard, §8 checklist
│   ├── frontmatter.md          # Frontmatter fields
│   ├── writing-guidelines.md   # Writing principles
│   ├── description-optimization.md  # Trigger testing and optimization loop
│   ├── evals.md                # Test case design, grading, benchmark
│   └── scripts.md              # Script design for agentic use
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
/skill:review-skill
```

Provide the target skill path, e.g. `~/workspace/my-omp-config/skills/<name>`.

## License

MIT — see [LICENSE](LICENSE).
