# Regex Extraction

Read when extracting simple data types (emails, URLs, prices, dates) with `RegexExtractionStrategy`.

## 4. RegexExtractionStrategy

Fast pattern matching, zero LLM. Built-in patterns combine with `|`:

```python
from crawl4ai import RegexExtractionStrategy

# Built-ins: Email, PhoneUS, PhoneIntl, Url, IPv4, IPv6, Uuid, Currency,
# Percentage, Number, DateIso, DateUS, Time24h, PostalUS, PostalUK, HexColor,
# TwitterHandle, Hashtag, MacAddr, Iban, CreditCard, All
strategy = RegexExtractionStrategy(
    pattern=RegexExtractionStrategy.Email | RegexExtractionStrategy.Url
)

# Custom patterns
strategy = RegexExtractionStrategy(
    custom={"usd_price": r"\$\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?"}
)
```

Results: `[{"url": ..., "label": "email", "value": ..., "span": [start, end]}, ...]`.

One-time LLM pattern generation, then cache and reuse (no further LLM calls):

```python
pattern = RegexExtractionStrategy.generate_pattern(
    label="price", html=html, query="Product prices in USD format",
    llm_config=LLMConfig(provider="openai/gpt-4o-mini", api_token="env:OPENAI_API_KEY"),
)
```
