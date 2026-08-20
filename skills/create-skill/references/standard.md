# Skill Standard

Single source of truth for how a skill is named, structured, licensed, attributed, and documented. Every skill MUST conform; new skills are rejected until they do.

## 1. Naming

- Name matches `[a-z0-9]+(-[a-z0-9]+)*`: lowercase letters, digits, and hyphens only.
- No uppercase, underscores, camelCase, spaces, or dots.
- No leading, trailing, or consecutive hyphens. 1–64 characters.
- The directory name MUST equal the frontmatter `name`.
- Name the subject, not the kind: tool/library skill = the tool's official name lowercased (`github-cli`, not `gh`); capability skill = verb–object (`create-agent-skill`).
- No redundant type suffixes (`-skill`, `-dev`, `-tool`) — except when the suffix is part of the meaning (`create-agent-skill` keeps `-skill` because it is the object of `create`).
- Avoid names that collide with broader concepts (`svgjs`, not `svg`).

Valid: `pdf-processing`, `data-analysis`, `svgjs`, `create-agent-skill`
Invalid: `PDF-Processing`, `data_analysis`, `dataAnalysis`, `-pdf`, `pdf-`

## 2. Directory layout

Every skill is one directory `<skills-root>/<name>/` containing:

```
<name>/
├── SKILL.md          # Required: frontmatter + core instructions
├── LICENSE           # Required: MIT license (§4)
├── README.md         # Required: follows the template (§6)
├── .gitignore        # Required: shared template (§7)
├── references/       # Optional: docs loaded on demand
├── evals/            # Recommended: evals/evals.json (§5)
├── scripts/          # Optional: executable code
└── assets/           # Optional: templates, resources
```

## 3. SKILL.md frontmatter

Required fields, in this order:

```yaml
---
name: <lowercase-hyphenated>            # == directory name (§1)
description: >-                          # what + when to use it, 1-1024 chars
  <first line>
  <folded continuation lines>
license: MIT                             # repository-wide license
disable-model-invocation: true           # manual trigger only: /skill:<name>
compatibility: >-                        # optional: environment requirements
  <requirements>
metadata:
  author: <github-username>              # required, no @ prefix, no URL
  author-url: https://github.com/<github-username>   # required
  version: "1.0"                         # skill's own version, quoted semver string
---
```

Rules:

- `name` MUST equal the directory name and match `[a-z0-9]+(-[a-z0-9]+)*` (§1).
- `description` MUST use the `>-` folded style (never a single long line), state both *what* the skill does and *when to use it*, and stay within 1-1024 chars.
- `license` MUST be `MIT` and MUST agree with the bundled `LICENSE` file (§4).
- `disable-model-invocation: true` is REQUIRED: skills are invoked manually via `/skill:<name>`; the model never auto-invokes them.
- `metadata` MUST include `author` and `author-url`, pointing at the same GitHub account.
- `metadata.version` is the **skill's own version** (quoted string, e.g. `"1.0"`) — never a version of the library or tool the skill documents.
- `compatibility` is optional; when present, use the folded style and keep it under 500 chars.
- The body MUST be written in English, stay under 500 lines, and push detail into `references/` loaded on demand.

## 4. License & attribution

Three things MUST agree:

1. Frontmatter declares `license: MIT`.
2. The skill directory contains a `LICENSE` file with the full standard MIT text (below).
3. The LICENSE copyright line matches `metadata.author`.

Standard MIT `LICENSE` file — replace `<year>` with the current year and `<author>` with the GitHub username:

```text
MIT License

Copyright (c) <year> <author>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

Attribution rules:

- `metadata.author` — the GitHub username, lowercase, no `@` prefix, no URL.
- `metadata.author-url` — the GitHub profile URL: `https://github.com/<author>`.
- The LICENSE copyright line uses the same `<author>`: `Copyright (c) <year> <author>`.
- If the skill is derived from external documentation (e.g. a library's official docs), note the source in the README under `## Source & verification`, but the skill's own attribution still names the skill author.

## 5. evals

Every skill SHOULD ship `evals/evals.json` (mandatory for new skills). One schema, used by all skills:

```json
{
  "skill_name": "<name>",
  "evals": [
    {
      "id": 1,
      "prompt": "A realistic user message that should trigger the skill.",
      "expected_output": "Human-readable description of what success looks like.",
      "assertions": [
        "Verifiable statement about the output",
        "Another verifiable statement"
      ]
    }
  ]
}
```

Rules:

- Top-level keys: `skill_name` (== skill name) and `evals` (array). No other shapes.
- `id`: integers starting at 1, strictly increasing.
- Every test case MUST have `prompt`, `expected_output`, and `assertions` (non-empty array of verifiable statements).
- Include at least one negative control — a prompt the skill should NOT be needed for — and give it assertions too (e.g. "The answer does not introduce skill-specific API calls").
- `files` (optional) may reference fixtures under `evals/files/`.
- The full eval workflow (running, grading, benchmarking) is documented in `references/evals.md`.

## 6. README template

Every `README.md` follows this section order. Sections marked optional are included only when applicable.

```markdown
# <name>

An [Agent Skill](https://agentskills.io) for Oh My Pi (omp), the AI coding harness — <one-line description of what the skill does>.

## What it covers

- <capability>
- <capability>

## Structure

<tree diagram of the skill directory>

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
/skill:<name>
```

## Requirements      (optional)

- <environment or tool requirements>

## Source & verification   (optional; for skills derived from external docs)

- <source material and how it was verified>

## License

MIT — see [LICENSE](LICENSE).
```

Rules:

- Title is `# <name>` — the bare skill name, never "`<name> Agent Skill`".
- `## Installation` is mandatory in every README and MUST use the exact commands above (the same for every skill — skills ship in the collection's `skills/` folder).
- `## License` is the last section in every README.

## 7. .gitignore template

Every skill directory and the repository root carry the identical `.gitignore`:

```text
# Editors
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# Windows download artifacts (Zone.Identifier ADS)
*:Zone.Identifier

# Python
__pycache__/
*.py[cod]
.venv/
venv/

# Logs
*.log
```

## 8. Acceptance checklist

Before a skill is added or merged, verify all of the following:

- [ ] Directory name == frontmatter `name` (§1 naming rules)
- [ ] `description` uses `>-` folded style, says what + when, ≤1024 chars
- [ ] `license: MIT` declared; `LICENSE` file present with standard MIT text; copyright line matches `metadata.author`
- [ ] `disable-model-invocation: true` present (manual trigger only, `/skill:<name>`)
- [ ] `metadata.author` + `metadata.author-url` present, consistent, GitHub account
- [ ] `metadata.version` is the skill's own quoted semver string, not a library version
- [ ] Body in English, <500 lines
- [ ] `README.md` follows §6 template: bare-name title, `## What it covers`, `## Structure`, `## Installation`, `## License` (last)
- [ ] `.gitignore` matches §7 template
- [ ] `evals/evals.json` present and matches §5 schema; negative control included
- [ ] `references/` files (if any) are referenced from `SKILL.md` or `README.md`
- [ ] Install check: the collection link exposes the skill — `test -f ~/.omp/agent/skills/<name>/SKILL.md` succeeds (or `<project>/.omp/skills/<name>/SKILL.md` for per-project)
