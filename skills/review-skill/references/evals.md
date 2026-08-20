# Evaluating skill output quality

Structured evals answer: does the skill work reliably — across varied prompts, in edge cases, better than no skill at all?

## Designing test cases

Three parts per test case:

- **Prompt**: a realistic user message — what someone would actually type.
- **Expected output**: human-readable description of what success looks like.
- **Input files** (optional): files the skill needs to work with.

Store in `evals/evals.json` inside the skill directory. One schema for every skill (see `references/standard.md` §5): top-level `skill_name` + `evals`, integer ids from 1, and every case carries `prompt`, `expected_output`, and `assertions`:

```json
{
  "skill_name": "csv-analyzer",
  "evals": [
    {
      "id": 1,
      "prompt": "I have a CSV of monthly sales data in data/sales_2025.csv. Can you find the top 3 months by revenue and make a bar chart?",
      "expected_output": "A bar chart image showing the top 3 months by revenue, with labeled axes and values.",
      "assertions": [
        "The output includes a chart image file",
        "The chart shows exactly the top 3 months by revenue",
        "Both axes are labeled"
      ],
      "files": ["evals/files/sales_2025.csv"]
    },
    {
      "id": 2,
      "prompt": "there's a csv in my downloads called customers.csv, some rows have missing emails — can you clean it up and tell me how many were missing?",
      "expected_output": "A cleaned CSV with missing emails handled, plus a count of how many were missing.",
      "assertions": [
        "The output CSV has no empty email cells",
        "The answer states how many rows were missing emails"
      ],
      "files": ["evals/files/customers.csv"]
    }
  ]
}
```

Tips:

- **Start with 2-3 test cases.** Expand after seeing the first round of results.
- **Vary the prompts** — phrasing, detail, formality (casual and precise).
- **Cover edge cases** — at least one boundary condition: malformed input, unusual request, ambiguous instructions.
- **Include a negative control** — a prompt the skill should NOT be needed for — with assertions that verify the answer stays skill-free (e.g. "The answer does not introduce skill-specific API calls").
- **Use realistic context** — file paths, column names, personal context. "Process this data" tests nothing.

Write initial `assertions` when authoring the cases; they are part of the schema. Expect to refine them after the first run — you often don't know what "good" looks like until the skill has run.

## Running evals

Run each test case **twice**: with the skill and without (baseline). For improvements to an existing skill, snapshot it first and use the old version as the baseline.

### Workspace structure

```text
csv-analyzer/
├── SKILL.md
└── evals/
    └── evals.json
csv-analyzer-workspace/
└── iteration-1/
    ├── eval-top-months-chart/
    │   ├── with_skill/
    │   │   ├── outputs/
    │   │   ├── timing.json      # {"total_tokens": 84852, "duration_ms": 23332}
    │   │   └── grading.json     # assertion results
    │   └── without_skill/
    │       ├── outputs/
    │       ├── timing.json
    │       └── grading.json
    ├── eval-clean-missing-emails/
    │   └── ... (same layout)
    └── benchmark.json            # aggregated statistics
```

`evals/evals.json` is authored by hand; `grading.json`, `timing.json`, `benchmark.json` are produced during the eval process.

### Spawning runs

Each run starts with a **clean context** — no leftover state. Use subagents (each starts fresh) or separate sessions. Provide: the skill path (or none for baseline), the test prompt, any input files, the output directory.

When a run completes, record token count and duration into `timing.json` immediately — they aren't persisted anywhere else.

## Writing assertions

Verifiable statements about what the output should contain or achieve. Add after seeing first outputs — you often don't know what "good" looks like until the skill has run.

Good:

- "The output file is valid JSON" — programmatically verifiable
- "The bar chart has labeled axes" — specific and observable
- "The report includes at least 3 recommendations" — countable

Weak:

- "The output is good" — too vague
- "The output uses exactly the phrase 'Total Revenue: $X'" — too brittle

Reserve assertions for objectively checkable things. Style, visual design, "feels right" → human review instead.

## Grading outputs

Evaluate each assertion against actual outputs: **PASS/FAIL with concrete evidence** — quote or reference the output, don't state an opinion. Use a verification script for code-checkable assertions (valid JSON, row counts, file existence) — more reliable than LLM judgment and reusable.

```json
{
  "assertion_results": [
    { "text": "The output includes a bar chart image file", "passed": true, "evidence": "Found chart.png (45KB) in outputs directory" },
    { "text": "Both axes are labeled", "passed": false, "evidence": "Y-axis is labeled 'Revenue ($)' but X-axis has no label" }
  ],
  "summary": { "passed": 3, "failed": 1, "total": 4, "pass_rate": 0.75 }
}
```

Grading principles:

- **Require concrete evidence for PASS.** A section titled "Summary" with one vague sentence is a FAIL.
- **Review the assertions themselves** while grading — too easy, too hard, or unverifiable ones get fixed next iteration.

For comparing versions, try **blind comparison**: present both outputs to an LLM judge without revealing which is which; judge holistic qualities (organization, formatting, usability, polish) on its own rubric.

## Aggregating results

Compute summary statistics per configuration into `benchmark.json`:

```json
{
  "run_summary": {
    "with_skill":    { "pass_rate": { "mean": 0.83, "stddev": 0.06 }, "time_seconds": { "mean": 45.0 }, "tokens": { "mean": 3800 } },
    "without_skill": { "pass_rate": { "mean": 0.33, "stddev": 0.10 }, "time_seconds": { "mean": 32.0 }, "tokens": { "mean": 2100 } },
    "delta": { "pass_rate": 0.50, "time_seconds": 13.0, "tokens": 1700 }
  }
}
```

The `delta` shows what the skill costs (time/tokens) and buys (pass rate). +13s for +50pp pass rate is probably worth it; 2× tokens for +2pp probably isn't. With few test cases and single runs, focus on raw pass counts and delta — stddev only becomes meaningful with multiple runs per eval.

## Analyzing patterns

- **Remove/replace assertions that always pass in both configs** — they inflate with-skill pass rate without reflecting value.
- **Investigate assertions that always fail in both** — broken assertion, too-hard test case, or wrong check.
- **Study assertions that pass with the skill but fail without** — this is where the skill adds value. Understand *why*.
- **Tighten instructions when results are inconsistent across runs** — ambiguous instructions get interpreted differently each time; add examples or more specific guidance.
- **Check time/token outliers** — read the execution transcript to find the bottleneck.

## Reviewing results with a human

Assertion grading only checks what you thought to write assertions for. A human reviewer catches unanticipated issues, "technically correct but misses the point" outputs, and qualities hard to express as pass/fail. Record specific, actionable feedback per test case in `feedback.json` ("The chart is missing axis labels and months are in alphabetical order instead of chronological" — not "looks bad"). Empty feedback = test case passed review.

## Iterating on the skill

Three sources of signal:

- **Failed assertions** → specific gaps (missing step, unclear instruction, unhandled case).
- **Human feedback** → broader quality issues.
- **Execution transcripts** → *why* things went wrong (ignored instructions, unproductive steps).

Give all three plus the current `SKILL.md` to an LLM and ask for proposed changes. Guidelines for that prompt:

- **Generalize from feedback.** Fixes address underlying issues broadly, not narrow patches for specific examples.
- **Keep the skill lean.** Fewer, better instructions outperform exhaustive rules. If transcripts show wasted work, remove those instructions. Plateau despite more rules → may be over-constrained; try removing and see if results hold.
- **Explain the why.** "Do X because Y tends to cause Z" works better than "ALWAYS do X, NEVER do Y".
- **Bundle repeated work.** If every run independently wrote a similar helper script, bundle it into `scripts/`.

### The loop

1. Give eval signals + current `SKILL.md` to an LLM → proposed improvements.
2. Review and apply the changes.
3. Rerun all test cases in a new `iteration-<N+1>/` directory.
4. Grade and aggregate.
5. Review with a human. Repeat.

Stop when satisfied, feedback is consistently empty, or improvement plateaus.

## Sources

Synthesized from the Agent Skills documentation on evaluating skill output quality (agentskills.io/skill-creation/evaluating-skills).
