# Reusing Browser Sessions

Read when reusing a browser tab across calls (`session_id`), running JS on a loaded page (`js_only`), or multi-tab workflows.

## Session Management

`session_id` (passed in `CrawlerRunConfig`) lets successive `arun()` calls reuse the **same browser tab (page object)** — state, cookies, scroll position, and JS globals survive between calls. Sequential workflows only, not parallel ones.

Key parameters:

- `session_id: str` — names the session; the same value on later `arun()` calls reuses the tab.
- `js_only: bool` — when `True`, the crawler does **not** navigate again; it only executes `js_code` / re-extracts on the already-open page (much faster for pagination).
- `wait_for` — CSS selector string or JS predicate expression to wait for before extracting.
- `js_code` — JS to run on the page (e.g. click the "next page" button).
- Cleanup: 0.9.x auto-kills sessions when done; `await crawler.crawler_strategy.kill_session(session_id)` still frees a tab early. Multiple tabs need distinct `session_id` values. `js_only`, `wait_for`, and `js_code` also combine with hooks.

Minimal example — reuse `session_id` across two `arun()` calls, then free the tab:

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode

async def main():
    session_id = "my_session"
    async with AsyncWebCrawler() as crawler:
        result1 = await crawler.arun(url="https://example.com/page1",
                                     config=CrawlerRunConfig(session_id=session_id, cache_mode=CacheMode.BYPASS))
        result2 = await crawler.arun(url="https://example.com/page2",  # same tab
                                     config=CrawlerRunConfig(session_id=session_id, cache_mode=CacheMode.BYPASS))
        print(result1.success, result2.success)
        await crawler.crawler_strategy.kill_session(session_id)  # free the tab

asyncio.run(main())
```

Typical pagination loop with `js_only` (click "next", wait for new content, re-extract — no reload):

```python
import asyncio, json
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

async def main():
    session_id = "commits_session"
    js_next = "document.querySelector('a[data-testid=\"pagination-next-button\"]').click();"
    wait_new = """() => {   // returns true when the first commit row changed
        const els = document.querySelectorAll('li[data-testid="commit-row-item"] h4');
        return els.length > 0 && els[0].textContent.trim() !== window.lastCommit;
    }"""
    schema = {"name": "Commit Extractor",
              "baseSelector": "li[data-testid='commit-row-item']",
              "fields": [{"name": "title", "selector": "h4 a", "type": "text", "transform": "strip"}]}

    async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
        all_commits = []
        for page in range(3):
            config = CrawlerRunConfig(
                session_id=session_id,
                extraction_strategy=JsonCssExtractionStrategy(schema),
                js_code=js_next if page > 0 else None,
                wait_for=wait_new if page > 0 else None,
                js_only=page > 0,              # no reload after first page
                cache_mode=CacheMode.BYPASS,
            )
            result = await crawler.arun(url="https://github.com/microsoft/TypeScript/commits/main", config=config)
            if result.extracted_content:
                all_commits += json.loads(result.extracted_content)
        print("Total commits:", len(all_commits))
        await crawler.crawler_strategy.kill_session(session_id)

asyncio.run(main())
```

Use cases: auth flows, pagination, form submissions, multi-step workflows, JS-rendered content. Session-based crawling works with hooks unchanged (see next section). A `session_id` also combines with identity-based crawling to persist a logged-in state.

---
