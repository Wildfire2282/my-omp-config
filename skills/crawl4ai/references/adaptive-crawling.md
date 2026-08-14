# Adaptive Crawling

Read when answering a research-style question over a whole site: `AdaptiveCrawler`, `digest()`, `AdaptiveConfig`.

## Adaptive Crawling (AdaptiveConfig / AdaptiveCrawler)

The adaptive crawler targets query-driven knowledge-base building. It scores pages via a **three-layer system** and ranks uncrawled links by expected information gain.

- **Coverage score** — how well crawled docs cover query terms: `confidence_threshold`, `top_k_links`.
- **Consistency score** — cross-document agreement (0–1); `>0.8` coherent, `<0.5` conflicting.
- **Saturation score** — stops when new pages stop adding novel terms: `min_gain_threshold` (stop if new info < threshold).

`AdaptiveConfig` parameters seen in the docs: `confidence_threshold`, `top_k_links`, `max_pages`, `min_gain_threshold`, `save_state`, `state_path`. Link ranking = `Relevance (BM25 on preview text) × Novelty (1 - max_similarity to KB) × Authority (domain/URL structure)`.

```python
import asyncio, logging
from crawl4ai import AsyncWebCrawler, BrowserConfig
from crawl4ai.adaptive_crawler import AdaptiveCrawler, AdaptiveConfig

async def main():
    config = AdaptiveConfig(
        confidence_threshold=0.85,   # technical docs: high coverage bar
        max_pages=30,
        top_k_links=3,
        min_gain_threshold=0.05,     # keep crawling for small gains
    )
    crawler = AsyncWebCrawler(config=BrowserConfig(headless=True))
    adaptive = AdaptiveCrawler(crawler, config=config, verbose=True)
    state = await adaptive.digest("https://docs.example.com/intro", "what is the API?")
    print("Pages crawled:", len(state.crawled_urls))
    print("Coverage:", adaptive.coverage_stats)
    await crawler.close()

asyncio.run(main())
```

Domain presets from the docs: news/articles lower `confidence_threshold` (0.6) + higher `min_gain_threshold` (0.15) to stop on repetition; e-commerce balanced (0.7 / 0.1 / `top_k_links=2`); research: high threshold (0.9), many pages (50), low gain (0.02).

Custom strategies subclass `CrawlStrategy` and override `calculate_coverage`, `calculate_consistency`, `rank_links`; pass the instance to `AdaptiveCrawler(crawler, config=config, strategy=CustomStrategy())`. `AdaptiveCrawler` also exposes `get_relevant_content(top_k=N)` to validate the knowledge base. Best practices: start conservative and tune (`if adaptive.confidence < 0.7: config.max_pages += 10`); monitor memory before large crawls; adjust `top_k_links`/`min_gain_threshold` to the domain.

---

## AdaptiveCrawler

Intelligent crawling that stops automatically once enough information has been gathered for a query, using a three-layer scoring system (coverage, consistency, saturation).

### Constructor & Properties

```python
AdaptiveCrawler(crawler: AsyncWebCrawler, config: Optional[AdaptiveConfig] = None)
```

| Property | Type | What It Is |
| --- | --- | --- |
| `confidence` | `float` | Current confidence score (0-1) of information sufficiency. |
| `coverage_stats` | `Dict[str, float]` | `coverage`, `consistency`, `saturation`, `confidence`. |
| `is_sufficient` | `bool` | Whether sufficient information has been gathered. |
| `state` | `CrawlState` | Current crawl state. |

### Methods

| Method | Signature | What It Does |
| --- | --- | --- |
| `digest()` | `async digest(start_url, query, resume_from=None) -> CrawlState` | Main adaptive crawl entry point. |
| `get_relevant_content()` | `get_relevant_content(top_k: int = 5) -> List[Dict[str, Any]]` | Top relevant docs; each dict: `url`, `content`, `score`, `metadata`. |
| `print_stats()` | `print_stats(detailed: bool = False) -> None` | Summary table, or detailed colored metrics when `detailed=True`. |
| `export_knowledge_base()` | `export_knowledge_base(path: Union[str, Path]) -> None` | Export knowledge base to JSONL. |
| `import_knowledge_base()` | `async import_knowledge_base(path: Union[str, Path]) -> None` | Import a previously exported JSONL knowledge base. |

### AdaptiveConfig

```python
@dataclass
class AdaptiveConfig:
    confidence_threshold: float = 0.8   # stop when confidence reaches this
    max_pages: int = 50                 # maximum pages to crawl
    top_k_links: int = 5                # links to follow per page
    min_gain_threshold: float = 0.1     # minimum expected gain to continue
    save_state: bool = False            # auto-save crawl state
    state_path: Optional[str] = None    # path for state persistence
    embedding_llm_config: Optional[LLMConfig] = None  # embedding model for adaptive crawling
    query_llm_config: Optional[LLMConfig] = None      # chat completion model for query expansion
```

Usage: `adaptive.export_knowledge_base("kb.jsonl")` exports the knowledge base; `get_relevant_content(top_k=3)` returns the top relevant pages.

## digest()

Primary adaptive-crawling interface: crawls from a start URL guided by a query and stops automatically once sufficient information has been gathered.

### Signature & Parameters

```python
async def digest(start_url: str, query: str, resume_from: Optional[Union[str, Path]] = None) -> CrawlState
```

| Parameter | Type | Required | What It Does |
| --- | --- | --- | --- |
| `start_url` | `str` | Yes | Entry-point URL (valid HTTP/HTTPS). |
| `query` | `str` | Yes | Search query guiding relevance evaluation and link selection. |
| `resume_from` | `Optional[Union[str, Path]]` | No | Path to a previously saved crawl state file; resumes instead of starting fresh. |

### Return Value: `CrawlState`

- `crawled_urls` (`Set[str]`): all crawled URLs.
- `knowledge_base` (`List[CrawlResult]`): crawled pages with content.
- `pending_links` (`List[Link]`): discovered but not yet crawled links.
- `metrics` (`Dict[str, float]`): performance and quality metrics; `query` (`str`): the original query; plus additional statistical information for scoring.

### How It Works

1. **Initial crawl** → **link analysis** (relevance) → **scoring** with three metrics — **coverage** (query-term coverage), **consistency** (coherence across pages), **saturation** (diminishing returns) → **adaptive selection** of the most promising links → **stopping decision** at the confidence threshold.

### Examples

```python
async with AsyncWebCrawler() as crawler:
    adaptive = AdaptiveCrawler(crawler)
    state = await adaptive.digest("https://docs.python.org/3/", "async await context managers")
    print(f"Crawled {len(state.crawled_urls)} pages, confidence: {adaptive.confidence:.0%}")
    adaptive.print_stats(detailed=True)   # progress monitoring
```

Resume a previous crawl:

```python
state1 = await adaptive.digest("https://example.com", "machine learning algorithms")
state1.save("ml_crawl_state.json")
state2 = await adaptive.digest("https://example.com", "machine learning algorithms", resume_from="ml_crawl_state.json")
```

### Stopping Conditions

Crawl stops when any of: (1) **confidence threshold** reached; (2) **page limit** reached (`max_pages`); (3) **diminishing returns** — expected information gain below `min_gain_threshold`; (4) **no relevant links** remain. Query best practices: be specific ("python async context managers implementation" — not "python programming"), include key technical terms ("oauth2 jwt refresh tokens authorization"), combine related concepts ("rest api pagination sorting filtering"); 3-8 terms work best; prefer a start URL with good navigation (e.g. docs index); enable caching for repeated crawls.
