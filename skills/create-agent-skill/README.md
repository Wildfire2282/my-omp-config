# create-agent-skill

An [Agent Skill](https://agentskills.io) for Oh My Pi (omp), the AI coding harness — create, validate, and iteratively improve Agent Skills, the `SKILL.md` format.

Give this skill to omp and it can scaffold a new skill end-to-end: gather real expertise, draft a spec-compliant `SKILL.md`, validate the structure, optimize the `description` for reliable triggering, and evaluate output quality against a baseline.

## What it covers

When activated, the skill walks through a five-step workflow:

1. **Gather real expertise** — extract a skill from a hands-on task or synthesize it from project artifacts; never fabricate from general knowledge.
2. **Draft the SKILL.md** — spec-compliant frontmatter (name/description, MIT license, author attribution) plus instructions written for progressive disclosure.
3. **Validate against the spec** — `name`/`description` constraints, license/attribution consistency, the §8 acceptance checklist in `references/standard.md`.
4. **Optimize the description** — trigger testing with ~20 eval queries, train/validation splits, and an optimization loop.
5. **Evaluate and iterate** — with/without baselines, assertions, grading, and benchmarks.

## Structure

```
create-agent-skill/
├── SKILL.md                    # Core workflow: frontmatter rules, writing principles, gotchas
└── references/
    ├── standard.md             # The full skill standard: naming, layout, frontmatter, license & attribution, evals schema, README template, .gitignore, acceptance checklist
    ├── frontmatter.md          # All frontmatter fields, constraints, examples
    ├── writing-guidelines.md   # Context budgeting, control calibration, instruction patterns
    ├── description-optimization.md  # Trigger testing and the description optimization loop
    ├── evals.md                # Test cases, assertions, grading, benchmark iteration
    └── scripts.md              # One-off commands, self-contained scripts, agentic script design
```

`SKILL.md` stays under 500 lines; the detail lives in `references/` and is loaded on demand.

## Installation

Clone the repository and link the folder into omp's user skills directory:

```bash
git clone https://github.com/Wildfire2282/my-skills.git
mkdir -p ~/.omp/agent/skills
ln -s "$(pwd)/my-skills/create-agent-skill" ~/.omp/agent/skills/create-agent-skill
```

Or copy the folder into `~/.omp/agent/skills/` (user-wide) or `<project>/.omp/skills/` (per-project). omp discovers skills as `<skills-root>/<name>/SKILL.md`; restart omp (or reload skills) to pick them up.

## Usage

Trigger manually — the skill is not auto-invoked:

```
/skill:create-agent-skill
```

## License

MIT — see [LICENSE](LICENSE).
