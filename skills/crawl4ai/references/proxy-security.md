# Proxies & Security

Read when routing crawls through proxies or configuring per-crawl proxy behavior.

## Proxy & Security

Configure proxies **per request** via `CrawlerRunConfig.proxy_config` (the legacy `proxy` argument on `BrowserConfig` is deprecated). `proxy_config` accepts any of:

- a plain string: `"http://proxy.example.com:8080"`
- a dict: `{"server": "http://proxy.example.com:8080", "username": "u", "password": "p"}`
- a `ProxyConfig` object
- a `list[ProxyConfig]` (used for anti-bot escalation, see Anti-Bot section)

```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, ProxyConfig

async def main():
    run_config = CrawlerRunConfig(
        proxy_config=ProxyConfig(
            server="http://proxy.example.com:8080",
            username="your_username",
            password="your_password",
        )
    )
    async with AsyncWebCrawler(config=BrowserConfig()) as crawler:
        result = await crawler.arun(url="https://example.com", config=run_config)
        print(f"Success: {result.success} -> {result.url}")

asyncio.run(main())
```

`ProxyConfig` helpers:

- `ProxyConfig.from_string(...)` — parses many formats: `http://user:pass@192.168.1.1:8080`, `https://proxy.example.com:8080`, `socks5://proxy.example.com:1080`, `192.168.1.1:8080`, `192.168.1.1:8080:user:pass`.
- `ProxyConfig.from_env("PROXIES")` — loads a comma-separated env var (`ip1:port1:user1:pass1,ip2:port2:user2:pass2`) into a list of proxies. `os.environ["PROXIES"] = "ip1:port1:user1:pass1,ip2:port2:user2:pass2"`.

Proxy rotation: attach a rotation strategy so each request in `arun_many()` uses the next proxy:

```python
import asyncio, re
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, ProxyConfig
from crawl4ai.proxy_strategy import RoundRobinProxyStrategy

async def main():
    proxies = ProxyConfig.from_env()  # PROXIES env var must be set
    if not proxies:
        print("No proxies found"); return
    run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS,
                                  proxy_rotation_strategy=RoundRobinProxyStrategy(proxies))
    async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
        results = await crawler.arun_many(urls=["https://httpbin.org/ip"] * (len(proxies) * 2), config=run_config)
        for i, r in enumerate(results):
            if r.success:
                ip = re.search(r'(?:[0-9]{1,3}\.){3}[0-9]{1,3}', r.html)
                print(f"Request {i+1} -> IP {ip.group(0) if ip else '?'}")

asyncio.run(main())
```

Security best practices: prefer SOCKS5 (`proxy_config="socks5://proxy.example.com:1080"`) for better protocol support; keep credentials in env vars, not code; don't log proxy passwords (mask auth); some proxies break SSL inspection — switch proxies if repeated SSL failures.

---
