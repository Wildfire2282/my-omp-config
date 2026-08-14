# Dynamic Pages: Lazy Loading & Virtual Scroll

Read when a page loads content on scroll: `scan_full_page` (appended content) vs `virtual_scroll_config` (replaced content).

## Lazy Loading

For sites that load images lazily as the user scrolls, so they appear in `result.media`:

- `wait_for_images=True` — wait for images to finish loading before finalizing the HTML.
- `scan_full_page=True` — scroll the entire page top-to-bottom, triggering lazy loads.
- `scroll_delay=<seconds>` — pause between scroll steps (default `0.2`; increase for slow-loading assets).

```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

async def main():
    config = CrawlerRunConfig(
        wait_for_images=True,
        scan_full_page=True,
        scroll_delay=0.5,
        cache_mode=CacheMode.BYPASS,
        verbose=True,
    )
    async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
        result = await crawler.arun("https://www.example.com/gallery", config=config)
        if result.success:
            images = result.media.get("images", [])
            print("Images found:", len(images))
            for img in images[:5]:
                print(f"[Image] URL: {img['src']}, Score: {img.get('score', 'N/A')}")

asyncio.run(main())
```

Compose with the usual filters: add `exclude_external_images=True` (keep only same-domain images) and `exclude_domains=[...]` to the same `CrawlerRunConfig`.

Tips: `scan_full_page` on extremely long/infinite pages is resource-intensive — prefer hooks or targeted `js_code` for "Load More" triggers; if images load in batches, raise `scroll_delay` or loop partial scrolls; for placeholder-to-image transitions use `wait_for="css:img.loaded"`; if caching hides fresh images, set `cache_mode=CacheMode.BYPASS`. For sites where content is *replaced* (Twitter/Instagram style), use Virtual Scroll instead.

---

## Virtual Scroll

Virtual scrolling (windowed rendering) **replaces** DOM items as you scroll instead of appending them, so a naive crawl captures only the visible items. Crawl4AI's Virtual Scroll detects three scroll behaviors — no change, content appended (traditional infinite scroll), content replaced (true virtual scroll). Only the replacement case needs special handling; `VirtualScrollConfig` automates it (detect → capture HTML chunks per position → merge, deduplicating by normalized text).

```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, VirtualScrollConfig

async def crawl_twitter_timeline():
    virtual_config = VirtualScrollConfig(
        container_selector="[data-testid='primaryColumn']",  # required
        scroll_count=30,          # max scrolls (default 10)
        scroll_by="container_height",  # "container_height" | "page_height" | int pixels
        wait_after_scroll=1.0,    # seconds after each scroll (default 0.5)
    )
    config = CrawlerRunConfig(virtual_scroll_config=virtual_config)

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="https://twitter.com/search?q=AI", config=config)
        import re
        tweets = re.findall(r'data-testid="tweet"', result.html)
        print(f"Captured {len(tweets)} tweets")

# asyncio.run(crawl_twitter_timeline())
```

`VirtualScrollConfig` parameters: `container_selector` (str, required), `scroll_count` (int, default `10`), `scroll_by` (str or int, default `"container_height"`), `wait_after_scroll` (float, default `0.5`). `scroll_by` options: `"container_height"` (container's visible height), `"page_height"` (viewport height), or an integer pixel amount.

Virtual Scroll vs `scan_full_page`:

| | Virtual Scroll | `scan_full_page` |
|---|---|---|
| Purpose | Capture content that is **replaced** during scroll | Load content that is **appended** during scroll |
| Use case | Twitter, Instagram, virtualized tables | Traditional infinite scroll, lazy-loaded images |
| DOM behavior | Replaces elements | Adds elements |
| Memory | Efficient (merges content) | Can grow large |
| Config | Requires container selector | Works on full page |

Works with extraction strategies (e.g. `LLMExtractionStrategy` in `CrawlerRunConfig`) — extraction runs over the merged full content. If the container isn't found, crawling continues normally without virtual scroll. Performance tips: be specific with the container selector; start with `scroll_count=10` and increase; tune `wait_after_scroll` (0.2 fast sites, 1.5 slow/heavy); use `headless=False` to watch scrolling.

---
