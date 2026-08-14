# SSL Certificate Info

Read when the user needs certificate information (`fetch_ssl_certificate`, `SSLCertificate`).

## SSL Certificate

Set `fetch_ssl_certificate=True` in `CrawlerRunConfig`; the crawl result then carries `result.ssl_certificate`, an `SSLCertificate` instance (class in `crawl4ai/ssl_certificate.py`).

Properties: `issuer` (dict, e.g. `{"CN": ...}`), `subject` (dict), `valid_from`, `valid_until`, `fingerprint` (SHA-256 lowercase hex).

Export methods (all take an optional `filepath`; without it they return the string/bytes):

- `to_json(filepath=None)` → JSON string
- `to_pem(filepath=None)` → PEM string
- `to_der(filepath=None)` → DER bytes
- `export_as_text()` → OpenSSL-style textual form (optional helper)

```python
import asyncio, os
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode

async def main():
    config = CrawlerRunConfig(fetch_ssl_certificate=True, cache_mode=CacheMode.BYPASS)
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://example.com", config=config)
        if result.success and result.ssl_certificate:
            cert = result.ssl_certificate
            print("Issuer CN:", cert.issuer.get("CN", ""))
            print("Valid until:", cert.valid_until)
            print("Fingerprint:", cert.fingerprint)
            cert.to_json("certificate.json")
            cert.to_pem("certificate.pem")
            cert.to_der("certificate.der")

asyncio.run(main())
```

Standalone constructors: `SSLCertificate.from_url("https://example.com", timeout=10)` (default 10s socket connect), `from_file(path)` (ASN.1/DER), `from_binary(data)`. This only fetches and parses the certificate — it does **not** validate the chain or trust store. Combine with a proxy per request for the certificate as seen through that proxy.

---
