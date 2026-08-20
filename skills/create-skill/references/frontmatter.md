# SKILL.md frontmatter reference

The `SKILL.md` file must contain YAML frontmatter followed by Markdown content.

## Frontmatter fields

| Field | Required | Constraints |
| --- | --- | --- |
| `name` | Yes | 1-64 chars. Lowercase letters, numbers, hyphens only. No leading/trailing/consecutive hyphens. Must match the parent directory name. |
| `description` | Yes | 1-1024 chars. Non-empty. Describes what the skill does and when to use it. |
| `license` | Yes | `MIT` for this repository's skills. Must match the bundled `LICENSE` file. |
| `disable-model-invocation` | Yes | `true`. Manual trigger only — invoked via `/skill:<name>`; the model never auto-invokes it. |
| `compatibility` | No | Max 500 chars. Environment requirements (intended product, system packages, network access, etc.). |
| `metadata` | Yes | Must include `author` and `author-url` (see Attribution below); arbitrary extra keys allowed. |
| `allowed-tools` | No | Space-separated string of pre-approved tools the skill may use. Experimental. |

## `name` — valid vs invalid

```yaml
name: pdf-processing   # valid
name: data-analysis    # valid
name: code-review      # valid
```

```yaml
name: PDF-Processing    # invalid: uppercase not allowed
name: -pdf              # invalid: cannot start with hyphen
name: pdf--processing   # invalid: consecutive hyphens
name: pdf-              # invalid: cannot end with hyphen
```

`name` must match the directory name. `skill-name/` directory → `name: skill-name`.

## `description`

- Must be 1-1024 characters.
- Should describe both **what the skill does** and **when to use it**.
- Should include specific keywords that help agents identify relevant tasks.

Good:

```yaml
description: Extracts text and tables from PDF files, fills PDF forms, and merges multiple PDFs. Use when working with PDF documents or when the user mentions PDFs, forms, or document extraction.
```

Poor:

```yaml
description: Helps with PDFs.
```

## `compatibility` examples

Only include when the skill has specific environment requirements. Most skills don't need it.

```yaml
compatibility: Designed for Oh My Pi (omp)
compatibility: Requires git, docker, jq, and access to the internet
compatibility: Requires Python 3.14+ and uv
```

## License & attribution (required)

The authoritative rules, the MIT `LICENSE` template, and the three-way consistency requirements live in `references/standard.md` §4. Summary:

- Frontmatter declares `license: MIT`.
- The skill directory contains a `LICENSE` file with the standard MIT text.
- The LICENSE copyright line matches `metadata.author`.
- `metadata.author` is the GitHub username (no `@` prefix, no URL); `metadata.author-url` is `https://github.com/<author>`.
- If the skill ships a `README.md`, end it with:

```markdown
## License

MIT — see [LICENSE](LICENSE).
```

## Minimal and full examples

```yaml
---
name: roll-dice
description: Roll dice using a random number generator. Use when asked to roll a die (d6, d20, etc.), roll dice, or generate a random dice roll.
license: MIT
metadata:
  author: your-github-username
  author-url: https://github.com/your-github-username
---
```

```yaml
---
name: pdf-processing
description: Extract PDF text, fill forms, merge files. Use when handling PDFs.
license: MIT
compatibility: Requires Python 3.14+ and uv
metadata:
  author: your-github-username
  author-url: https://github.com/your-github-username
  version: "1.0"
---
```

The same skill directory also contains a `LICENSE` file (see License above).

## Body content

The Markdown body after the frontmatter contains the skill instructions. No format restrictions — write whatever helps agents perform the task. Recommended sections:

- Step-by-step instructions
- Examples of inputs and outputs
- Common edge cases

The agent loads the **entire** body once the skill is activated, so keep it lean and move longer material to referenced files.

## Optional directories

- `scripts/` — executable code. Self-contained or clearly document dependencies; include helpful error messages; handle edge cases gracefully. Common languages: Python, Bash, JavaScript (support varies by agent).
- `references/` — additional docs loaded on demand (`REFERENCE.md`, `FORMS.md`, domain files). Keep each file focused — smaller files mean less context use.
- `assets/` — static resources: templates, images, data files (lookup tables, schemas).

## File references

Use relative paths from the skill root, one level deep from `SKILL.md`:

```markdown
See [the reference guide](references/REFERENCE.md) for details.

Run the extraction script:
scripts/extract.py
```

Avoid deeply nested reference chains.

## Progressive disclosure

1. **Metadata** (~100 tokens): `name` + `description` loaded at startup for all skills.
2. **Instructions** (<5000 tokens recommended): full `SKILL.md` body loaded on activation.
3. **Resources** (as needed): files in `scripts/`, `references/`, `assets/` loaded only when required.

Keep `SKILL.md` under 500 lines. Move detailed reference material to separate files, and tell the agent *when* to load each one.
