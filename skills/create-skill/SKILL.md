---
name: create-skill
description: >-
  Create a new Agent Skill from scratch with spec-compliant SKILL.md frontmatter, MIT license, README and evals, including self-check against the skill standard. Use when the user asks to create, scaffold or draft a new skill — not to review or install an existing one.
license: MIT
disable-model-invocation: true
metadata:
  author: Wildfire2282
  author-url: https://github.com/Wildfire2282
  version: "1.0"
---

# Create Skill

Create a new skill at its permanent home `~/workspace/my-omp-config/skills/<name>/` (always via `~`, never a hardcoded username). The collection folder is symlinked into omp (`~/.omp/agent/skills -> ../../workspace/my-omp-config/skills`), so a new directory is live after reload — no copy step.

Follow `references/standard.md` exactly (§8 acceptance checklist). Keep `SKILL.md` under 500 lines / ~5000 tokens; push detail into `references/` and tell the agent when to load each file.

## Deliverable

```text
<name>/
├── SKILL.md          # Required: frontmatter + core instructions
├── LICENSE           # Required: MIT, copyright matches metadata.author
├── README.md         # Required: §6 template
├── .gitignore        # Required: §7 template
├── references/       # Optional: docs loaded on demand
├── scripts/          # Optional: executable code
├── assets/           # Optional: templates
└── evals/evals.json  # Required: §5 schema, includes negative control
```

One `SKILL.md` is a complete deliverable; `LICENSE` is the only other required file for a distributable skill.

## Workflow

### 0. Create in the right place

1. `mkdir -p ~/workspace/my-omp-config/skills/<name>` (use `~`, never `/home/...`).
2. Confirm link: `readlink ~/.omp/agent/skills` must resolve to `~/workspace/my-omp-config/skills` (or `<project>/.omp/skills` for per-project). Keep it relative (`../../workspace/my-omp-config/skills` from `~/.omp/agent`).

### 1. Gather real expertise — never generate from scratch

- Extract from a hands-on task when available: steps that worked, corrections, I/O formats.
- Synthesize from project artifacts otherwise: docs, runbooks, API specs, failure cases.
- If no source material, ask for it or state the skill will be generic — do not fabricate API names or commands.

### 2. Draft SKILL.md

Frontmatter (see `references/frontmatter.md`):

```yaml
---
name: <lowercase-hyphenated>          # == directory name, 1-64 chars [a-z0-9-]+
description: >-                        # folded style, 1-1024 chars, what + when
  <first line>
  <continuation>
license: MIT
disable-model-invocation: true
metadata:
  author: <github-username>
  author-url: https://github.com/<github-username>
  version: "1.0"
---
```

Rules:
- `name` matches directory name, no leading/trailing/consecutive hyphens.
- `description` uses `>-` folded style, states what + when, ≤1024 chars.
- `license: MIT`, `LICENSE` file standard MIT text, copyright `Copyright (c) <year> <author>` matches `metadata.author`.
- `metadata.author` / `author-url` consistent (`https://github.com/<author>`).
- Body in English, <500 lines, push detail to `references/`. Follow `references/writing-guidelines.md` (add what agent lacks, omit what it knows; procedures over declarations; defaults not menus).

### 3. Self-check (inner loop — fix in place until PASS)

Run the §8 acceptance checklist from `references/standard.md` directly in this session:

- [ ] Directory name == frontmatter `name`
- [ ] `description` folded style, what+when, ≤1024 chars
- [ ] `license: MIT` declared; `LICENSE` present with standard text; copyright matches `author`
- [ ] `disable-model-invocation: true` present
- [ ] `metadata.author` + `author-url` consistent
- [ ] `metadata.version` quoted semver string
- [ ] Body English, <500 lines
- [ ] `README.md` follows §6 template
- [ ] `.gitignore` matches §7 template
- [ ] `evals/evals.json` present, §5 schema, negative control included
- [ ] `references/` files referenced from `SKILL.md` or `README.md` if present
- [ ] `test -f ~/.omp/agent/skills/<name>/SKILL.md` succeeds (or `<project>/.omp/skills/...`)

If any item FAILs, fix it immediately in the same session and re-check. Repeat until all PASS. If `skills-ref` is available (`skills-ref validate ./<name>`), run it and fix flags.

Self-check is a lightweight gate for your own output — it repairs the draft you just created. It does not replace `review-skill`, which is for external/existing skills. Do not run description optimization (20 queries) here — that belongs to `review-skill`.

### 4. Done — stop here

Report self-check result (all PASS with evidence). Do not install, do not chain.

## Gate — stop here

This skill ends here. Do not automatically invoke `review-skill` or `install-skill`, do not run `ln -s`, do not chain. Report the deliverable and ask the user whether to run `/skill:install-skill` or `/skill:review-skill` — wait for an explicit user instruction naming the next skill.

## References — load on demand

- `references/standard.md` — naming, layout, frontmatter, license, evals schema, README/.gitignore, §8 checklist
- `references/frontmatter.md` — frontmatter fields, constraints, examples
- `references/writing-guidelines.md` — context budgeting, control calibration, instruction patterns
