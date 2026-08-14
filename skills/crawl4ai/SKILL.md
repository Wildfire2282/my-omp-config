---
name: crawl4ai
description: >-
  Use this skill when the user wants to scrape, crawl, or extract data from
  websites with Crawl4AI: fetch pages, convert HTML to clean Markdown for
  LLM/RAG pipelines, filter boilerplate, extract structured JSON (CSS,
  XPath, regex, or LLM strategies), handle dynamic pages and anti-bot
  measures, reuse sessions, or run concurrent crawls. Activate even when
  Crawl4AI is not named — e.g. "scrape this site", "convert this page to
  markdown", "extract all prices from this listing". Do not use for simple
  HTTP GET requests that standard tools already handle.
license: MIT
disable-model-invocation: true
compatibility: >-
  Requires Python 3.9+ with uv. Create a project virtual environment and pin
  the 0.9.x line: `uv pip install "crawl4ai==0.9.2"`, then run
  `uv run crawl4ai-setup` once to install the Playwright Chromium browser
  (pip inside a venv works as a fallback). LLM-based features need an API
  token (OpenAI, Anthropic, Gemini, DeepSeek, Ollama, etc.).
metadata:
  author: Wildfire2282
  author-url: https://github.com/Wildfire2282
  version: "1.0"
---

# Crawl4AI

Crawl4AI is an open-source, LLM-friendly **async** web crawler & scraper for Python.
It launches a headless browser (Chromium by default), converts HTML to clean Markdown,
and extracts structured JSON via CSS/XPath schemas or LLM strategies.

This skill knows the **0.9.x API**. If the user's installed version differs, verify
against `uv pip show crawl4ai` and read the matching docs.

## Core API model

Three objects do almost everything:

- `AsyncWebCrawler` — the crawler. `async with AsyncWebCrawler(config=browser_cfg) as crawler:`.
- `BrowserConfig` — how the **browser** behaves (headless, viewport, proxy, user agent, stealth).
- `CrawlerRunConfig` — how each **crawl** behaves (caching, filters, JS, waits, extraction, screenshot…).
- `LLMConfig` — LLM provider for `LLMExtractionStrategy`, `LLMContentFilter`, schema generation.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

async def main():
    browser_conf = BrowserConfig(headless=True)
    run_conf = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
    async with AsyncWebCrawler(config=browser_conf) as crawler:
        result = await crawler.arun(url="https://example.com", config=run_conf)
        print(result.markdown)  # MarkdownGenerationResult, not str — see below

asyncio.run(main())
```

> **0.9.x rule:** configuration objects go into `CrawlerRunConfig`; do **not** pass
> `extraction_strategy`, `markdown_generator`, `cache_mode`, `css_selector` etc. as
> direct `arun()` arguments.

## Installation & first run

```bash
uv venv                                    # project-isolated environment (.venv)
uv pip install "crawl4ai==0.9.2"           # pin to the API this skill documents
uv run crawl4ai-setup                      # installs Playwright Chromium (required once)
uv run crawl4ai-doctor                     # optional diagnostics
```

- Every example in this skill runs with `uv run` (or `.venv/bin/python`) — the
  script must use the same environment that installed Crawl4AI.
- Without `crawl4ai-setup`, the browser is missing and every crawl fails.
- No uv? Fall back to `python -m venv .venv && .venv/bin/pip install "crawl4ai==0.9.2"`,
  then `.venv/bin/crawl4ai-setup`. Never global-install: it pollutes the system
  interpreter and leaves the version unpinned.
- CLI tool: `crwl https://example.com -o markdown` (see `references/installation-cli.md` for CLI flags).

## Core patterns (copy-paste recipes)

### 1. Basic crawl → Markdown

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://example.com", config=CrawlerRunConfig())
        if result.success:
            md = result.markdown
            print(md.raw_markdown[:500])   # full HTML→Markdown
        else:
            print("failed:", result.error_message)

asyncio.run(main())
```

`result.markdown` is a `MarkdownGenerationResult` (not a plain string). Use
`.raw_markdown`, `.fit_markdown`, `.markdown_with_citations`, `.references_markdown`, `.fit_html`.

### 2. Fit Markdown (filter out boilerplate)

- `PruningContentFilter` — no query needed, heuristics (text/link density).
- `BM25ContentFilter` — user has a search query.
- `LLMContentFilter` — LLM-based extraction of the meaningful content.

```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import PruningContentFilter

config = CrawlerRunConfig(
    markdown_generator=DefaultMarkdownGenerator(
        content_filter=PruningContentFilter(threshold=0.48, threshold_type="dynamic"),
        options={"ignore_links": True},   # common options below
    )
)
# result.markdown.fit_markdown  ← filtered content
```

Common `DefaultMarkdownGenerator` options: `ignore_links`, `ignore_images`,
`escape_html`, `body_width`, `skip_internal_links`, `include_sup_sub`.
`content_source` selects input HTML: `"cleaned_html"` (default), `"raw_html"`, `"fit_html"`.

### 3. Structured extraction without LLM (preferred when structure is regular)

```python
import json
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, JsonCssExtractionStrategy

schema = {
    "name": "Items",
    "baseSelector": "div.item",
    "fields": [
        {"name": "title", "selector": "h2", "type": "text"},
        {"name": "link", "selector": "a", "type": "attribute", "attribute": "href"},
    ],
}
config = CrawlerRunConfig(extraction_strategy=JsonCssExtractionStrategy(schema))
async with AsyncWebCrawler() as crawler:
    result = await crawler.arun("https://example.com/list", config=config)
    data = json.loads(result.extracted_content)  # JSON string → list[dict]
```

- XPath variant: `JsonXPathExtractionStrategy` (baseSelector/selector use XPath).
- Schema types: `"text"`, `"attribute"`, `"html"`, `"regex"`, `"nested"` (one sub-object),
  `"list"` (simple items), `"nested_list"` (repeated complex objects), plus `"baseFields"`
  and optional `transform` / `default`. Full schema reference: `references/css-xpath-schema.md`.
- LLM can generate the schema once: `JsonCssExtractionStrategy.generate_schema(html, llm_config=...)`.
- `regex` extraction: `RegexExtractionStrategy`.

### 4. Structured extraction with LLM (irregular / semantic content)

```python
from pydantic import BaseModel
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, LLMConfig, LLMExtractionStrategy

class Product(BaseModel):
    name: str
    price: str

config = CrawlerRunConfig(
    extraction_strategy=LLMExtractionStrategy(
        llm_config=LLMConfig(provider="openai/gpt-4o-mini", api_token="..."),  # or env:VAR
        schema=Product.model_json_schema(),
        extraction_type="schema",          # or "block"
        instruction="Extract all products with name and price.",
        input_format="markdown",           # "markdown" | "html" | "fit_markdown"
        chunk_token_threshold=1000,        # split large pages
        overlap_rate=0.1,
        apply_chunking=True,
        extra_args={"temperature": 0.0},
    ),
)
# result.extracted_content → JSON string; call strategy.show_usage() for token stats
```

- Providers follow LiteLLM naming: `"openai/gpt-4o"`, `"ollama/llama3.3"`, `"anthropic/claude-3-5-sonnet-..."`, `"gemini/gemini-2.0-flash"`, `"deepseek/deepseek-chat"`.
- `api_token=None` works for local models (Ollama); otherwise pass token or use `"env:VAR_NAME"`.
- Prefer CSS/XPath schema extraction for repetitive pages — faster, cheaper, deterministic.

### 5. Dynamic pages (JS, infinite scroll, virtual lists)

```python
config = CrawlerRunConfig(
    js_code="document.querySelector('#load-more')?.click();",  # run after page load
    wait_for="css:.item:nth-child(20)",                        # "css:" or "js:" prefix
    scan_full_page=True,        # auto-scroll for APPENDED content (infinite scroll)
    scroll_delay=0.3,
    delay_before_return_html=0.5,
    process_iframes=True,
    remove_overlay_elements=True,   # popups/modals
    remove_consent_popups=True,     # GDPR/cookie banners
)
```

- Virtual scrolling (content **replaced**, e.g. Twitter/Instagram): use
  `virtual_scroll_config=VirtualScrollConfig(container_selector="#timeline", scroll_count=30, ...)`
  instead of `scan_full_page`. Details: `references/dynamic-pages.md`.
- Shadow DOM sites: `flatten_shadow_dom=True`.
- Reuse a loaded page: keep `session_id="s1"` and set `js_only=True` on later calls
  (no full reload) — see Sessions below.

### 6. Multiple URLs in parallel

```python
config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, stream=True)
async with AsyncWebCrawler() as crawler:
    async for result in await crawler.arun_many(urls, config=config):
        if result.success:
            print(result.url, len(result.markdown.raw_markdown))
```

- `stream=True` yields results as they finish; default waits for all.
- Concurrency control: `semaphore_count` (default 5) in `CrawlerRunConfig`, or a
  `MemoryAdaptiveDispatcher`/`SemaphoreDispatcher`/`RateLimiter` — see `references/multi-url.md`.
- Per-URL configs: `url_matcher="*.pdf"` etc. (first matching config wins; add a default config last).

### 7. Caching

```python
from crawl4ai import CacheMode
# CacheMode.ENABLED (read/write) | DISABLED | READ_ONLY | WRITE_ONLY | BYPASS
config = CrawlerRunConfig(cache_mode=CacheMode.ENABLED)
```

- Set explicitly — do not rely on the default (docs disagree between BYPASS and ENABLED).
- Legacy booleans (`bypass_cache`, `disable_cache`, …) are deprecated.

### 8. Screenshots, PDFs, downloads

```python
config = CrawlerRunConfig(
    screenshot=True,                    # → result.screenshot (base64)
    pdf=True,                           # → result.pdf (bytes)
    capture_mhtml=True,                 # → result.mhtml
    accept_downloads=True, downloads_path="/tmp/dl",   # → result.downloaded_files
)
```

- Crawl a PDF file itself: `scraping_strategy=PDFContentScrapingStrategy()` plus
  `url_matcher="*.pdf"` (see `references/pdf-downloads.md`).
- SSL info: `fetch_ssl_certificate=True` → `result.ssl_certificate`.

## Task → configuration decision guide

| User need | What to configure |
|---|---|
| Just clean text from a page | `CrawlerRunConfig()` + read `result.markdown.raw_markdown` |
| Remove nav/ads/boilerplate | `PruningContentFilter` in markdown generator |
| Only content matching a topic | `BM25ContentFilter(user_query=...)` |
| Extract repeated items (products, listings) | `JsonCssExtractionStrategy(schema)` |
| Irregular/semantic extraction | `LLMExtractionStrategy` with Pydantic schema |
| Page renders via JS / needs clicks | `js_code`, `wait_for`, `scan_full_page`, `process_iframes` |
| Infinite scroll (append) | `scan_full_page=True` |
| Replaced-content feeds (Twitter) | `virtual_scroll_config` |
| Many pages | `arun_many(..., stream=True)` + dispatcher/semaphore |
| Same logged-in session across calls | `session_id` (and `js_only=True` for later steps) |
| Site blocks bots | `user_agent_mode="random"`, `enable_stealth`, proxies, retries |
| Reuse cookies/profiles across runs | `use_persistent_context=True`, `user_data_dir`, `storage_state` |
| Respect robots.txt | `check_robots_txt=True`, `user_agent="MyBot/1.0"` |
| Answer a research question over a site | `AdaptiveCrawler` + `digest(start_url, query)` |
| Pass raw HTML without a URL | `url="raw://<html>"` |

## Gotchas (0.9.x)

- **Config goes in `CrawlerRunConfig`.** Direct kwargs on `arun()` for extraction,
  caching, filters, screenshots etc. are gone/deprecated in 0.9.x.
- **`result.markdown` is an object**, not a string: use `.raw_markdown` / `.fit_markdown`.
  `fit_markdown` exists **only** if a content filter was configured.
- **`result.extracted_content` is a JSON string** — always `json.loads()` it.
- **Default cache mode is ambiguous** across docs (BYPASS vs ENABLED). Always set `cache_mode` explicitly.
- **`crawl4ai-setup` is mandatory** after installing (run it inside the same venv as the install) or the browser is missing.
- **`raw://` prefix** feeds raw HTML directly, no network: `arun("raw://<html>", ...)`.
- **LLM features need `LLMConfig`** (`provider` + `api_token`), used by
  `LLMExtractionStrategy`, `LLMContentFilter`, and `generate_schema`.
- **Provider strings are LiteLLM-style** `"provider/model"` — not plain model names.
- **`enable_stealth` cannot combine with `browser_mode="builtin"`**.
- **`css_selector` keeps only the matching region** for the whole pipeline (use
  `target_elements` to focus markdown/extraction while still collecting links/media).
- **Large pages**: raise `page_timeout` (default 60s) and/or `word_count_threshold`
  (default ~200) when content is heavy or slow.
- **Wait conditions** need a prefix: `wait_for="css:.sel"` or `wait_for="js:() => bool"`.
- **`wait_for` waits for a *visible* element** — a selector matching only hidden nodes
  (e.g. `css:title`, which lives in `<head>`) times out even though the element exists.
  Wait for visible content (`css:h1`, `.item`), or use the `js:` form for computed checks.
- **0.9.x sessions auto-clean**: sessions are auto-killed; `crawler.crawler_strategy.kill_session(id)`
  still works but is optional for cleanup.

## Reference files — load on demand

Pick the file for the current task; load more only as needed.

### Setup & basics

- `references/installation-cli.md` — install, `crawl4ai-setup`, `crwl` CLI flags
- `references/caching.md` — `CacheMode` behavior (fresh vs cached)
- `references/content-options.md` — common `CrawlerRunConfig` options, `raw://` / local-file input, logging
- `references/crawl-result.md` — every `CrawlResult` field, markdown result, links/media, error handling

### Markdown output

- `references/markdown-generator.md` — generator options, citations, `content_source`, custom filters
- `references/content-filters.md` — Pruning / BM25 / LLM filter tuning ( → `fit_markdown`)

### Structured extraction

- `references/css-xpath-schema.md` — `JsonCss/JsonXPathExtractionStrategy` schemas (field types, nesting, `source`)
- `references/regex-extraction.md` — `RegexExtractionStrategy` for emails/URLs/prices/dates
- `references/llm-extraction.md` — `LLMExtractionStrategy` params + LLM schema generation
- `references/chunking.md` — chunking strategies + `CosineStrategy` clustering
- `references/table-extraction.md` — `DefaultTableExtraction` / `LLMTableExtraction`

### Advanced crawling

- `references/sessions.md` — `session_id` reuse, `js_only`, multi-tab
- `references/hooks-auth.md` — pipeline hooks, login/auth flows
- `references/proxy-security.md` — `proxy_config`, per-crawl proxy behavior
- `references/anti-bot.md` — stealth, UA randomization, retries, fallback, undetected mode
- `references/dynamic-pages.md` — `scan_full_page` vs `virtual_scroll_config`, lazy loading
- `references/pdf-downloads.md` — `PDFContentScrapingStrategy`, `accept_downloads`
- `references/ssl-cert.md` — `fetch_ssl_certificate`, `SSLCertificate`
- `references/identity.md` — persistent profiles, `user_data_dir`, `storage_state`
- `references/multi-url.md` — `arun_many`, dispatchers, rate limiting
- `references/network-capture.md` — `capture_network_requests`, console capture
- `references/adaptive-crawling.md` — `AdaptiveCrawler`, `digest()`, `AdaptiveConfig`
- `references/advanced-features.md` — other advanced capabilities tour
- `references/advanced-gotchas.md` — advanced-topic pitfalls (read before advanced work)

### API reference

- `references/async-webcrawler.md` — `AsyncWebCrawler` class + `arun_many()`
- `references/strategies.md` — extraction/chunking/filter strategy class hierarchy
- `references/c4a-script.md` — C4A-Script command reference
