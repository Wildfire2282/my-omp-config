# Other Advanced Features

Read when touring remaining advanced capabilities (async/sync crawlers, browser reuse, multiple crawlers).

## Other Advanced Features (from advanced-features.md)

### PDF & Screenshot capture in one pass

`CrawlerRunConfig(pdf=True, screenshot=True)` returns `result.pdf` (base64) and `result.screenshot` (base64). A PDF export is more reliable than a full-page screenshot on long pages; if both are requested, the first PDF page is auto-converted to an image. `scroll_delay` (default `0.2`) controls the delay between scroll steps during full-page capture.

```python
import asyncio
from base64 import b64decode
from crawl4ai import AsyncWebCrawler, CacheMode, CrawlerRunConfig

async def main():
    run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, screenshot=True, pdf=True)
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="https://en.wikipedia.org/wiki/List_of_common_misconceptions", config=run_config)
        if result.success:
            if result.screenshot:
                open("wikipedia_screenshot.png", "wb").write(b64decode(result.screenshot))
            if result.pdf:
                open("wikipedia_page.pdf", "wb").write(result.pdf)

asyncio.run(main())
```

### Custom headers

Two ways: pass `headers={"Accept-Language": "es-ES,es;q=0.9"}` directly to `arun()`, or set on the strategy: `crawler.crawler_strategy.update_user_agent("MyCustomUA/1.0")` and `crawler.crawler_strategy.set_custom_headers({...})`. For advanced UA randomization/client hints, see Identity-Based Crawling or `UserAgentGenerator`.

### Robots.txt compliance

`CrawlerRunConfig(check_robots_txt=True)` checks and respects robots.txt; rules are cached in `~/.crawl4ai/robots/robots_cache.db` with a 7-day TTL. If robots.txt can't be fetched, crawling is allowed; a disallowed URL returns status 403.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://example.com", config=CrawlerRunConfig(check_robots_txt=True))
        if not result.success and result.status_code == 403:
            print("Access denied by robots.txt")

asyncio.run(main())
```

### Async vs sync crawler

The async API (`AsyncWebCrawler`) is the primary config-object API used throughout these docs. Sync equivalents exist for simple scripts. The 0.9.x pattern is `AsyncWebCrawler` + `BrowserConfig`/`CrawlerRunConfig`, with strategies inside `CrawlerRunConfig`.

### Browser reuse across runs

`BrowserConfig` + `storage_state` (dict or file) lets you resume with cookies/localStorage without re-logging in; managed browsers (`use_managed_browser=True`) persist full profiles. From the hooks docs: session-based crawling (`session_id`) reuses a single tab across multiple `arun()` calls; `arun_many()` runs each URL in parallel — hooks must be async-safe accordingly.

### Choosing anti-bot approach

Progression: regular browser (no protection) → regular + stealth (basic checks) → undetected browser (advanced protection) → undetected + stealth (maximum evasion).

---
