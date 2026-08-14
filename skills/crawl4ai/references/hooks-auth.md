# Hooks & Auth

Read when running code at crawl pipeline stages (hooks) or handling login/authenticated sessions.

## Hooks & Authentication

Hooks are registered on the crawler strategy via `crawler.crawler_strategy.set_hook(name, fn)` and run at fixed points of the pipeline. Available hooks (exact names):

1. `on_browser_created` — after the browser is created; **no page/context exists yet** → light tasks only.
2. `on_page_context_created` — after a new context and page are created, before navigating; **the right place for login/auth/route blocking**.
3. `before_goto` — just before navigating to a URL (custom headers, logging).
4. `after_goto` — right after navigation completes (verify content, wait for elements).
5. `on_user_agent_updated` — whenever the user agent changes.
6. `on_execution_started` — when custom JS (`js_code`) execution begins.
7. `before_retrieve_html` — just before the final HTML snapshot (final scroll, lazy-load triggers).
8. `before_return_html` — last hook before HTML goes into `CrawlResult` (logging, minor tweaks).

Each hook is an async function that takes the relevant objects plus `**kwargs` and returns the page (e.g. `return page`).

```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from playwright.async_api import Page, BrowserContext

async def main():
    browser_config = BrowserConfig(headless=True, verbose=True)
    run_config = CrawlerRunConfig(js_code="window.scrollTo(0, document.body.scrollHeight);", cache_mode=CacheMode.BYPASS)
    crawler = AsyncWebCrawler(config=browser_config)

    async def on_browser_created(browser, **kwargs):
        print("[HOOK] browser created")
        return browser

    async def on_page_context_created(page: Page, context: BrowserContext, **kwargs):
        # AUTH GOES HERE: fresh page+context before arun() navigates.
        # await page.goto("https://example.com/login"); await page.fill(...); await page.click(...)
        # await context.add_cookies([...])   # or set localStorage tokens
        async def route_filter(route):  # block image requests
            if route.request.resource_type == "image":
                await route.abort()
            else:
                await route.continue_()
        await context.route("**", route_filter)
        await page.set_viewport_size({"width": 1080, "height": 600})
        return page

    async def before_goto(page: Page, context: BrowserContext, url: str, **kwargs):
        await page.set_extra_http_headers({"Custom-Header": "my-value"})
        return page

    async def after_goto(page: Page, context: BrowserContext, url: str, response, **kwargs):
        return page

    async def on_user_agent_updated(page: Page, context: BrowserContext, user_agent: str, **kwargs):
        print("[HOOK] new user agent:", user_agent)
        return page

    async def on_execution_started(page: Page, context: BrowserContext, **kwargs):
        return page

    async def before_retrieve_html(page: Page, context: BrowserContext, **kwargs):
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
        return page

    async def before_return_html(page: Page, context: BrowserContext, html: str, **kwargs):
        return page

    for name, fn in [
        ("on_browser_created", on_browser_created),
        ("on_page_context_created", on_page_context_created),
        ("before_goto", before_goto),
        ("after_goto", after_goto),
        ("on_user_agent_updated", on_user_agent_updated),
        ("on_execution_started", on_execution_started),
        ("before_retrieve_html", before_retrieve_html),
        ("before_return_html", before_return_html),
    ]:
        crawler.crawler_strategy.set_hook(name, fn)

    await crawler.start()
    result = await crawler.arun("https://example.com", config=run_config)
    print("success:", result.success, "html length:", len(result.html))
    await crawler.close()

asyncio.run(main())
```

Login-state save/restore (no hook needed): sign in once, export the browser context, reuse it later.

```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    # Run 1: after interactive login, export state
    async with AsyncWebCrawler() as crawler:
        context = await crawler.crawler_strategy.get_browser_context()
        await context.storage_state(path="my_storage.json")  # cookies + localStorage

    # Run 2: start "already logged in" — no re-login
    storage_dict = {
        "cookies": [{"name": "session", "value": "abcd1234", "domain": "example.com",
                      "path": "/", "expires": 1699999999.0, "httpOnly": False, "secure": False, "sameSite": "None"}],
        "origins": [{"origin": "https://example.com",
                      "localStorage": [{"name": "token", "value": "my_auth_token"}]}],
    }
    async with AsyncWebCrawler(storage_state=storage_dict) as crawler:
        result = await crawler.arun("https://example.com/protected")
        print(result.success, len(result.html))

asyncio.run(main())
```

Hook gotchas: do **not** create or close pages inside `on_browser_created`; do auth in `on_page_context_created`; keep hooks light (they slow crawling); a failing hook fails the whole crawl; under `arun_many()` hooks run per-URL in parallel, so they must be thread/async-safe.

---
