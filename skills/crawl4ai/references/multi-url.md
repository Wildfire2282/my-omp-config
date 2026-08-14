# Multi-URL Crawling & Dispatchers

Read when crawling many URLs concurrently: `arun_many`, dispatchers, rate limiting, streaming.

## Multi-URL Crawling

`arun_many(urls, config, dispatcher=None)` handles many URLs with proper concurrency. A basic loop (`arun()` in a `for`) works but is the least efficient.

Batch mode (`stream=False`, default) collects all results, then you process them:

```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

async def main():
    urls = ["https://example1.com", "https://example2.com", "https://example3.com"]
    browser_config = BrowserConfig(headless=True)
    run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)  # stream=False is default

    async with AsyncWebCrawler(config=browser_config) as crawler:
        results = await crawler.arun_many(urls=urls, config=run_config)
        for result in results:
            if result.success:
                print(result.url, len(result.markdown.raw_markdown))
            else:
                print("Failed:", result.url, result.error_message)

asyncio.run(main())
```

Streaming mode (`stream=True`) yields results as soon as each finishes — use `async for`:

```python
async with AsyncWebCrawler(config=browser_config) as crawler:
    async for result in await crawler.arun_many(urls=urls, config=run_config, dispatcher=dispatcher):
        if result.success:
            await process_result(result)   # act immediately (real-time analytics, progressive storage)
```

With a dispatcher: pass `dispatcher=MemoryAdaptiveDispatcher(...)` (see Crawl Dispatchers section) to `arun_many`.

URL-specific configurations: pass a **list of `CrawlerRunConfig`** to `arun_many`; each config is matched against a URL via `url_matcher`. A config without `url_matcher` matches all URLs (fallback). `url_matcher` accepts glob strings (`"*.pdf"`, `"*/api/*"`, `"https://*.example.com/*"`), callables (`lambda url: 'github.com' in url`), or a list combined with `match_mode=MatchMode.AND` (all must match) or `MatchMode.OR`. Configs are evaluated in order — put specific patterns first, default config last; unmatched URLs fail with "No matching configuration found". Test with `config.is_match(url)`.

```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, MatchMode
from crawl4ai.processors.pdf import PDFContentScrapingStrategy
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import PruningContentFilter

async def crawl_mixed():
    configs = [
        CrawlerRunConfig(url_matcher="*.pdf", scraping_strategy=PDFContentScrapingStrategy()),
        CrawlerRunConfig(
            url_matcher=["*/blog/*", "*/article/*"],
            markdown_generator=DefaultMarkdownGenerator(content_filter=PruningContentFilter(threshold=0.48)),
        ),
        CrawlerRunConfig(url_matcher=lambda url: 'github.com' in url, js_code="window.scrollTo(0, 500);"),
        CrawlerRunConfig(),  # default/fallback: matches everything
    ]
    urls = ["https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
            "https://blog.python.org/", "https://github.com/microsoft/playwright", "https://example.com/"]
    async with AsyncWebCrawler() as crawler:
        for r in await crawler.arun_many(urls=urls, config=configs):
            print(r.url, len(r.markdown.raw_markdown))

# asyncio.run(crawl_mixed())
```

Robots.txt with multi-URL: `CrawlerRunConfig(check_robots_txt=True, semaphore_count=3)` respects robots.txt per URL (disallowed → 403 with "robots.txt" in the error message).

---

## Crawl Dispatchers

Dispatcher components (`crawl4ai.async_dispatcher`):

- `MemoryAdaptiveDispatcher` (default) — concurrency adapts to system memory: `memory_threshold_percent=90.0` (pause above this), `check_interval=1.0`, `max_session_permit=10` (max concurrent tasks), `memory_wait_timeout=600.0` (raises `MemoryError`), `rate_limiter=None`, `monitor=None`.
- `SemaphoreDispatcher` — fixed concurrency: `max_session_permit=20`, `rate_limiter=None`, `monitor=None`. (One doc example passes `semaphore_count=5` instead — `max_session_permit` is the documented constructor parameter.)
- `RateLimiter` — request pacing + exponential backoff with jitter on rate-limit codes: `base_delay=(1.0, 3.0)`, `max_delay=60.0`, `max_retries=3`, `rate_limit_codes=[429, 503]`.
- `CrawlerMonitor` — live dashboard: `max_visible_rows=15`, `display_mode=DisplayMode.DETAILED` (per-task status, memory, timing) or `DisplayMode.AGGREGATED` (summary).

```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, CrawlerMonitor, DisplayMode, RateLimiter
from crawl4ai.async_dispatcher import MemoryAdaptiveDispatcher, SemaphoreDispatcher

async def main():
    urls = ["https://example.com"] * 10
    browser_config = BrowserConfig(headless=True)

    rate_limiter = RateLimiter(base_delay=(1.0, 2.0), max_delay=30.0, max_retries=2, rate_limit_codes=[429, 503])
    monitor = CrawlerMonitor(max_visible_rows=15, display_mode=DisplayMode.DETAILED)

    dispatcher = MemoryAdaptiveDispatcher(
        memory_threshold_percent=70.0,
        check_interval=1.0,
        max_session_permit=10,
        rate_limiter=rate_limiter,
        monitor=monitor,
    )
    # Fixed concurrency alternative:
    # dispatcher = SemaphoreDispatcher(max_session_permit=20, rate_limiter=rate_limiter, monitor=monitor)

    async with AsyncWebCrawler(config=browser_config) as crawler:
        results = await crawler.arun_many(urls=urls, config=CrawlerRunConfig(cache_mode=CacheMode.BYPASS), dispatcher=dispatcher)
        for result in results:
            dr = result.dispatch_result        # DispatchResult dataclass
            print(result.url, f"{dr.memory_usage:.1f}MB", dr.end_time - dr.start_time)

asyncio.run(main())
```

`result.dispatch_result` is a `DispatchResult` with `task_id`, `memory_usage`, `peak_memory`, `start_time`, `end_time`, `error_message`.

Choice guidance: `MemoryAdaptiveDispatcher` for large crawls or limited resources; `SemaphoreDispatcher` for simple fixed-concurrency scenarios. (The standalone `crawl-dispatcher.md` page only announces a future dispatcher module — the actual, documented dispatcher API lives in `multi-url-crawling.md`, as above.)

---
