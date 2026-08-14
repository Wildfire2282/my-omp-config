# LLM Extraction & Schema Generation

Read when using `LLMExtractionStrategy` or generating extraction schemas with an LLM (`generate_schema`).

## 5. LLMExtractionStrategy

```python
from pydantic import BaseModel
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, LLMConfig, LLMExtractionStrategy

class Product(BaseModel):
    name: str
    price: str

strategy = LLMExtractionStrategy(
    llm_config=LLMConfig(provider="openai/gpt-4o-mini", api_token="env:OPENAI_API_KEY"),
    schema=Product.model_json_schema(),   # Pydantic → JSON schema
    extraction_type="schema",             # or "block" (freeform)
    instruction="Extract all products with name and price.",
    input_format="markdown",              # "markdown" | "html" | "fit_markdown"
    chunk_token_threshold=1000,           # max tokens per chunk
    overlap_rate=0.1,                     # context continuity across chunks
    apply_chunking=True,
    extra_args={"temperature": 0.0, "max_tokens": 800},
    verbose=True,
)
config = CrawlerRunConfig(extraction_strategy=strategy, cache_mode=CacheMode.BYPASS)

# after crawl: json.loads(result.extracted_content); strategy.show_usage() for tokens
```

Key parameters:

- `llm_config` — `LLMConfig(provider=..., api_token=...)`; provider is LiteLLM-style
  (`"openai/gpt-4o"`, `"ollama/llama3.3"`, `"groq/llama3-70b-8192"`, ...). Token via
  env var: `"env:OPENAI_API_KEY"`.
- `extraction_type` — `"schema"` (strict JSON per Pydantic schema) or `"block"`.
- `input_format` — which crawler output feeds the LLM; `"fit_markdown"` cuts tokens
  if a content filter is active.
- `apply_chunking` / `chunk_token_threshold` / `overlap_rate` — chunk pages
  larger than the model context; chunks can process in parallel (watch provider rate limits).
- `show_usage()` prints token/cost stats; `strategy.usages` / `strategy.total_usage` expose them directly.

Validate model output with Pydantic after parsing — LLMs occasionally omit fields
or emit malformed JSON.

## 6. Automatic schema generation (one-time LLM cost)

```python
from crawl4ai import JsonCssExtractionStrategy, JsonXPathExtractionStrategy, LLMConfig

schema = JsonCssExtractionStrategy.generate_schema(
    url="https://news.ycombinator.com",
    query="Extract each story: title, url, score, author",
    llm_config=LLMConfig(provider="openai/gpt-4o", api_token="..."),
    validate=True,        # validates + auto-refines selectors (default)
    schema_type="css",    # or "xpath"
)
```

- Works on `url=`, raw `html=`, or multiple HTML samples (multi-sample generation
  produces stable selectors — avoid fragile `tr:nth-child(n)` positional selectors;
  request href/data-attribute based selectors instead).
- Pass a `TokenUsage()` accumulator to track cost: `usage = TokenUsage()` then
  `generate_schema(..., usage=usage)`.
- Async variant: `agenerate_schema(...)`.
- Cache generated schemas to disk — reuse is free.
