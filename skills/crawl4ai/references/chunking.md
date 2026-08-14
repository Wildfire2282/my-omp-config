# Chunking & Cosine Strategies

Read when splitting large text for extraction/RAG (chunking strategies) or semantic clustering (`CosineStrategy`).

## 7. Chunking strategies

Chunking splits large text before extraction/RAG. Import from `crawl4ai`:

- `RegexChunking(patterns=[r"\n\n"])` — paragraph-style splits (default strategy).
- `NlpSentenceChunking()` — sentence splits (NLTK).
- `TopicSegmentationChunking()` — TextTiling topic-coherent chunks.
- `FixedLengthWordChunking(chunk_size=100)` — fixed word windows.
- `SlidingWindowChunking(window_size=100, step=50)` — overlapping windows.
- `ClusterSemanticChunking(...)` — embedding-based semantic chunks.

Set via `CrawlerRunConfig(chunking_strategy=RegexChunking(...))`; use with extraction
strategies and RAG pipelines.

## 8. Cosine (clustering) strategy

Semantic clustering for topic extraction without an LLM:

```python
from crawl4ai import CosineStrategy

strategy = CosineStrategy(
    semantic_filter="customer reviews and ratings",  # target topic keywords
    word_count_threshold=20,    # min words per cluster
    sim_threshold=0.3,          # 0.0–1.0, higher = stricter grouping
    max_dist=0.2,               # max cluster distance
    linkage_method="ward",
    top_k=3,                    # top clusters to return
    model_name="sentence-transformers/all-MiniLM-L6-v2",
)
config = CrawlerRunConfig(extraction_strategy=strategy)
# result.extracted_content — JSON with clustered, relevant content
```

Typical uses: main article extraction (`semantic_filter="main article content"`,
`top_k=1`, `word_count_threshold=100`), review mining, doc slicing for RAG.
