# Cache Control

Read when the user cares about cache behavior (fresh vs cached content, cache modes).

## Caching

`CacheMode` enum in `CrawlerRunConfig`:

| Mode | Behavior |
|---|---|
| `CacheMode.ENABLED` | Normal read/write cache |
| `CacheMode.DISABLED` | No caching at all |
| `CacheMode.READ_ONLY` | Read cache, never write |
| `CacheMode.WRITE_ONLY` | Write cache, never read |
| `CacheMode.BYPASS` | Skip cache entirely (fresh fetch) |

```python
from crawl4ai import CrawlerRunConfig, CacheMode

config = CrawlerRunConfig(cache_mode=CacheMode.ENABLED)
```

Deprecated legacy flags (replaced by `cache_mode`): `bypass_cache`, `disable_cache`,
`no_cache_read`, `no_cache_write`.
