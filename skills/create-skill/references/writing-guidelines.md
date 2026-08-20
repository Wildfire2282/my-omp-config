# Writing guidelines for skill instructions

Principles for the `SKILL.md` body — what to include, what to cut, how to phrase it.

## Spending context wisely

Once a skill activates, its full body loads into the agent's context alongside conversation history, system context, and other active skills. Every token competes for attention.

### Add what the agent lacks, omit what it knows

Focus on what the agent *wouldn't* know without the skill: project-specific conventions, domain-specific procedures, non-obvious edge cases, particular tools or APIs. Don't explain what a PDF is, how HTTP works, or what a database migration does.

```markdown
<!-- Too verbose — the agent already knows what PDFs are -->
## Extract PDF text

PDF (Portable Document Format) files are a common file format that contains
text, images, and other content. To extract text from a PDF, you'll need to
use a library. pdfplumber is recommended because it handles most cases well.

<!-- Better — jumps straight to what the agent wouldn't know on its own -->
## Extract PDF text

Use pdfplumber for text extraction. For scanned documents, fall back to
pdf2image with pytesseract.
```

Ask about each piece: "Would the agent get this wrong without this instruction?" If no, cut it. If unsure, test it.

### Design coherent units

A skill should encapsulate a coherent unit of work that composes well with other skills — like a well-scoped function. Too narrow → multiple skills load for one task (overhead, conflicting instructions). Too broad → hard to activate precisely. Querying a database and formatting results may be one unit; also covering database administration is too much.

### Aim for moderate detail

Concise, stepwise guidance with a working example outperforms exhaustive documentation. The agent struggles to extract what's relevant from a comprehensive doc and may pursue unproductive paths triggered by instructions that don't apply. When covering every edge case, consider whether most are better handled by the agent's judgment.

### Structure large skills with progressive disclosure

Keep `SKILL.md` under 500 lines and ~5000 tokens — just the core instructions needed on every run. Move detail to `references/` and tell the agent *when* to load each file: "Read `references/api-errors.md` if the API returns a non-200 status code" is more useful than "see references for details."

## Write in English

All skill content must be English: `SKILL.md`, frontmatter values, `references/`, `assets/`, and comments/help text in bundled scripts. The skill is a stable, shared artifact — one language keeps instructions internally consistent, avoids mixed-language drift, and works for any user regardless of what language they ask in.

```markdown
<!-- Bad: skill written in the user's language -->
## 提取 PDF 文本
用 pdfplumber 提取文本。扫描件用 pdf2image + pytesseract。

<!-- Good: instructions stay English regardless of user language -->
## Extract PDF text
Use pdfplumber for text extraction. For scanned documents, fall back to
pdf2image with pytesseract.
```

The rule applies to the skill's *instructions*, not to what the skill *produces*: if a skill writes output in the user's language (e.g. localized marketing copy), that output may follow the user's language — the skill's own content stays English.

## Calibrating control

Not every part needs the same prescriptiveness. Match specificity to the fragility of the task.

### Give freedom where variation is harmless

When multiple approaches are valid, describe *why* rather than issuing rigid directives. An agent that understands the purpose behind an instruction makes better context-dependent decisions.

```markdown
## Code review process

1. Check all database queries for SQL injection (use parameterized queries)
2. Verify authentication checks on every endpoint
3. Look for race conditions in concurrent code paths
4. Confirm error messages don't leak internal details
```

### Be prescriptive where operations are fragile

When consistency matters or a specific sequence must be followed:

````markdown
## Database migration

Run exactly this sequence:

```bash
python scripts/migrate.py --verify --backup
```

Do not modify the command or add additional flags.
````

Most skills have a mix — calibrate each part independently.

### Provide defaults, not menus

Pick a default and mention alternatives briefly rather than presenting equal options:

```markdown
<!-- Too many options -->
You can use pypdf, pdfplumber, PyMuPDF, or pdf2image...

<!-- Clear default with escape hatch -->
Use pdfplumber for text extraction. For scanned PDFs requiring OCR,
use pdf2image with pytesseract instead.
```

### Favor procedures over declarations

Teach *how to approach a class of problems*, not *what to produce for one instance*:

```markdown
<!-- Specific answer — only useful for this exact task -->
Join the `orders` table to `customers` on `customer_id`, filter where
`region = 'EMEA'`, and sum the `amount` column.

<!-- Reusable method — works for any analytical query -->
1. Read the schema from `references/schema.yaml` to find relevant tables
2. Join tables using the `_id` foreign key convention
3. Apply any filters from the user's request as WHERE clauses
4. Aggregate numeric columns as needed and format as a markdown table
```

Specific details are fine — output templates, constraints ("never output PII"), tool-specific instructions. The *approach* must generalize.

## Instruction patterns

Reusable techniques; use the ones that fit the task.

### Gotchas sections

The highest-value content in many skills: environment-specific facts that defy reasonable assumptions — concrete corrections to mistakes the agent will make without being told.

```markdown
## Gotchas

- The `users` table uses soft deletes. Queries must include
  `WHERE deleted_at IS NULL` or results will include deactivated accounts.
- The user ID is `user_id` in the database, `uid` in the auth service,
  and `accountId` in the billing API. All three refer to the same value.
- The `/health` endpoint returns 200 even if the database is down.
  Use `/ready` to check full service health.
```

Keep gotchas in `SKILL.md`, where the agent reads them *before* hitting the situation. When an agent makes a mistake you have to correct, add the correction to the gotchas — one of the most direct ways to improve a skill iteratively.

### Templates for output format

Provide a concrete template when output must be in a specific format — agents pattern-match well against structures. Keep short templates inline in `SKILL.md`; store long or rarely used ones in `assets/` and reference them from `SKILL.md`.

### Checklists for multi-step workflows

Explicit checklists help the agent track progress and avoid skipping steps, especially when steps have dependencies or validation gates.

```markdown
## Form processing workflow

Progress:
- [ ] Step 1: Analyze the form (run `scripts/analyze_form.py`)
- [ ] Step 2: Create field mapping (edit `fields.json`)
- [ ] Step 3: Validate mapping (run `scripts/validate_fields.py`)
- [ ] Step 4: Fill the form (run `scripts/fill_form.py`)
- [ ] Step 5: Verify output (run `scripts/verify_output.py`)
```

### Validation loops

Do the work, run a validator (script, reference checklist, or self-check), fix issues, repeat until validation passes.

```markdown
## Editing workflow

1. Make your edits
2. Run validation: `python scripts/validate.py output/`
3. If validation fails:
   - Review the error message
   - Fix the issues
   - Run validation again
4. Only proceed when validation passes
```

### Plan-validate-execute

For batch or destructive operations: create an intermediate plan in structured format, validate it against a source of truth, then execute. The key ingredient is a validation script that checks the plan against the source of truth and produces errors actionable enough for the agent to self-correct ("Field 'signature_date' not found — available fields: customer_name, order_total, signature_date_signed").

### Bundle repeated work

If execution traces show the agent reinventing the same logic each run (building charts, parsing a format, validating output), write a tested script once and bundle it in `scripts/`. See `references/scripts.md`.

## Sources

Synthesized from the Agent Skills documentation on best practices for skill creators (agentskills.io/skill-creation/best-practices).
