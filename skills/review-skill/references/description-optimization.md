# Optimizing skill descriptions

A skill only helps if it gets activated. The `description` field is the primary mechanism agents use to decide whether to load a skill. Under-specified → won't trigger when it should; over-broad → triggers when it shouldn't.

## How triggering works

At startup, agents load only `name` + `description` of each available skill — just enough to decide relevance. When a user's task matches, the agent reads the full `SKILL.md`. The description carries the entire burden of triggering. Note: agents typically only consult skills for tasks requiring knowledge beyond what they can handle alone — a simple one-step request may not trigger even a relevant skill.

## Writing effective descriptions

- **Imperative phrasing.** Frame as an instruction: "Use this skill when…" rather than "This skill does…".
- **Focus on user intent, not implementation.** Describe what the user is trying to achieve, not internal mechanics — the agent matches against what the user asked for.
- **Err on the side of being pushy.** Explicitly list contexts where it applies, including cases where the user doesn't name the domain directly: "even if they don't explicitly mention 'CSV' or 'analysis.'"
- **Keep it concise.** A few sentences to a short paragraph. Hard limit: 1024 characters.

Before / after example:

```yaml
# Before
description: Process CSV files.

# After
description: Analyze CSV and tabular data files — compute summary statistics,
  add derived columns, generate charts, and clean messy data. Use this
  skill when the user has a CSV, TSV, or Excel file and wants to
  explore, transform, or visualize the data, even if they don't
  explicitly mention "CSV" or "analysis."
```

## Designing trigger eval queries

~20 queries in `eval_queries.json`: 8-10 should-trigger, 8-10 should-not-trigger, each labeled.

```json
[
  { "query": "I've got a spreadsheet in ~/data/q4_results.xlsx with revenue in col C and expenses in col D — can you add a profit margin column and highlight anything under 10%?", "should_trigger": true },
  { "query": "whats the quickest way to convert this json file to yaml", "should_trigger": false }
]
```

### Should-trigger queries

Vary along several axes:

- **Phrasing**: some formal, some casual, some with typos or abbreviations.
- **Explicitness**: some name the domain directly ("analyze this CSV"), others describe the need without naming it ("my boss wants a chart from this data file").
- **Detail**: mix terse prompts with context-heavy ones (file paths, column names, backstory).
- **Complexity**: single-step tasks alongside multi-step workflows, where the skill-relevant part is buried in a larger chain.

The most useful should-trigger queries are ones where the skill helps but the connection isn't obvious — if the query already asks for exactly what the skill does, any reasonable description would trigger.

### Should-not-trigger queries

The most valuable negatives are **near-misses** — shared keywords/concepts but a different actual need:

- Weak:
  - `"Write a fibonacci function"` — irrelevant, tests nothing.
  - `"What's the weather today?"` — no keyword overlap, too easy.
- Strong:
  - `"I need to update the formulas in my Excel budget spreadsheet"` — shares "spreadsheet", but needs Excel editing, not CSV analysis.
  - `"can you write a python script that reads a csv and uploads each row to our postgres database"` — involves CSV, but it's database ETL, not analysis.

### Realism

Real prompts contain file paths (`~/Downloads/report_final_v2.xlsx`), personal context ("my manager asked me to…"), specific details, casual language, abbreviations, occasional typos.

## Testing whether a description triggers

Run each query through the agent with the skill installed; check logs/tool-call history whether the skill's `SKILL.md` was consulted. Pass = `should_trigger` matches whether the skill was invoked.

### Multiple runs

Model behavior is nondeterministic — run each query 3× (reasonable starting point) and compute **trigger rate** = fraction of runs where the skill was invoked. A should-trigger query passes above a threshold (0.5 default); a should-not-trigger query passes below it. ~20 queries × 3 runs = 60 invocations — script this.

Stop a run early once the outcome is clear (the agent either consulted the skill or started working without it) to save time/cost.

## Avoiding overfitting: train/validation splits

Optimizing against all queries risks overfitting to specific phrasings. Split:

- **Train set (~60%)** — used to identify failures and guide improvements.
- **Validation set (~40%)** — set aside, only used to check whether improvements generalize.

Both sets need proportional mixes of positives/negatives. Shuffle randomly, keep the split fixed across iterations. Run the eval script against each file separately.

## The optimization loop

1. **Evaluate** the current description on both train and validation sets.
2. **Identify failures** in the train set: which should-trigger queries didn't trigger? Which should-not-trigger queries did? Keep validation results out of the revision process.
3. **Revise the description**, focusing on generalizing:
   - Should-trigger failing → too narrow. Broaden scope or add context about when it's useful.
   - Should-not-trigger false-triggering → too broad. Add specificity about what it does *not* do, or clarify the boundary with adjacent capabilities.
   - Avoid adding specific keywords from failed queries — that's overfitting. Address the general category the queries represent.
   - Stuck after several iterations → try a structurally different framing rather than incremental tweaks.
   - Stay under 1024 characters — descriptions grow during optimization.
4. **Repeat** until all train queries pass or improvement plateaus.
5. **Select the best iteration** by validation pass rate — may not be the last one (later iterations can overfit to train).

Five iterations is usually enough. If performance isn't improving, the issue may be the queries (too easy/hard/poorly labeled), not the description.

## Applying the result

1. Update `description` in `SKILL.md` frontmatter.
2. Verify under 1024 chars.
3. Sanity-check with a few manual prompts; for rigor, write 5-10 fresh queries (never part of optimization) and run them through the eval script.

## Sources

Synthesized from the Agent Skills documentation on optimizing skill descriptions (agentskills.io/skill-creation/optimizing-descriptions).
