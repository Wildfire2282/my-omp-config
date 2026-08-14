# C4A-Script Reference

Read when writing C4A-Script (visual automation scripts): commands, syntax, control flow.

## C4A-Script

Line-oriented DSL executed in the browser context to drive dynamic pages. Enable via `CrawlerRunConfig(c4a_script=script, ...)`:

```python
script = """
WAIT `.content` 5
IF (EXISTS `.load-more-button`) THEN CLICK `.load-more-button`
WAIT `.additional-content` 5
IF (EXISTS `.cookie-banner`) THEN CLICK `.accept-all`
"""
async with AsyncWebCrawler() as crawler:
    result = await crawler.arun("https://example.com",
                                config=CrawlerRunConfig(c4a_script=script, wait_for=".content", screenshot=True))
    print(result.markdown)
```

### Command Reference

| Category | Command | Syntax | Notes |
| --- | --- | --- | --- |
| Navigation | `GO` | `GO <url>` | Absolute or relative URL; waits for page load. |
| Navigation | `RELOAD` | `RELOAD` | Refresh current page. |
| Navigation | `BACK` / `FORWARD` | `BACK` / `FORWARD` | Browser history; no-op if none. |
| Wait | `WAIT <seconds>` | `WAIT 3` / `WAIT 1.5` | Fixed wait; decimals allowed. |
| Wait | `WAIT <selector>` | `WAIT #content 10` | Waits for element; fails if not present within timeout. |
| Wait | `WAIT <text>` | `WAIT "Loading complete" 10` | Case-sensitive page-text wait. |
| Mouse | `CLICK` | `CLICK #submit` or `CLICK <x> <y>` | Selector-based (waits, scrolls into view) or viewport coordinates. |
| Mouse | `DOUBLE_CLICK` | `DOUBLE_CLICK <sel>` | Triggers `dblclick`. |
| Mouse | `RIGHT_CLICK` | `RIGHT_CLICK <sel>` | Opens context menu. |
| Mouse | `SCROLL` | `SCROLL <UP`\|`DOWN`\|`LEFT`\|`RIGHT> <amount>` | Smooth scrolling. |
| Mouse | `MOVE` | `MOVE <x> <y>` | Move cursor (hover). |
| Mouse | `DRAG` | `DRAG <x1> <y1> <x2> <y2>` | Click-drag-release. |
| Keyboard | `TYPE` | `TYPE "<text>"` | Types into focused element with realistic timing. |
| Keyboard | `TYPE $var` | `TYPE $<variable>` | Types a `SETVAR` value. |
| Keyboard | `PRESS` | `PRESS <key>` | Keys: `Tab`, `Enter`, `Escape`, `Space`, `ArrowUp/Down/Left/Right`, `Delete`, `Backspace`, `Home`, `End`, `PageUp`, `PageDown` (case-sensitive). |
| Keyboard | `KEY_DOWN`/`KEY_UP` | `KEY_DOWN <key>` / `KEY_UP <key>` | Modifiers: `Shift`, `Control`, `Alt`, `Meta`; must be paired. |
| Keyboard | `CLEAR` | `CLEAR <sel>` | Clears input/textarea. |
| Keyboard | `SET` | `SET <sel> "<value>"` | Sets field value directly; fires change/input events. |
| Control | `IF (EXISTS ...)` | `IF (EXISTS <sel>) THEN <cmd> [ELSE <cmd>]` | Exactly one command runs. |
| Control | `IF (NOT EXISTS ...)` | `IF (NOT EXISTS <sel>) THEN <cmd>` | Inverse of EXISTS. |
| Control | `IF (JS)` | `IF (<js>) THEN <cmd>` | JS must return boolean; runs in browser context. |
| Control | `REPEAT` | `REPEAT (<cmd>, <count>)` | Fixed count. |
| Control | `REPEAT (cond)` | `REPEAT (<cmd>, <condition>)` | JS condition checked before each iteration. |
| Data | `SETVAR` | `SETVAR <name> = "<value>"` | Script-global; values are always strings. |
| Data | `EVAL` | `EVAL <js>` | Run arbitrary JS; return values not captured. |
| Comments | `#` | `# comment` | Ignored during execution. |
| Procedures | `PROC` | `PROC <name> ... ENDPROC` | Reusable; defined before use; no params (use variables); call by name. |

Best practices: always wait before interacting (`WAIT #button 5` then `CLICK #button`); guard optional elements with `IF (EXISTS <sel>)`; use descriptive `SETVAR <name>`; add debug `EVAL <js>` statements.
