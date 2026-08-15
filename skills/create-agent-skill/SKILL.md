---
name: create-agent-skill
description: >-
  Create, validate, and iteratively improve Agent Skills (SKILL.md format). Design a
  skill directory with spec-compliant frontmatter — name/description, MIT license,
  author attribution — write instructions that add what the agent lacks and omit what
  it knows, structure content with progressive disclosure, and optimize the description
  for reliable triggering. Use when the user asks to create, write, scaffold, draft,
  improve, or fix an agent skill or SKILL.md — for Oh My Pi (omp).
license: MIT
disable-model-invocation: true
metadata:
  author: Wildfire2282
  author-url: https://github.com/Wildfire2282
  version: "1.0"
---

# Create Agent Skills

Create a skill that installs into omp the current way — a symlink, not a copy. Skills live in the collection's `skills/` folder, and the whole folder is linked into omp (same pattern as `extensions` and `rules`):

```bash
ln -s ~/workspace/my-omp-config/skills ~/.omp/agent/skills      # user-wide
ln -s ~/workspace/my-omp-config/skills <project>/.omp/skills    # per-project
```

**Create every new skill at its permanent home — `~/workspace/my-omp-config/skills/<name>/`** (the current user's `workspace/my-omp-config/skills` — always via `~`, never a hardcoded username). The link makes omp read every skill straight from source: a new skill is usable as soon as its directory exists in `skills/`, and later edits apply without re-installing. omp discovers skills as `<skills-root>/<name>/SKILL.md`; restart omp (or reload skills) to pick up a new link. Deliverable: a directory with a valid `SKILL.md` — spec-compliant frontmatter plus instructions an agent can actually follow.

Follow the standard in `references/standard.md` exactly — naming, directory layout, frontmatter, license & attribution, README template, evals schema, `.gitignore` (§8 acceptance checklist).

## Deliverable

```text
<skill-name>/
├── SKILL.md          # Required: frontmatter + core instructions
├── LICENSE           # Required: MIT license, copyright line matches metadata.author
├── scripts/          # Optional: executable code (see references/scripts.md)
├── references/       # Optional: docs loaded on demand
├── assets/           # Optional: templates, resources
└── evals/            # Optional: evals.json + test fixtures (see references/evals.md)
```

- One file (`SKILL.md`) is a complete, valid deliverable; `LICENSE` is the only other required file for a distributable skill. Everything else is added only when it earns its place.
- Keep `SKILL.md` under 500 lines and ~5000 tokens — just what the agent needs on every run. Push detail into `references/` and tell the agent *when* to load each file ("Read `references/scripts.md` when writing a script for the skill" — not "see references for details").

## Workflow

### 0. Create in the right place — the folder is the install

The collection folder is the install point; there is no per-skill install step.

1. Create the skill directory at its permanent home: `mkdir -p ~/workspace/my-omp-config/skills/<name>` (current user's `workspace/my-omp-config/skills` — use `~`, never a hardcoded username).
2. Confirm the collection link is in place: `readlink ~/.omp/agent/skills` must resolve to `~/workspace/my-omp-config/skills` (user-wide), or `<project>/.omp/skills` for a per-project install.
   - Link missing or pointing elsewhere → create it: `ln -s ~/workspace/my-omp-config/skills ~/.omp/agent/skills`. Never copy the skill into the skills root — the link exposes the whole folder.
   - On this machine the link target is relative (`../../workspace/my-omp-config/skills` from `~/.omp/agent`) so it survives username changes — keep it relative; don't replace it with an absolute `/home/...` target.
3. Once the skill's files exist, it is live through the link — restart omp (or reload skills) to register the new directory. Verify with `test -f ~/.omp/agent/skills/<name>/SKILL.md`.

### 1. Gather real expertise — never generate from scratch

A skill built from an LLM's general training knowledge comes out vague ("handle errors appropriately"). Ground it in domain specifics:

- **Extract from a hands-on task** when available: capture the steps that worked, the corrections made, input/output formats, and the context the user had to supply.
- **Synthesize from project artifacts** otherwise: internal docs, runbooks, API specs, schemas, review comments, real failure cases. Project-specific material beats generic references.
- If the user hasn't provided source material, ask for it or state that the skill will be generic — do not fabricate API names, commands, or conventions.

### 2. Draft the SKILL.md

Frontmatter (see `references/frontmatter.md` for the full field reference):

```yaml
name: <lowercase-hyphenated>
description: <what it does + when to use it, imperative phrasing, ≤1024 chars>
license: MIT
disable-model-invocation: true   # manual trigger only: /skill:<name>
metadata:
  author: <github-username>
  author-url: https://github.com/<github-username>
# optional: compatibility, allowed-tools
```

- **License & attribution are required, not optional.** Every distributable skill: declares `license: MIT` in frontmatter, ships a `LICENSE` file with the standard MIT text whose copyright line reads `Copyright (c) <year> <author>`, and carries the author's GitHub identity in `metadata.author` / `metadata.author-url`. All three must agree with each other. The MIT template and full rules: `references/frontmatter.md`.
- `name` must match the directory name: 1-64 chars, lowercase letters/digits/hyphens only, no leading/trailing/consecutive hyphens.
- **Write everything in English.** Frontmatter values, instructions, examples, comments in bundled scripts, and reference files must all be in English. Skills are stable artifacts consumed by agents across teams and locales; one language keeps instructions consistent and avoids mixed-language drift.
- Body: step-by-step instructions, examples of inputs/outputs, edge cases. Follow the writing principles in `references/writing-guidelines.md`.

### 3. Validate against the spec

- Check `name` against the rules above and verify it matches the directory name.
- Check `description`: non-empty, ≤1024 chars, says what the skill does AND when to use it.
- Check license: `license: MIT` is declared, a `LICENSE` file exists with the standard MIT text, and its `Copyright (c) <year> <author>` line matches `metadata.author`.
- Check attribution: `metadata.author` and `metadata.author-url` are both present and consistent — `author-url` must be `https://github.com/<author>`.
- Check the standard: run the §8 acceptance checklist in `references/standard.md` (README sections, evals schema, `.gitignore`) and fix every failure.
- Check the body: does every instruction tell the agent something it wouldn't know otherwise? Cut anything that doesn't.
- Check the language: all skill content — `SKILL.md`, frontmatter, `references/`, scripts, `assets/` — is written in English. Flag and rewrite any non-English content.
- If `skills-ref` is available (`skills-ref validate ./<skill>`), run it; fix whatever it flags.
- Check install: the collection link exposes the new skill — `test -f ~/.omp/agent/skills/<name>/SKILL.md` (or `<project>/.omp/skills/<name>/SKILL.md`) must succeed. If it fails, the skill is in the wrong folder or the link is broken — fix before delivering.

### 4. Optimize the description

The description is the *only* thing that decides activation — an under-specified one won't trigger when it should; an over-broad one triggers on the wrong tasks.

- Write it as an instruction: "Use this skill when…", focused on user intent (not implementation), explicitly listing the contexts where it applies, including implicit ones ("even if they don't mention 'CSV'"). Keep it concise.
- Test it: write ~20 eval queries (8-10 should-trigger, 8-10 should-not-trigger; near-misses matter most), run each 3×, compute trigger rate (pass threshold ≈ 0.5). Split 60/40 into train/validation sets and optimize against train only. Full procedure: `references/description-optimization.md`.

### 5. Evaluate and iterate

- Start with 2-3 realistic test prompts in `evals/evals.json` (prompt + expected output + optional files).
- Run each twice: with the skill and without (baseline). Record tokens/duration.
- Add assertions after seeing first outputs; grade PASS/FAIL with concrete evidence; aggregate into a benchmark with delta vs. baseline.
- Iterate: feed failed assertions, human feedback, and execution transcripts back into the skill. Stop when feedback is consistently empty or improvement plateaus. Details: `references/evals.md`.

## Gotchas

- **Don't over-scope or under-scope.** A skill should encapsulate one coherent unit of work. Too narrow → many skills load per task; too broad → imprecise triggering and unproductive paths.
- **Aim for moderate detail.** Concise stepwise guidance with one working example beats exhaustive documentation. If you're covering every edge case, most belong to the agent's judgment instead.
- **Provide defaults, not menus.** Pick one tool/approach as default, mention alternatives briefly — never list equal options.
- **Favor procedures over declarations.** Teach *how to approach a class of problems*, not *what to produce for one instance*. Output-format templates and hard constraints ("never output PII") are fine — the approach must generalize.
- **Match specificity to fragility.** Give freedom where variation is harmless (explain *why*); be prescriptive where sequences are fragile (exact commands, "do not modify").
- **Add what the agent lacks, omit what it knows.** No explanations of PDFs, HTTP, or database migrations. Ask per item: "Would the agent get this wrong without this instruction?"
- **Gotchas sections are the highest-value content.** Environment-specific facts that defy reasonable assumptions (soft deletes, ID naming mismatches, health vs. ready endpoints). Keep them in `SKILL.md`, where the agent reads them *before* hitting the situation.
- **Scripts: never interactive.** Agents can't answer TTY prompts. Accept flags/env/stdin, document with `--help`, print actionable error messages, prefer structured output on stdout (JSON/CSV), diagnostics on stderr. Full guidance: `references/scripts.md`.

## References — load on demand

- `references/standard.md` — the full skill standard: naming, layout, frontmatter, license & attribution, evals schema, README template, `.gitignore`, acceptance checklist
- `references/frontmatter.md` — every frontmatter field, constraints, examples
- `references/writing-guidelines.md` — context budgeting, control calibration, instruction patterns
- `references/description-optimization.md` — trigger testing, train/validation split, optimization loop
- `references/evals.md` — test case design, assertions, grading, benchmark, iteration loop
- `references/scripts.md` — one-off commands, self-contained scripts, agentic script design
