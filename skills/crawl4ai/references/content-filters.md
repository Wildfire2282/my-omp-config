# Content Filters (Pruning / BM25 / LLM)

Read when the user wants filtered 'fit markdown' — boilerplate removal, query-focused relevance, or LLM-curated content.

## Content filters

### PruningContentFilter — no query, generic junk removal

Scores nodes by text density, link density, tag importance, structural context
(sidebars, deep nesting), and drops low scorers.

```python
from crawl4ai.content_filter_strategy import PruningContentFilter

prune_filter = PruningContentFilter(
    threshold=0.48,             # lower → keep more; higher → prune more
    threshold_type="dynamic",   # "fixed" = score >= threshold; "dynamic" = adaptive
    min_word_threshold=50,      # drop blocks under N words
)
```

Use when: the page has nav bars, sidebars, footers, disclaimers, or you want
the "meatiest" text without a query. Adds ~50ms.

### BM25ContentFilter — query-focused relevance

```python
from crawl4ai.content_filter_strategy import BM25ContentFilter

bm25_filter = BM25ContentFilter(
    user_query="startup fundraising tips",
    bm25_threshold=1.2,      # higher → fewer, more relevant blocks (default 1.0)
    language="english",      # stemming language
    use_stemming=True,
)
```

Use when: the user has a specific query ("extract only content about X").
Without `user_query`, it tries page metadata or degrades to generic scoring —
always supply a query for best results.

### LLMContentFilter — LLM-curated Markdown

```python
from crawl4ai import LLMConfig, DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import LLMContentFilter

filter = LLMContentFilter(
    llm_config=LLMConfig(provider="openai/gpt-4o", api_token="..."),
    instruction="""Extract the core educational content. Include key concepts
    and code examples. Exclude navigation, sidebars, footers. Output clean
    markdown.""",
    chunk_token_threshold=4096,  # smaller (2048/4096) enables parallel chunk processing
    verbose=True,
)
config = CrawlerRunConfig(
    markdown_generator=DefaultMarkdownGenerator(content_filter=filter)
)
# result.markdown.fit_markdown
```

Two common instruction modes:

1. **Exact preservation** — keep original wording, only remove clearly irrelevant elements.
2. **Focused extraction** — pull specific content types (docs, code, API refs) and reformat.
