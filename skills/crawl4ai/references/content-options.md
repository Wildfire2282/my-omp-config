# Content Options & Input Sources

Read when configuring common content options (`word_count_threshold`, exclusions) or feeding raw HTML / local files.

## Common `CrawlerRunConfig` content options

```python
from crawl4ai import CrawlerRunConfig

config = CrawlerRunConfig(
    word_count_threshold=10,          # skip text blocks under N words (default ~200)
    excluded_tags=["nav", "footer"],  # remove whole tags
    excluded_selector="#ads, .tracker",
    exclude_external_links=True,
    process_iframes=True,
    remove_overlay_elements=True,
    keep_attrs=["id", "class"],       # attributes preserved in cleaned HTML
    only_text=True,                   # text-only extraction attempt
)
```

## Local files & raw HTML as input

- `url="raw://<html>"` — inline HTML, no network.
- `url="file:///path/to/file.html"` — local file.
- `url="pdf://..."` — PDF as input source (see advanced reference).

## Logging & debugging

```python
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

browser_config = BrowserConfig(verbose=True)
config = CrawlerRunConfig(
    log_console=True,                 # page's JS console output
    capture_console_messages=True,    # → result.console_messages
    capture_network_requests=True,    # → result.captured_requests
)
```
