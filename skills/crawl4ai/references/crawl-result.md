# CrawlResult & Output Handling

Read when inspecting crawl output: all `CrawlResult` fields, markdown result, links/media, error handling, logging.

## CrawlResult

Everything returned after a single crawl. Source: `crawl4ai/crawler/models.py`.

### Full Field List

```python
class CrawlResult(BaseModel):
    url: str
    html: str
    success: bool
    cleaned_html: Optional[str] = None
    fit_html: Optional[str] = None  # Preprocessed HTML optimized for extraction
    media: Dict[str, List[Dict]] = {}
    links: Dict[str, List[Dict]] = {}
    downloaded_files: Optional[List[str]] = None
    screenshot: Optional[str] = None
    pdf: Optional[bytes] = None
    mhtml: Optional[str] = None
    markdown: Optional[Union[str, MarkdownGenerationResult]] = None
    extracted_content: Optional[str] = None
    metadata: Optional[dict] = None
    error_message: Optional[str] = None
    session_id: Optional[str] = None
    response_headers: Optional[dict] = None
    status_code: Optional[int] = None
    redirected_status_code: Optional[int] = None
    ssl_certificate: Optional[SSLCertificate] = None
    dispatch_result: Optional[DispatchResult] = None
```

### Basic Crawl Info

| Field | Type | What It Is |
| --- | --- | --- |
| `url` | `str` | Final URL (after any redirects). |
| `success` | `bool` | `True` if the crawl pipeline ended without major errors. |
| `status_code` | `Optional[int]` | HTTP status of the **first** response in the redirect chain (e.g. 301/302 when redirected). |
| `redirected_status_code` | `Optional[int]` | HTTP status of the **final** redirect destination (302 → 200: `status_code=302`, `redirected_status_code=200`). `None` for non-HTTP requests (raw HTML, local files). |
| `error_message` | `Optional[str]` | Failure description when `success=False`. |
| `ssl_certificate` | `Optional[SSLCertificate]` | Certificate info when `fetch_ssl_certificate=True` in `CrawlerRunConfig`; exportable PEM/DER/JSON; props `issuer`, `subject`, `valid_from`, `valid_until`. |

```python
if result.status_code in (301, 302) and result.redirected_status_code == 200:
    print(f"Redirected to {result.url} (OK)")
```

### Content Fields

- `html` (`str`): original, unmodified HTML (possibly large).
- `cleaned_html` (`Optional[str]`): sanitized HTML — scripts, styles, and excluded tags removed per `CrawlerRunConfig`.
- `fit_html` (`Optional[str]`): preprocessed HTML optimized for extraction.

### Markdown Fields

`result.markdown` holds a `MarkdownGenerationResult`:

| Field | Type | What It Is |
| --- | --- | --- |
| `raw_markdown` | `str` | Full HTML → Markdown conversion. |
| `markdown_with_citations` | `str` | Same markdown with links as academic-style citations. |
| `references_markdown` | `str` | Reference list / footnotes at the end. |
| `fit_markdown` | `Optional[str]` | Filtered "fit" text — only if a content filter (Pruning/BM25) was applied. |
| `fit_html` | `Optional[str]` | The HTML that led to `fit_markdown`. |

```python
if result.markdown:
    print("Raw MD:", result.markdown.raw_markdown[:300])
    if result.markdown.fit_markdown:
        print("Pruned text:", result.markdown.fit_markdown[:300])
```

"fit" content exists only when a filter (like `PruningContentFilter` or `BM25ContentFilter`) was used inside a `MarkdownGenerationStrategy`; otherwise both stay `None`. Citations require `options={"citations": True}` in `DefaultMarkdownGenerator`.

### Media & Links

- `media` (`Dict[str, List[Dict]]`): keys `"images"`, `"videos"`, `"audios"`. Item fields: `src` (URL), `alt`/`title`, `score` (relevance float), `desc`/`description`.
- `links` (`Dict[str, List[Dict]]`): keys `"internal"` and `"external"` (grouped by domain). Item fields: `href`, `text`, `title`, `context` (surrounding text), `domain` (external only).

```python
for img in result.media.get("images", []):
    if img.get("score", 0) > 5:
        print("High-value image:", img["src"])
```

### Additional Fields

| Field | Type | How to Get It |
| --- | --- | --- |
| `extracted_content` | `Optional[str]` | JSON string when an `extraction_strategy` was used; parse with `json.loads`. |
| `downloaded_files` | `Optional[List[str]]` | Local paths when `accept_downloads=True` in `BrowserConfig` + `downloads_path`. |
| `screenshot` | `Optional[str]` | Base64 PNG when `screenshot=True` in `CrawlerRunConfig`; decode with `base64.b64decode`. |
| `pdf` | `Optional[bytes]` | Raw PDF bytes when `pdf=True` in `CrawlerRunConfig`. |
| `mhtml` | `Optional[str]` | MHTML snapshot (page + all resources) when `capture_mhtml=True`. |
| `metadata` | `Optional[dict]` | Page metadata: `title`, `description`, OG data, `author`. |

### `dispatch_result` (Concurrency Info)

Populated when crawling in parallel (e.g. `arun_many()` + dispatcher): `task_id`, `memory_usage` (MB at completion), `peak_memory` (MB), `start_time`/`end_time` (datetime), `error_message`. `None` without concurrency.

### Network Requests & Console Messages

Enabled via `capture_network_requests=True` and `capture_console_messages=True` in `CrawlerRunConfig`.

- `network_requests` (`Optional[List[Dict]]`): items with `event_type` `"request"`/`"response"`/`"request_failed"` plus `timestamp`. Request events add `url`, `method`, `headers`, `post_data`, `resource_type`, `is_navigation_request`; response events add `status`, `status_text`, `request_timing`; failed events add `failure_text`.
- `console_messages` (`Optional[List[Dict]]`): items with `type` (`"log"`, `"error"`, `"warning"`, ...), `text`, optional `location` (URL/line/column), `timestamp`.

### Deprecated Legacy Properties

`markdown_v2` — removed in v0.5, raises `AttributeError`; use `result.markdown`. Top-level `fit_markdown`/`fit_html` — no longer top-level in v0.5; use `result.markdown.fit_markdown`/`fit_html`.

## Handling errors, links & media

### Standard error handling

```python
result = await crawler.arun("https://example.com", config=CrawlerRunConfig())
if not result.success:
    print(f"Crawl failed: {result.error_message}")
    print(f"Status code: {result.status_code}")
```

### Link/media processing

```python
for img in result.media["images"]:
    print(img["src"], img.get("alt"), img.get("score"))
for link in result.links["internal"]:
    print(link["href"])
```
