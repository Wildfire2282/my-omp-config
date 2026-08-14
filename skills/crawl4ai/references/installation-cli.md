# Installation & CLI

Read when the user needs to install Crawl4AI, run `crawl4ai-setup`, or use the `crwl` command-line tool.

## Installation

```bash
uv venv                                   # project-isolated environment (.venv)
uv pip install "crawl4ai==0.9.2"          # pin to the API this skill documents
uv run crawl4ai-setup                     # REQUIRED once: installs Playwright Chromium
uv run crawl4ai-doctor                    # diagnostics (optional)
```

- All code examples in this skill run under `uv run` (or `.venv/bin/python`) inside
  the same environment that installed Crawl4AI.
- No uv installed? Fall back to `python -m venv .venv && .venv/bin/pip install
  "crawl4ai==0.9.2"` — same isolation, same pin. Avoid global `pip install`:
  it pollutes the system interpreter and leaves the version unpinned.
- To upgrade: bump the version pin, then verify the API against this skill's docs —
  the 0.9.x→next-major API is not backward compatible.
- Async-first: run all code under `asyncio.run(main())` or an event loop.
- Heavy optional deps (torch, transformers) are NOT installed by default — install only if needed.

## CLI (`crwl`)

The CLI ships with the library:

```bash
crwl https://example.com                    # default: all output
crwl https://example.com -o markdown        # raw markdown
crwl https://example.com -o markdown-fit    # filtered markdown
crwl https://example.com -o json -v --bypass-cache

# Browser config file / inline params
crwl https://example.com -B browser.yml
crwl https://example.com -b "headless=true,viewport_width=1280,user_agent_mode=random"

# Crawler config
crwl https://example.com -C crawler.yml
crwl https://example.com -c "css_selector=#main,scan_full_page=true"

# Structured extraction (YAML strategy + JSON schema)
crwl https://example.com -e extract_css.yml -s css_schema.json -o json
crwl https://example.com -e extract_llm.yml -s llm_schema.json -o json

# Content filtering
crwl https://example.com -f filter_bm25.yml -o markdown-fit

# LLM Q&A over crawled content
crwl https://example.com -q "Summarize the key points"

crwl --example  # usage examples
```

- Output formats: `all`, `json`, `markdown`/`md`, `markdown-fit`/`md-fit`.
- First `-q` run prompts for LLM provider/token, saved to `~/.crawl4ai/global.yml`.
