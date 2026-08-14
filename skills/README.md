# my-skills

A collection of [Agent Skills](https://agentskills.io) for Oh My Pi (omp), the AI coding harness.

- **create-agent-skill/** — create, validate, and improve Agent Skills (SKILL.md format)
- **crawl4ai/** — scrape and extract structured data from websites with Crawl4AI
- **github-cli/** — operate GitHub from the command line with the official GitHub CLI
- **python-verify-loop/** — external layered verification and fix loop for Python code changes (Ruff, Pyright, pytest, Bandit, git, architecture rules)
- **svgjs/** — create, manipulate, and animate SVG with SVG.js v3
- **userscript/** — write, debug, and enhance userscripts (Tampermonkey, ScriptCat, …)

Each directory is a complete skill: a spec-compliant `SKILL.md` plus optional `references/` and `evals/`. Copy one into omp's skills directory — `~/.omp/agent/skills/` (user-wide) or `<project>/.omp/skills/` (per-project) — and it is ready to use.

The skill standard — naming, structure, frontmatter, licensing, attribution, README, and evals — is defined inside the `create-agent-skill` skill: `create-agent-skill/references/standard.md`.
