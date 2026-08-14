# Advanced-Topic Gotchas

Read when working on advanced topics: hooks, sessions, anti-bot, proxies, virtual scroll, PDFs, downloads.

## Gotchas

- **Hooks**: never create/close pages inside `on_browser_created` (no context exists yet) — do auth in `on_page_context_created`. A failing hook fails the crawl; heavy hooks slow it down. With `arun_many()`, hooks run per-URL in parallel — make them async-safe. Overwriting/removing elements in the wrong hook can corrupt the final crawl.
- **Session management** is for sequential workflows only — do not use `session_id` reuse for parallel tasks. Always call `kill_session(session_id)` when done to free the tab.
- **Anti-bot retries**: worst case is `(1 + max_retries) × len(proxy_config)` browser attempts before the fallback function runs — budget crawl time. Detection uses structural HTML markers, not keywords (a page merely *mentioning* "CAPTCHA" won't be flagged). Use `wait_until="load"` (not `domcontentloaded`) for anti-bot sites.
- **Proxy**: the legacy `BrowserConfig(proxy)` parameter is deprecated — configure via `CrawlerRunConfig.proxy_config`. Order proxy lists cheapest-first (datacenter → residential → premium). Some proxies break SSL inspection; switch proxies on repeated SSL errors. Use env vars (never hardcode) for proxy credentials.
- **Undetected mode**: slower and more resource-hungry than the regular browser; some sites still detect headless; not 100% guaranteed. Stealth and undetected are not enabled by default — opt in explicitly. Run `crawl4ai-setup` if the browser is missing.
- **Virtual scroll**: requires an accurate `container_selector`; if the container isn't found, crawling continues normally (no error, but no virtual-scroll capture either). Prefer it for *replacing* content; use `scan_full_page` for *appending* content.
- **Lazy loading**: `scan_full_page=True` on extremely long/infinite pages is resource-intensive; if caching is on, repeated crawls may skip network fetches — use `cache_mode=CacheMode.BYPASS` to force fresh loads.
- **PDF**: scanned/image-based PDFs yield no text without OCR (not built in); `NaivePDFProcessorStrategy` is limited on complex layouts, encrypted PDFs, and forms; image extraction is CPU/disk heavy.
- **SSL**: `SSLCertificate` fetches and parses only — it does **not** validate the certificate chain or trust store; `from_url` uses a default 10s socket timeout.
- **Multi-URL configs**: config list is evaluated in order — specific `url_matcher` patterns first, default config last; without a default config, unmatched URLs fail with "No matching configuration found". No `url_matcher` = matches everything (fallback).
- **Dispatchers**: `SemaphoreDispatcher` is documented with `max_session_permit` in the constructor reference, but one doc example passes `semaphore_count=5` — check the version you use. `MemoryAdaptiveDispatcher.memory_wait_timeout` (default 600s) raises `MemoryError` if memory stays above threshold too long.
- **File downloads**: downloads happen inside the browser context — `js_code` must target the real trigger element; use `wait_for` so the download starts before extraction; scan downloaded files before use.
- **Robots.txt**: cache lives in `~/.crawl4ai/robots/robots_cache.db` (7-day TTL); a disallowed URL returns 403 — check `result.status_code` / error message, don't treat it as a network failure.
