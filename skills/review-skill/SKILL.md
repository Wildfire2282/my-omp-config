---
name: review-skill
description: >-
  Audit and normalize an existing Agent Skill not created by create-skill — validate against the skill standard, review writing quality, optimize description triggering and fix evals. Use when the user asks to review, audit, normalize or fix an existing skill.
license: MIT
disable-model-invocation: true
metadata:
  author: Wildfire2282
  author-url: https://github.com/Wildfire2282
  version: "1.0"
---

# Review Skill

Normalize an existing skill that was not created by `create-skill` (external import, hand-written, AI-generated, legacy). Input must be an existing directory `~/workspace/my-omp-config/skills/<name>/` containing `SKILL.md`. Do not create new skills — use `/skill:create-skill` for that.

This skill is read-only by default. Any write-back requires explicit user confirmation with a shown diff.

## Workflow

### 1. Static validation — §8 checklist

Run the §8 acceptance checklist from `references/standard.md` against the target directory. For each item report PASS/FAIL with evidence (`file:line`):

- [ ] Directory name == frontmatter `name` (§1)
- [ ] `description` uses `>-` folded style, says what + when, ≤1024 chars
- [ ] `license: MIT` declared; `LICENSE` present with standard MIT text; copyright line matches `metadata.author` (§4)
- [ ] `disable-model-invocation: true` present
- [ ] `metadata.author` + `author-url` consistent, GitHub account (§4)
- [ ] `metadata.version` quoted semver string (§3)
- [ ] Body English, <500 lines (§3)
- [ ] `README.md` follows §6 template (bare-name title, What it covers, Structure, Installation, License last)
- [ ] `.gitignore` matches §7 template
- [ ] `evals/evals.json` present, §5 schema, negative control included
- [ ] `references/` files referenced from `SKILL.md` or `README.md` if any
- [ ] Install check: `test -f ~/.omp/agent/skills/<name>/SKILL.md` (link exposes it)

If `skills-ref` is available (`skills-ref validate ./<name>`), run it and include its output.

Classify failures: `MUST FIX` (blocks install), `SHOULD FIX` (quality), `NIT` (style).

### 2. Semantic review

Load `references/writing-guidelines.md` and check:

- Add what agent lacks, omit what it knows — cut generic explanations
- Coherent unit — not too narrow/broad
- Moderate detail — concise stepwise + one working example, not exhaustive
- Progressive disclosure — `SKILL.md` <500 lines, detail in `references/` with when-to-load guidance
- Control calibration — freedom where harmless, prescriptive where fragile
- Defaults not menus, procedures over declarations, English throughout
- Gotchas in `SKILL.md` body (environment-specific corrections)

### 3. Description optimization

Per `references/description-optimization.md`:

- Write ~20 eval queries (8-10 should-trigger, 8-10 should-not-trigger, near-misses most valuable) if not provided
- Run each 3×, trigger rate threshold 0.5, split 60/40 train/validation, optimize against train only
- Diagnose: should-trigger fail → too narrow; should-not-trigger false positive → too broad
- Propose a revised `description` (stay ≤1024 chars, imperative phrasing, user intent focused). Do not apply yet.

### 4. Evals review

Per `references/evals.md` and `references/standard.md §5`:

- Schema: `skill_name` + `evals` array, ids from 1, each has `prompt`/`expected_output`/`assertions`
- Negative control present with assertions
- Assertions verifiable (not "output is good"), countable, evidence-based
- Suggest with/without baseline and grading improvements if needed

### 5. Report and patch

Produce a report with:
- Per-item PASS/FAIL with evidence
- Severity classification
- Unified diff for proposed fixes (frontmatter, LICENSE, README, .gitignore, evals, description)
- Validation of patched state (re-run §8 would PASS)

Do not write back yet.

### 6. Gate — confirm before apply

Present the report and diff. Ask the user explicitly: apply the patch? Wait for confirmation. Only after user says yes, apply the diff and re-validate (re-run §8 + `skills-ref validate` if available). If user declines, leave files untouched and report remains as artifact.

After apply (or decline), second gate: ask whether to run `/skill:install-skill` — do not auto-install, wait for explicit instruction naming that skill.

## References — load on demand

- `references/standard.md` — full skill standard, §8 checklist
- `references/frontmatter.md` — frontmatter fields, constraints, examples
- `references/writing-guidelines.md` — context budgeting, control calibration, patterns
- `references/description-optimization.md` — trigger testing, train/validation, optimization loop
- `references/evals.md` — test case design, assertions, grading, benchmark, iteration
- `references/scripts.md` — script design for agentic use (if bundling fixes into scripts/)
