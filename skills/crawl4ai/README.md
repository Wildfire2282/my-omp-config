# crawl4ai

An [Agent Skill](https://agentskills.io/specification.md) that gives AI assistants
expert-level knowledge of [Crawl4AI](https://docs.crawl4ai.com/) (v0.9.x), the
open-source LLM-friendly web crawler & scraper for Python.

Built by distilling the official Crawl4AI documentation into a progressive-disclosure
skill: a compact `SKILL.md` with copy-paste recipes, decision tables, and gotchas,
plus 27 focused reference files loaded on demand.

## What it covers

- **Core API model** — `AsyncWebCrawler`, `BrowserConfig`, `CrawlerRunConfig`, `LLMConfig` (0.9.x config-object style)
- **8 copy-paste recipes** — basic crawl, fit markdown, CSS/XPath schema extraction, LLM extraction, dynamic pages, multi-URL concurrency, caching, screenshots/PDFs/downloads
- **Structured extraction** — CSS/XPath schemas (nested, `source`), regex, LLM strategies, chunking, table extraction
- **Markdown pipeline** — Pruning / BM25 / LLM content filters, citations, `content_source`
- **Advanced topics** — sessions, hooks & auth, proxies, anti-bot/fallback, lazy loading, virtual scroll, PDF parsing, SSL, identity persistence, dispatchers, network capture
- **Task → configuration decision table** and **15 version-specific gotchas** (0.9.x)

## Structure

```
crawl4ai/
├── SKILL.md                # metadata + core instructions (<350 lines)
├── references/             # 27 focused topic files, loaded on demand
│   ├── installation-cli.md / caching.md / content-options.md / crawl-result.md
│   ├── markdown-generator.md / content-filters.md
│   ├── css-xpath-schema.md / regex-extraction.md / llm-extraction.md / chunking.md / table-extraction.md
│   ├── sessions.md / hooks-auth.md / proxy-security.md / anti-bot.md / dynamic-pages.md
│   ├── pdf-downloads.md / ssl-cert.md / identity.md / multi-url.md / network-capture.md
│   ├── adaptive-crawling.md / advanced-features.md / advanced-gotchas.md
│   └── async-webcrawler.md / strategies.md / c4a-script.md
└── evals/evals.json        # trigger/output eval cases
```

## Installation

Clone the repository and link the folder into omp's user skills directory:

```bash
git clone https://github.com/Wildfire2282/my-omp-config.git ~/workspace/my-omp-config
ln -s ~/workspace/my-omp-config/skills ~/.omp/agent/skills
```

Per-project: link into `<project>/.omp/skills` instead. omp discovers skills as `<skills-root>/<name>/SKILL.md`; restart omp (or reload skills) to pick up new skills.

## Usage

Trigger manually — the skill is not auto-invoked:

```
/skill:crawl4ai
```

## Requirements

- Python 3.9+ with uv: `uv venv && uv pip install "crawl4ai==0.9.2"`, then `uv run crawl4ai-setup` once to install the Playwright Chromium browser (pip inside a venv works as a fallback)
- LLM-based features need an API token (OpenAI, Anthropic, Gemini, DeepSeek, Ollama, ...)

## Source & verification

- Content distilled from the official [Crawl4AI docs](https://docs.crawl4ai.com/) (v0.9.x)
- API names verified against the installed `crawl4ai` 0.9.2 package (30/30 symbols)
- All core recipes smoke-tested against a live crawl
- Validated with `pymarkdownlnt` and rendered with markdown-it (zero structural issues)

## License

MIT — see [LICENSE](LICENSE).
