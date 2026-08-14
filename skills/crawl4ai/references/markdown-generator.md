# Markdown Generation

Read when producing markdown output: generator options, link citations, `content_source`, multi-level filtering, custom filters.

## How it works

`DefaultMarkdownGenerator` converts the crawled HTML into Markdown. Attach a
**content filter** to prune or rank content before conversion. With a filter,
`result.markdown` exposes both `raw_markdown` (unfiltered) and `fit_markdown`
(filtered); without one, only raw output is produced.

```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

config = CrawlerRunConfig(markdown_generator=DefaultMarkdownGenerator())

async with AsyncWebCrawler() as crawler:
    result = await crawler.arun("https://example.com", config=config)
    print(result.markdown.raw_markdown)
```

## Generator options

```python
md_generator = DefaultMarkdownGenerator(
    options={
        "ignore_links": True,       # drop all hyperlinks
        "ignore_images": True,      # drop image references from output
        "escape_html": True,        # HTML entities as text
        "body_width": 80,           # wrap at N chars (0/None = no wrap)
        "skip_internal_links": True,# omit #anchors / same-page links
        "include_sup_sub": True,    # readable <sup>/<sub>
    }
)
```

Links can be rendered as academic-style citations: `[text][1]` with a
references section at the bottom (see `references_markdown`).

### Choosing the HTML source: `content_source`

| Value | Input HTML | Use when |
|---|---|---|
| `"cleaned_html"` (default) | HTML after scraping-strategy cleaning | Most cases |
| `"raw_html"` | Original page HTML, unprocessed | Need everything, cleaning drops wanted content |
| `"fit_html"` | HTML preprocessed for schema extraction | Structured data pipelines |

```python
DefaultMarkdownGenerator(content_source="raw_html", options={"ignore_links": True})
```

## Multi-level filtering

`word_count_threshold`, `excluded_tags`, and `exclude_external_links` in
`CrawlerRunConfig` work *before* the content filter:

1. `excluded_tags`/`excluded_selector` remove HTML elements first.
2. The content filter (Pruning/BM25/LLM) prunes or ranks remaining blocks.
3. `fit_markdown` is generated from what survives.

```python
config = CrawlerRunConfig(
    word_count_threshold=10,
    excluded_tags=["nav", "footer", "header"],
    exclude_external_links=True,
    markdown_generator=DefaultMarkdownGenerator(
        content_filter=PruningContentFilter(threshold=0.5)
    ),
)
```

## Accessing fit output

```python
result.markdown.fit_markdown   # filtered markdown
result.markdown.fit_html       # HTML that produced fit_markdown
```

## Custom filters

Subclass `RelevantContentFilter` and implement `filter_content(html, min_word_threshold=None)`,
then pass it to the generator:

```python
from crawl4ai.content_filter_strategy import RelevantContentFilter

class MyFilter(RelevantContentFilter):
    def filter_content(self, html, min_word_threshold=None):
        ...  # custom logic, return list of kept blocks

md_generator = DefaultMarkdownGenerator(content_filter=MyFilter())
```

## Selection shortcuts

- `css_selector="main.article"` — keep only the matching region for the whole pipeline.
- `target_elements=["h1", "article"]` — focus markdown + extraction on these,
  while still collecting all links/media.
