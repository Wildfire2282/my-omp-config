# Extraction & Chunking Strategies API

Read when you need the extraction / chunking / filter strategy class hierarchy and their parameters.

## Extraction & Chunking Strategies

All extraction strategies inherit from `ExtractionStrategy` and implement `extract(url: str, html: str) -> List[Dict[str, Any]]` and `run(url: str, sections: List[str]) -> List[Dict[str, Any]]`; chunking strategies inherit from `ChunkingStrategy` and implement `chunk(text: str) -> list`.

### LLMExtractionStrategy

```python
LLMExtractionStrategy(
    llm_config=LLMConfig(provider="ollama/llama2"),  # preferred over legacy provider/api_token
    instruction: str = None,            # custom extraction instruction
    schema: Dict = None,                # Pydantic model schema for structured data
    extraction_type: str = "block",     # "block" or "schema"
    chunk_token_threshold: int = 4000,  # max tokens per chunk
    overlap_rate: float = 0.1,          # overlap between chunks
    word_token_rate: float = 0.75,      # word→token conversion rate
    apply_chunking: bool = True,        # enable/disable chunking
    base_url: str = None, extra_args: Dict = {}, verbose: bool = False,
)
```

```python
from pydantic import BaseModel
from crawl4ai import LLMExtractionStrategy, LLMConfig
class Article(BaseModel):
    title: str
    content: str
    author: str
strategy = LLMExtractionStrategy(llm_config=LLMConfig(provider="ollama/llama2"), schema=Article.schema())
result = await crawler.arun(url="https://example.com/article", extraction_strategy=strategy)
data = json.loads(result.extracted_content)
```

### RegexExtractionStrategy

Fast, pattern-based extraction. `pattern` is an `IntFlag` bitmask; `custom` is `{label: regex}`; `input_format` is `"html"`, `"markdown"`, `"text"`, or `"fit_html"` (default).

Built-in flags: `Email`, `PhoneIntl`, `PhoneUS`, `Url`, `IPv4`, `IPv6`, `Uuid`, `Currency`, `Percentage`, `Number`, `DateIso`, `DateUS`, `Time24h`, `PostalUS`, `PostalUK`, `HexColor`, `TwitterHandle`, `Hashtag`, `MacAddr`, `Iban`, `CreditCard`, `All`.

```python
strategy = RegexExtractionStrategy(pattern=RegexExtractionStrategy.Email | RegexExtractionStrategy.Url)
strategy = RegexExtractionStrategy(custom={"usd_price": r"\$\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?"})
```

One-time LLM-assisted pattern generation (no LLM calls at extraction time); results are `{"label": ..., "value": ...}` items — see `regex-extraction.md` for a full example.

### CosineStrategy

Content-similarity extraction/clustering. Params: `semantic_filter` (topic filter), `word_count_threshold=10`, `sim_threshold=0.3`, `max_dist=0.2`, `linkage_method='ward'`, `top_k=3`, `model_name='sentence-transformers/all-MiniLM-L6-v2'`, `verbose=False`.

### JsonCssExtractionStrategy / JsonXPathExtractionStrategy

Schema-driven structured extraction (CSS or XPath selectors):

```python
schema = {"name": "Product List", "baseSelector": ".product-card",
          "fields": [
              {"name": "title", "selector": "h2.title", "type": "text"},
              {"name": "price", "selector": ".price", "type": "text", "transform": "strip"},
              {"name": "image", "selector": "img", "type": "attribute", "attribute": "src"}]}
strategy = JsonCssExtractionStrategy(schema)
result = await crawler.arun(url, extraction_strategy=strategy)
```

Field keys: `name`, `selector`, `type` (`"text"`, `"attribute"`, `"html"`, `"regex"`), `attribute` (for `type="attribute"`), `pattern` (for `type="regex"`), `transform` (`"lowercase"`, `"uppercase"`, `"strip"`), `default` (fallback), `source` (sibling navigation, e.g. `"+ tr"`). Top-level: `name`, `baseSelector`, `fields`. `JsonXPathExtractionStrategy` is the XPath counterpart; both offer `generate_schema(...)` LLM-assisted schema generation.

### Chunking Strategies

| Strategy | Key Parameters | Notes |
| --- | --- | --- |
| `RegexChunking` | `patterns: List[str] = None` | Default `[r'\n\n']`; also the default `chunking_strategy` of `CrawlerRunConfig`. |
| `SlidingWindowChunking` | `window_size: int = 100`, `step: int = 50` | Overlapping chunks via sliding window (words). |
| `OverlappingWindowChunking` | `window_size: int = 1000`, `overlap: int = 100` | Chunks with explicit word overlap. |
| `NLPChunking` | — | Sentence-aware chunking (`crawl4ai.chunking_strategy`). |
| `ClusterSemanticChunking` | — | Semantic-similarity-based chunking (`crawl4ai.chunking_strategy`). |

```python
from crawl4ai.chunking_strategy import OverlappingWindowChunking
chunker = OverlappingWindowChunking(window_size=500, overlap=50)
strategy = LLMExtractionStrategy(llm_config=LLMConfig(provider="ollama/llama2"), chunking_strategy=chunker)
```

### Content Filters & Markdown Generation

- `PruningContentFilter` — relevance-based pruning; e.g. `PruningContentFilter(threshold=0.48)`.
- `BM25ContentFilter` — keyword/BM25-based filtering.
- `LLMContentFilter` — LLM-based filtering; configure with `LLMConfig`.
- `DefaultMarkdownGenerator` — markdown generation strategy; accepts `content_filter` and `options` such as `{"citations": True}` (yields `markdown_with_citations` + `references_markdown`).

```python
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
run_cfg = CrawlerRunConfig(
    markdown_generator=DefaultMarkdownGenerator(content_filter=PruningContentFilter(threshold=0.48)))
```

### LLMConfig

Shared LLM provider config usable in `LLMExtractionStrategy`, `LLMContentFilter`, `JsonCssExtractionStrategy.generate_schema`, `JsonXPathExtractionStrategy.generate_schema`, and `AdaptiveConfig` (`embedding_llm_config`/`query_llm_config`).

| Parameter | Type / Default | What It Does |
| --- | --- | --- |
| `provider` | e.g. `"openai/gpt-4o-mini"` (default), `"ollama/llama3"`, `"groq/llama3-70b-8192"`, `"anthropic/claude-3-5-sonnet-20240620"`, `"gemini/gemini-2.0-flash"`, `"deepseek/deepseek-chat"` | LLM provider. |
| `api_token` | Optional | Read from provider-specific env var when omitted (e.g. `GEMINI_API_KEY`), `"env:VAR_NAME"` prefix, or literal token. |
| `base_url` | Optional | Custom API endpoint. |
| `backoff_base_delay` | `int` (2) | Seconds before first retry on throttling. |
| `backoff_max_attempts` | `int` (3) | Total tries (initial + retries). |
| `backoff_exponential_factor` | `int` (2) | Retry multiplier (`delay = base_delay * factor^attempt`). |

```python
llm_config = LLMConfig(provider="openai/gpt-4o-mini", api_token=os.getenv("OPENAI_API_KEY"), backoff_base_delay=1, backoff_max_attempts=5, backoff_exponential_factor=3)
```

### Strategy Selection Guide

Common data types (email/phone/date/URL) → `RegexExtractionStrategy`; consistent HTML structure → `JsonCssExtractionStrategy` or `JsonXPathExtractionStrategy`; semantically complex/unstructured content → `LLMExtractionStrategy`; content similarity/clustering → `CosineStrategy`.

Best practices: for long documents lower `chunk_token_threshold` (e.g. 2000) with `overlap_rate=0.1`; combine strategies in passes (CSS structure first, regex for specific fields); wrap `arun()` in try/except; cache generated regex patterns to disk.
