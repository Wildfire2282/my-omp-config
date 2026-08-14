# CSS & XPath Schema Extraction

Read when building `JsonCssExtractionStrategy` / `JsonXPathExtractionStrategy` schemas: field types, nesting, baseFields, sibling `source`.

## 1. Schema-based extraction (CSS)

```python
import json
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, JsonCssExtractionStrategy

schema = {
    "name": "Crypto Prices",
    "baseSelector": "div.crypto-row",        # repeated container
    "fields": [
        {"name": "coin_name", "selector": "h2.coin-name", "type": "text"},
        {"name": "price", "selector": "span.coin-price", "type": "text"},
        {"name": "link", "selector": "a", "type": "attribute", "attribute": "href"},
    ],
}

config = CrawlerRunConfig(extraction_strategy=JsonCssExtractionStrategy(schema))
async with AsyncWebCrawler() as crawler:
    result = await crawler.arun("https://example.com/prices", config=config)
    data = json.loads(result.extracted_content)  # list[dict]
```

### Field `type` reference

| type | Meaning |
|---|---|
| `"text"` | Inner text of the matched element |
| `"attribute"` | Attribute value — needs `"attribute": "href"` |
| `"html"` | Inner HTML |
| `"regex"` | Regex match against the element |
| `"nested"` | Single sub-object; define `"fields"` inside |
| `"list"` | Multiple simple items (dicts or single text via one inner field) |
| `"nested_list"` | Repeated complex objects with `"fields"` |

Optional keys: `"default"` (fallback when missing), `"transform"` (e.g. lowercase),
`"source"` (reach sibling elements — see below).

### `baseFields` — attributes of the container

```python
schema = {
    "name": "Blog Posts",
    "baseSelector": "a.blog-post-card",
    "baseFields": [{"name": "post_url", "type": "attribute", "attribute": "href"}],
    "fields": [
        {"name": "title", "selector": "h2.post-title", "type": "text", "default": "No Title"},
        {"name": "date", "selector": "time.post-date", "type": "text"},
    ],
}
```

### Nested structures (products → details → features)

```python
schema = {
    "name": "Catalog",
    "baseSelector": "div.category",
    "baseFields": [{"name": "cat_id", "type": "attribute", "attribute": "data-cat-id"}],
    "fields": [
        {"name": "category_name", "selector": "h2.category-name", "type": "text"},
        {"name": "products", "selector": "div.product", "type": "nested_list", "fields": [
            {"name": "name", "selector": "h3.product-name", "type": "text"},
            {"name": "price", "selector": "p.product-price", "type": "text"},
            {"name": "details", "selector": "div.product-details", "type": "nested", "fields": [
                {"name": "brand", "selector": "span.brand", "type": "text"},
            ]},
            {"name": "features", "selector": "ul.product-features li", "type": "list",
             "fields": [{"name": "feature", "type": "text"}]},
        ]},
    ],
}
```

## 2. XPath variant

`JsonXPathExtractionStrategy` — same schema shape, but `baseSelector` and every
field `"selector"` use XPath:

```python
from crawl4ai import JsonXPathExtractionStrategy

schema = {
    "name": "Prices via XPath",
    "baseSelector": "//div[@class='crypto-row']",
    "fields": [
        {"name": "coin_name", "selector": ".//h2[@class='coin-name']", "type": "text"},
    ],
}
config = CrawlerRunConfig(extraction_strategy=JsonXPathExtractionStrategy(schema))
```

## 3. Sibling data with `source`

When one logical item spans sibling elements (classic Hacker News two-`<tr>` rows),
use `"source": "+ selector"` to hop to a sibling before running the field selector:

```python
schema = {
    "name": "HN Submissions",
    "baseSelector": "tr.athing.submission",
    "fields": [
        {"name": "title", "selector": "span.titleline a", "type": "text"},
        {"name": "score", "selector": "span.score", "type": "text", "source": "+ tr"},
        {"name": "author", "selector": "a.hnuser", "type": "text", "source": "+ tr"},
    ],
}
```

`source` works with all field types and both strategies. Missing sibling → `default`.
