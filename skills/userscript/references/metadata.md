# Metadata block (@ fields) reference

Each line between `// ==UserScript==` and `// ==/UserScript==` is one `// @field value`. The manager uses this block to decide which pages the script runs on, when, and with what permissions.

## Basic info
- `@name` — script name, required.
- `@namespace` — distinguishes scripts with the same name.
- `@version` — version number (e.g. 0.1); update detection depends on it.
- `@description` — one-line description.
- `@author` — author.
- `@icon` — icon URL.
- `@homepage` / `@supportURL` — homepage and feedback address.
- `@downloadURL` / `@updateURL` — update addresses (usually filled in automatically by the platform when publishing to ScriptCat/GreasyFork).

## Match rules
- `@match` — matches pages, supports `*` wildcards: `https://example.com/*`, `http://*/*`. Multiple `@match` lines may coexist. **A page inside an iframe needs its own separate `@match` to take effect.**
- `@include` / `@exclude` — include/exclude rules similar to `@match`.
- `@noframes` — run only in the top-level page, never inside iframes.

## Run timing `@run-at`
| Value | Timing | Use |
|---|---|---|
| `document-start` | Before HTML parsing, earliest | **Required for hijacking scripts**; also used for injecting styles before flash of unstyled content |
| `document-body` | When body appears | Rarely used |
| `document-end` | DOM ready, elements available | Pure DOM manipulation |
| `document-idle` | After the page is idle (default) | General scripts |
| `context-menu` | Triggered when the context menu is clicked | With context-menu entries |

## Permissions `@grant`
- `none` — no sandbox, no GM functions; runs directly in the page context.
- `unsafeWindow` — gives a reference to the page window: call page functions, read/write page data.
- Declare every `GM_*` function you use individually: `@grant GM_setValue`, `@grant GM_xmlhttpRequest`.
- Special window capabilities: `@grant window.onurlchange` (listen for urlchange events), `@grant window.close`, `@grant window.focus` — the sandbox cannot reach these window members by default.

Declaring any grant enables sandbox mode; the difference between `@grant none` and the sandbox is in the "Execution model" section of SKILL.md.

## External resources
- `@require` — loads JS libraries; the manager fetches them and they share the sandbox scope with the script:
  ```
  // @require https://cdn.jsdelivr.net/npm/vue@2.6.12/dist/vue.min.js#md5=xxxx
  ```
  SRI validation supported: `#md5=`, `#sha256=`, `#sha1=`, `#sha384=`, `#sha512=` (comma-separate multiple).
  Gotcha: library code executes in the sandbox, so `var Vue = ...` does not attach to the global scope; if the library touches `window` (e.g. Element Plus's UMD factory uses `this`), add an assignment require via the `data:` protocol:
  ```
  // @require data:application/javascript,unsafeWindow.Vue%3DVue%3Bthis.Vue%3DVue%3B
  ```
- `@resource name URL` — preloads arbitrary resources (CSS/images/JSON/JS); at runtime use `GM_getResourceText("name")` for the content and `GM_getResourceURL("name")` for a dataURL:
  ```
  // @resource css https://example.com/style.css
  // @grant    GM_getResourceText
  // @grant    GM_getResourceURL
  // @grant    GM_addStyle
  GM_addStyle(GM_getResourceText("css"));
  ```

## Cross-origin whitelist
- `@connect domain` — whitelist of domains `GM_xmlhttpRequest` may access. Without it, the first cross-origin request pops a "cross-site request authorization" dialog that the user must approve:
  ```
  // @grant   GM_xmlhttpRequest
  // @connect api.bilibili.com
  ```

## References
- Tampermonkey official docs: https://www.tampermonkey.net/documentation.php
- ScriptCat docs: https://docs.scriptcat.org/
