# Capturing Network & Console Output

Read when capturing network requests or page console output for debugging.

## Network & Console Capture

Enable both in `CrawlerRunConfig`:

- `capture_network_requests=True` — records every request/response/failed request.
- `capture_console_messages=True` — records all browser console output.

Results: `result.network_requests` and `result.console_messages`, each a list of dicts.

`network_requests` items: `event_type` (`"request"`, `"response"`, `"request_failed"`), `url`, `timestamp`; request adds `method`, `headers`, `post_data`, `resource_type`, `is_navigation_request`; response adds `status`, `status_text`, `headers`, `from_service_worker`, `request_timing`; failed adds `method`, `resource_type`, `failure_text` (e.g. `"net::ERR_ABORTED 404"`).

`console_messages` items: `type` (`"log"`, `"error"`, `"warning"`, `"info"`, ...), `text`, `timestamp`, and usually `location` (`script.js:123:45`).

```python
import asyncio, json
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async def main():
    config = CrawlerRunConfig(capture_network_requests=True, capture_console_messages=True)
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="https://example.com", config=config)
        if result.success:
            reqs = result.network_requests or []
            api_calls = [r for r in reqs if r.get("event_type") == "request" and "api" in r.get("url", "")]
            print("Network events:", len(reqs), "| API calls:", [f"{c.get('method')} {c.get('url')}" for c in api_calls[:3]])
            msgs = result.console_messages or []
            errors = [m for m in msgs if m.get("type") == "error"]
            print("Console messages:", len(msgs), "| errors:", len(errors))
            for err in errors[:2]:
                print("  -", err.get("text", "")[:100])
            with open("network_capture.json", "w") as f:
                json.dump({"network_requests": reqs, "console_messages": msgs}, f, indent=2)

asyncio.run(main())
```

Use cases: hidden API endpoint discovery in SPAs, debugging JS errors, security auditing (unexpected third-party requests, data leakage), performance analysis (request timing), ad/tracker detection.

---
