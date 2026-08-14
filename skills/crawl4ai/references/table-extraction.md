# Table Extraction

Read when extracting HTML tables: `DefaultTableExtraction`, `LLMTableExtraction`, `NoTableExtraction`.

## 9. Table extraction

`DefaultTableExtraction` extracts tables automatically into `result.tables` (list of
`{"headers": [...], "rows": [[...]]}`) — no config needed.

- Scoring threshold: `CrawlerRunConfig(table_score_threshold=7)` (old-style) or

```python
from crawl4ai import DefaultTableExtraction, LLMTableExtraction, NoTableExtraction

config = CrawlerRunConfig(
    table_extraction=DefaultTableExtraction(
        table_score_threshold=7, min_rows=2, min_cols=2, verbose=True
    )
)
```

- `LLMTableExtraction(llm_config=..., css_selector="table", enable_chunking=True, chunk_token_threshold=3000, max_parallel_chunks=5)` — use **only** when the default fails
  on complex rowspan/colspan tables; it costs per call. Prefer fast providers (Groq,
  Cerebras) for large tables; the default handles ~95% of cases.
- `NoTableExtraction()` — disable table processing for text-only crawls.
