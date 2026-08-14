# AsyncWebCrawler & arun_many

Read when working with the `AsyncWebCrawler` class or `arun_many()` for multi-URL crawling.

## AsyncWebCrawler

Core class for asynchronous web crawling. Create it **once** with a `BrowserConfig`, then run multiple `arun()` calls with different `CrawlerRunConfig` objects.

### Constructor

```python
AsyncWebCrawler(
    crawler_strategy: Optional[AsyncCrawlerStrategy] = None,  # (Advanced) custom strategy
    config: Optional[BrowserConfig] = None,                    # browser setup (engine, headless, UA, proxy)
    always_bypass_cache: bool = False,           # DEPRECATED: use CrawlerRunConfig.cache_mode
    always_by_pass_cache: Optional[bool] = None, # DEPRECATED
    base_directory: str = ..., thread_safe: bool = False, **kwargs)
```

```python
from crawl4ai import AsyncWebCrawler, BrowserConfig
browser_cfg = BrowserConfig(browser_type="chromium", headless=True, verbose=True)
crawler = AsyncWebCrawler(config=browser_cfg)
```

### Lifecycle: Context Manager or Manual Start/Close

```python
async with AsyncWebCrawler(config=browser_cfg) as crawler:  # recommended; auto start/close
    result = await crawler.arun("https://example.com")

crawler = AsyncWebCrawler(config=browser_cfg)  # manual start/close for long-running apps
await crawler.start()
result2 = await crawler.arun("https://another.com")
await crawler.close()
```

### `arun()` — Primary Method

```python
async def arun(self, url: str, config: Optional[CrawlerRunConfig] = None, ...) -> CrawlResult:
```

`CrawlerRunConfig` sets everything per crawl — caching, content filtering, extraction strategy, session reuse, JS code, screenshots:

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
run_cfg = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, css_selector="main.article",
                           word_count_threshold=10, screenshot=True)
async with AsyncWebCrawler(config=browser_cfg) as crawler:
    result = await crawler.arun("https://example.com/news", config=run_cfg)
    print("Crawled HTML length:", len(result.cleaned_html))
```

Each `arun()` returns a `CrawlResult` (see below): `url`, `html`, `cleaned_html`, `markdown` (**`markdown_v2` removed in v0.5 — raises `AttributeError`; use `markdown`**), `extracted_content` (JSON for CSS/LLM strategies), `screenshot`/`pdf`, `media`, `links`, `success`, `error_message`. Legacy direct arguments (`css_selector=...`, `word_count_threshold=...`) still work but migrate into `CrawlerRunConfig`. `BrowserConfig` holds global browser settings; `CrawlerRunConfig`, per-crawl logic. Use the context manager unless you need a persistent crawler.

## arun_many()

Concurrent/batch crawling. Returns `RunManyReturn` — a **list** of `CrawlResult`, or an **async generator** when streaming is enabled.

| Parameter | Type / Default | What It Does |
| --- | --- | --- |
| `urls` | `Union[List[str], List[Any]]` | List of URLs (or tasks) to crawl. |
| `config` | single `CrawlerRunConfig`, or list with `url_matcher` patterns (first match wins) | Per-URL behavior. |
| `dispatcher` | `Optional[BaseDispatcher]` | Concurrency controller; a default (e.g. `MemoryAdaptiveDispatcher`) is used if omitted. |
| return | `RunManyReturn` | List of `CrawlResult` or async generator when `stream=True`. |

### Batch Mode (Default)

```python
results = await crawler.arun_many(["https://site1.com", "https://site2.com"])  # batch, default dispatcher
for res in results:
    print(res.url, "crawled OK!" if res.success else f"Failed: {res.error_message}")
```

### Streaming Mode

Set `stream=True` in `CrawlerRunConfig`; process each result as it completes — ideal for large URL sets:

```python
async for result in await crawler.arun_many(
    urls=["https://site1.com", "https://site2.com", "https://site3.com"],
    config=CrawlerRunConfig(stream=True, cache_mode=CacheMode.BYPASS)):
    if result.success:
        print(f"Just completed: {result.url}")
```

### Concurrency, Dispatchers & Rate Limiting

```python
dispatcher = MemoryAdaptiveDispatcher(memory_threshold_percent=70.0, max_session_permit=10)
results = await crawler.arun_many(urls=[...], config=cfg, dispatcher=dispatcher)
```

| Dispatcher | Behavior |
| --- | --- |
| `MemoryAdaptiveDispatcher` | Dynamically manages concurrency based on system memory usage. |
| `SemaphoreDispatcher` | Fixed concurrency limit; simpler but less adaptive. |

Rate limiting: automatic delay between requests, exponential backoff on rate-limit detection, domain-specific rate limiting, configurable retry strategy. Resource monitoring: memory tracking, adaptive concurrency under system load, automatic pausing when constrained. Each `CrawlResult` may carry a `dispatch_result` with memory/timing info. Pitfalls: use a dispatcher for thousands of URLs (memory/rate limits); handle sessions for logins; always check `result.success`/`error_message` per result.

### URL-Specific Configurations

Pass a list of configs with `url_matcher` patterns — **first match wins**:

```python
from crawl4ai.processors.pdf import PDFContentScrapingStrategy
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
pdf_config = CrawlerRunConfig(url_matcher="*.pdf", scraping_strategy=PDFContentScrapingStrategy())
blog_config = CrawlerRunConfig(url_matcher="*/blog/*",
    markdown_generator=DefaultMarkdownGenerator(content_filter=PruningContentFilter(threshold=0.48)))
github_config = CrawlerRunConfig(url_matcher=lambda url: 'github.com' in url, js_code="window.scrollTo(0, 500);")
api_config = CrawlerRunConfig(url_matcher=lambda url: 'api' in url or url.endswith('.json'))
default_config = CrawlerRunConfig()  # no url_matcher = fallback only
results = await crawler.arun_many(urls=["https://blog.python.org/", "https://github.com/microsoft/playwright",
                                        "https://httpbin.org/json", "https://example.com/"],
                                  config=[pdf_config, blog_config, github_config, api_config, default_config])
```

URL matching: string patterns (`"*.pdf"`, `"*/blog/*"`, `"*python.org*"`), function matchers (`lambda url: 'api' in url`), combined with `MatchMode.OR`/`MatchMode.AND`. **Always include a default config (no `url_matcher`) as the last item — otherwise unmatched URLs fail.**
