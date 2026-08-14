# PDF Parsing & File Downloads

Read when crawling PDF files or handling file downloads (`accept_downloads`, `downloads_path`).

## PDF Parsing

Two strategy classes in `crawl4ai.processors.pdf`:

- `PDFCrawlerStrategy(AsyncCrawlerStrategy)` — treats the URL as a pointer to a PDF (web URL or local `file:///path`); it does not parse HTML — it hands the PDF source to the scraping strategy. Set `response_headers` to `application/pdf`, status 200.
- `PDFContentScrapingStrategy(ContentScrapingStrategy)` — extracts text page-by-page, metadata, and optionally images, using `NaivePDFProcessorStrategy` internally. Output lands in the standard `CrawlResult` (`result.markdown.raw_markdown`, `result.metadata`, `result.media["images"]`).

Constructor options for `PDFContentScrapingStrategy`: `extract_images: bool = False`, `save_images_locally: bool = False`, `image_save_dir: str = None`, `batch_size: int = 4`, `logger=None`.

```python
import asyncio, os
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.processors.pdf import PDFCrawlerStrategy, PDFContentScrapingStrategy

async def main():
    pdf_scraping = PDFContentScrapingStrategy(
        extract_images=True, save_images_locally=True, image_save_dir="./my_pdf_images", batch_size=2)
    async with AsyncWebCrawler(crawler_strategy=PDFCrawlerStrategy()) as crawler:
        result = await crawler.arun(url="https://arxiv.org/pdf/2310.06825.pdf",
                                    config=CrawlerRunConfig(scraping_strategy=pdf_scraping))
        if result.success:
            print("Title:", result.metadata.get("title", "N/A"))
            print("Pages:", result.metadata.get("num_pages", "N/A"))
            print("Text:", result.markdown.raw_markdown[:200])
            print("Images:", len(result.media.get("images", [])))

asyncio.run(main())
```

In multi-URL mode, route PDF URLs to the PDF strategy with `url_matcher` (no separate `PDFCrawlerStrategy` needed):

```python
from crawl4ai import CrawlerRunConfig
from crawl4ai.processors.pdf import PDFContentScrapingStrategy

config = CrawlerRunConfig(
    url_matcher="*.pdf",
    scraping_strategy=PDFContentScrapingStrategy(),
)
```

Limitations (documented): extraction quality depends on the PDF (scanned/image-based PDFs yield no text without OCR — not included); image extraction is resource-intensive; `NaivePDFProcessorStrategy` may struggle with complex layouts, encrypted PDFs, or forms; link extraction is basic.

---

## File Downloading

Enable downloads at the browser level, trigger them with JS, and collect paths from the result:

- `BrowserConfig(accept_downloads=True)` — enable downloads.
- `BrowserConfig(downloads_path=...)` — where files land; default is a `downloads` directory inside `~/.crawl4ai/`.
- Trigger clicks with `js_code` in `CrawlerRunConfig`; give the download time with `wait_for=<seconds>`.
- `result.downloaded_files` — list of absolute paths to downloaded files.

```python
import asyncio, os
from crawl4ai.async_configs import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

async def main():
    downloads_path = os.path.join(os.getcwd(), "my_downloads")
    os.makedirs(downloads_path, exist_ok=True)

    config = BrowserConfig(accept_downloads=True, downloads_path=downloads_path)
    async with AsyncWebCrawler(config=config) as crawler:
        run_config = CrawlerRunConfig(
            js_code="const link = document.querySelector('a[download]'); if (link) link.click();",
            wait_for=10,  # wait for the download to start
        )
        result = await crawler.arun(url="https://www.python.org/downloads/windows/", config=run_config)

        if result.downloaded_files:
            for file_path in result.downloaded_files:
                print("-", file_path, os.path.getsize(file_path), "bytes")
        else:
            print("No files downloaded.")

asyncio.run(main())
```

Considerations: downloads live inside the browser context, so `js_code` must target the real download triggers; use `wait_for` for timing; handle failed downloads/incorrect paths gracefully; scan downloaded files for security threats before use.

---
