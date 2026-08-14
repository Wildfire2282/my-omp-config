# Persistent Identity

Read when preserving login state across runs: persistent contexts, `user_data_dir`, `storage_state`, cookies.

## Identity-Based Crawling

Preserve a real browsing identity (cookies, localStorage, fingerprints, logins) across runs using persistent browser profiles.

Workflow: 1) create a user-data directory (external Chromium with `--user-data-dir=...`, or the CLI `crwl profiles`, or `BrowserProfiler.create_profile()`); 2) log in / configure sites in that browser and close it; 3) point `BrowserConfig.user_data_dir` at that folder with `use_managed_browser=True`; 4) crawl — the site sees your real identity.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

async def main():
    browser_config = BrowserConfig(
        headless=True,
        verbose=True,
        use_managed_browser=True,     # enables persistent browser strategy
        browser_type="chromium",
        user_data_dir="/home/you/my_chrome_profile",
    )
    crawl_config = CrawlerRunConfig(wait_for="css:.logged-in-content")

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url="https://example.com/private", config=crawl_config)
        print("Accessed private data:", result.success)

asyncio.run(main())
```

`BrowserProfiler` API (recommended over the legacy `ManagedBrowser` methods, which still delegate to it):

```python
import asyncio
from crawl4ai import BrowserProfiler

async def main():
    profiler = BrowserProfiler()
    profile_path = await profiler.create_profile(profile_name="my-login-profile")
    # A browser window opens; log in, press 'q' in the terminal to save.
    print("Saved at:", profile_path)

    for profile in profiler.list_profiles():
        print(profile["name"], profile["path"], profile["created"], profile["type"])
    print(profiler.get_profile_path("my-login-profile"))

asyncio.run(main())
```

Other `BrowserProfiler` methods: `interactive_manager(crawl_callback=fn)` (guided console with a "crawl with profile" option) and `delete_profile(name)`.

CLI alternative: `crwl profiles` → "Create new profile", log in, press `q`; profiles land in `~/.crawl4ai/profiles/<name>/` with a `storage_state.json`. Pass the folder to `BrowserConfig.user_data_dir`.

Session-state injection without a profile: pass `storage_state` (dict or path to a JSON file exported via `context.storage_state(path=...)`) directly to the crawler — `AsyncWebCrawler(storage_state=storage_dict)` (see Hooks section).

Identity customization via `CrawlerRunConfig`: `locale` (e.g. `"fr-FR"`), `timezone_id` (e.g. `"Europe/Paris"`), and `geolocation=GeolocationConfig(latitude=..., longitude=..., accuracy=...)` (auto-grants geolocation permission; use e.g. `GeolocationConfig(latitude=48.8566, longitude=2.3522, accuracy=100)`).

```python
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, GeolocationConfig

browser_config = BrowserConfig(
    use_managed_browser=True,
    user_data_dir="/path/to/my-profile",
    browser_type="chromium",
)
crawl_config = CrawlerRunConfig(
    locale="es-MX",
    timezone_id="America/Mexico_City",
    geolocation=GeolocationConfig(latitude=19.4326, longitude=-99.1332),
)
# async with AsyncWebCrawler(config=browser_config) as crawler:
#     result = await crawler.arun(url="https://example.com", config=crawl_config)
```

**Magic Mode** (`CrawlerRunConfig(magic=True)` in an ordinary crawl) is the lightweight alternative: randomizes user agent and navigator, randomizes interactions/timings, masks automation signals, attempts pop-up handling. No persistent data; good for quick tasks, not a substitute for a real identity. Managed Browsers are recommended for login-gated or complex sites.

---
