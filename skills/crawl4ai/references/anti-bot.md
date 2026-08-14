# Bypassing Bot Detection

Read when a site blocks the crawler: stealth, user-agent randomization, retries, fallback fetch, undetected mode.

## Anti-Bot Detection & Fallback

Crawl4AI detects blocking (HTTP 403/429 with short bodies, challenge pages, CAPTCHA injection, firewall iframes — via structural HTML markers, not keywords) and escalates through layered strategies automatically. All options live on `CrawlerRunConfig`:

| Parameter | Type | Default | Meaning |
|---|---|---|---|
| `max_retries` | `int` | `0` | Retry rounds when blocking is detected (`0` = no retries) |
| `proxy_config` | `ProxyConfig` \| `list[ProxyConfig]` \| `None` | `None` | Single proxy or ordered list; each round iterates the whole list. Put `ProxyConfig.DIRECT` (or `"direct"`) in a list to try no-proxy explicitly |
| `fallback_fetch_function` | `async (str) -> str` | `None` | Last resort: receives URL, returns raw HTML, processed through the normal pipeline |

Escalation chain — for each of `1 + max_retries` rounds, try every proxy in order; if all fail, call `fallback_fetch_function` (worst case: `(1 + max_retries) x len(proxy_config)` browser attempts). `result.crawl_stats` reports what happened:

```python
result.crawl_stats = {
    "attempts": 3,                # total browser attempts
    "retries": 1,                 # retry rounds used (0 = first round succeeded)
    "proxies_used": [
        {"proxy": None,             "status_code": 403, "blocked": True,  "reason": "Akamai block"},
        {"proxy": "proxy.io:8080",  "status_code": 200, "blocked": False, "reason": ""},
    ],
    "fallback_fetch_used": False, # whether fallback_fetch_function ran
    "resolved_by": "proxy",       # "direct" | "proxy" | "fallback_fetch" | None
}
```

```python
import asyncio, aiohttp
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig, ProxyConfig

# Last-resort fetch via an external scraping service
async def external_fetch(url: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.my-scraping-service.com/fetch",
                               params={"url": url, "format": "html"},
                               headers={"Authorization": "Bearer MY_TOKEN"}) as resp:
            if resp.status == 200:
                return await resp.text()
            raise RuntimeError(f"API error: {resp.status}")

async def main():
    browser_config = BrowserConfig(headless=True, enable_stealth=True)
    crawl_config = CrawlerRunConfig(
        magic=True,                    # human-like interactions, UA/navigator randomization
        wait_until="load",             # domcontentloaded can return before anti-bot sensors finish
        max_retries=2,
        proxy_config=[                # tried in order each round — cheapest first
            ProxyConfig(server="http://datacenter-proxy.example.com:8080", username="u", password="p"),
            ProxyConfig(server="http://residential-proxy.example.com:9090", username="u", password="p"),
        ],
        fallback_fetch_function=external_fetch,
    )
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url="https://protected-site.com/products", config=crawl_config)
        if result.success:
            print(f"Got {len(result.markdown.raw_markdown)} chars; resolved by {result.crawl_stats['resolved_by']}")
        else:
            print("All attempts failed:", result.error_message)

asyncio.run(main())
```

Simpler combos: `CrawlerRunConfig(max_retries=3)` for plain retry; direct-first escalation via `proxy_config=[ProxyConfig.DIRECT, ProxyConfig(...)]`; a lone `fallback_fetch_function` with `max_retries=0` as a safety net.

Tips: order proxies cheapest-first (datacenter → residential → premium); combine with `BrowserConfig(enable_stealth=True)` and `magic=True`; check `crawl_stats` to see which proxy worked. If everything fails, the result returns `success=False` with `error_message` describing the block reason.

---

## Undetected Browser Mode

Two anti-bot features (see the comparison table in the docs):

- **Stealth Mode** — `BrowserConfig(enable_stealth=True)`: uses playwright-stealth to remove `navigator.webdriver`, modify fingerprints, emulate plugins, adjust navigator properties. Fixes common automation leaks. For basic bot detection.
- **Undetected Browser Mode** — deep-level patches via a browser **adapter**; handles CDP detection and sophisticated services (Cloudflare, DataDome). Slightly slower, more resource-heavy.

Recommended progression: regular browser + stealth → undetected browser → undetected + stealth.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, UndetectedAdapter
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy

async def main():
    browser_config = BrowserConfig(headless=False, verbose=True, enable_stealth=True)  # stealth + undetected
    crawler_strategy = AsyncPlaywrightCrawlerStrategy(browser_config=browser_config, browser_adapter=UndetectedAdapter())
    async with AsyncWebCrawler(crawler_strategy=crawler_strategy, config=browser_config) as crawler:
        result = await crawler.arun(url="https://example.com", config=CrawlerRunConfig())
        print(result.success, (result.markdown.raw_markdown or "")[:500])

asyncio.run(main())
```

Adapter pattern: `PlaywrightAdapter()` is the default; swap per site: `adapter = UndetectedAdapter() if is_protected_site(url) else PlaywrightAdapter()`.

Additional evasion knobs documented in the troubleshooting section: `CrawlerRunConfig(simulate_user=True, magic=True, wait_time=5.0)` (user simulation, magic mode, longer waits).

Best practices: avoid headless when possible; use reasonable delays (`wait_time`, `delay_before_return_html`); rotate/customize user agents (`BrowserConfig(headers={"User-Agent": "..."})`); handle failure gracefully — some sites still block.

Installation: `crawl4ai-setup` installs all browser dependencies for both regular and undetected modes.

Limitations (documented): slightly slower than regular mode; some sites can still detect headless mode; higher resource usage; not 100% guaranteed — anti-bot services evolve. (Stealth/undetected are not enabled by default; opt in explicitly.)

---
