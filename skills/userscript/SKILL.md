---
name: userscript
description: >-
  Write, debug, and enhance userscripts (Tampermonkey / ScriptCat / Greasemonkey /
  Violentmonkey). Use when the user asks to write, debug, or improve a userscript /
  Tampermonkey script / Greasemonkey script / ScriptCat script — including implicit
  asks like "write a script for this site", "intercept or listen to this API",
  "remove ads or restrictions from a page", "automate a page", "extract page data",
  or "inject UI into a page". Covers the GM_ API, @match/@grant/@run-at metadata,
  the sandbox and unsafeWindow, XHR/Fetch/WebSocket hijacking, MutationObserver,
  shadow DOM, iframe, Vue/React framework pages, and loading external libraries.
license: MIT
disable-model-invocation: true
metadata:
  author: Wildfire2282
  author-url: https://github.com/Wildfire2282
  version: "1.0"
---

# Userscript Development

Inject JavaScript into web pages to modify them, hijack network requests, and automate interactions. Scripts are injected by an extension (Tampermonkey, ScriptCat, Greasemonkey, Violentmonkey) into matching pages according to the metadata block.

## Script skeleton

```javascript
// ==UserScript==
// @name         Script name
// @namespace    https://example.com/
// @version      0.1
// @description  One-line description of purpose
// @author       Author
// @match        https://example.com/*
// @run-at       document-start    // hijacking must be document-start; default is document-idle
// @grant        unsafeWindow
// @connect      api.example.com   // cross-origin whitelist for GM_xmlhttpRequest
// ==/UserScript==

(function () {
  "use strict";
  // code...
})();
```

- Every `GM_*` function and `unsafeWindow` you use MUST be declared in `@grant`, or you get a `ReferenceError`.
- `@match` supports `*` wildcards; when the target lives inside an iframe, the iframe's own address needs a separate `@match` for the script to run there directly.

## Execution model (understand this first)

| Mode | Environment | Capabilities |
|---|---|---|
| Default (any grant declared) | Extension sandbox; the page cannot see the script's variables | All GM APIs + DOM; page data via `unsafeWindow` |
| `@grant none` | Injected directly into the page context | Page-native APIs; **no GM functions at all** |

- Inside the script, `window` is a sandbox wrapper object; `unsafeWindow` is the page's real window.
- Replacing `window.setInterval`, `window.fetch`, etc. from the sandbox is **useless** — page code uses the page window. You must hijack the versions on `unsafeWindow`.
- Assignment without a declaration (`x = 1`) breaks out of the sandbox into the page global scope, leaking variables and causing naming collisions. Forbidden.
- Variables the page declares with `let`/`const` are readable from the script; variables declared with `var` hang off the page window (`unsafeWindow`).

## Development workflow

1. **Analyze the target page**: F12 to inspect target elements and network requests; use Wappalyzer or global markers to identify the framework — Vue2 has `__vue__`, Vue3 has `__vue_app__`, React has `__reactProps`/`__reactFiber`, webpack has `__webpack_require__`.
2. **Write the metadata**: decide `@match` first (only match pages you need — never `http://*/*` wide open) and `@run-at` (pure DOM work → document-end, hijacking → document-start).
3. **Pick the technique**: see "Choose by need" below; read `references/network-hijacking.md` before writing a hijack, and `references/framework-integration.md` whenever a framework is involved.
4. **Implement**: every step of invasive code needs defensive checks (`arguments.length !== 0 && arguments[0].indexOf !== undefined` before calling), because a script error takes down the page.
5. **Verify**: a `console.log` output proves the code executed; use breakpoints to locate the step that did not take effect; GM_xhr requests are invisible in the normal Network panel — capture them from the userscript manager (see `references/debugging.md`).

## Choose by need

- **Wait for dynamic elements**: `references/dom-techniques.md`. setInterval polling is simplest; MutationObserver performs better and detects delete-and-reinsert; cxxjackie's ElementGetter library is the least effort.
- **Intercept/modify network requests**: `references/network-hijacking.md`. XHR → hook open+send; Fetch → replace `window.fetch` and wrap `Response`; WebSocket → wrap the constructor.
- **Cross-origin requests**: `references/gm-api.md`. `GM_xmlhttpRequest` + `@connect` whitelist bypasses the same-origin policy.
- **Modify Vue/React page data, trigger framework validation**: `references/framework-integration.md`.
- **Load jQuery/Vue/UI libraries**: `references/libraries.md`. Prefer `@require`; libraries that locate themselves via `currentScript`/`this` (Element Plus, Layui) need script injection or a `data:`-URL injection config instead.
- **Add elements/styles**: `GM_addStyle(css)` injects styles (use `!important` to survive overrides); `createElement`+`appendChild` adds elements — SPA re-renders wipe them, so re-insert via MutationObserver.
- **shadow DOM / cross-origin iframe / SPA route watching**: `references/dom-techniques.md`.

## Gotchas (where scripts usually break)

- **Element not found**: page loaded ≠ element exists; data renders only after XHR returns, so process it in the request's `load` callback; the element may be in an iframe (same-origin → `contentDocument.querySelector`, cross-origin → add an `@match` for the iframe address); or in shadow DOM (read `.shadowRoot` or hook `attachShadow`).
- **Injection timing**: hijacking code MUST run before the page's own code grabs the original function — `@run-at document-start`. If you inject too late and the original is already held by reference, the hijack never takes effect.
- **`@require` scope**: library code runs in the same sandbox as the script; `var Vue = ...` inside the library does NOT hit the global scope → put `unsafeWindow.Vue = Vue` as the script's first line, or inject the assignment with a `data:` require: `// @require data:application/javascript,unsafeWindow.Vue%3DVue%3B`.
- **GM functions must be granted**: `GM_getValue` is synchronous in Tampermonkey, asynchronous in Greasemonkey (returns a Promise — use `.then`).
- **Simulated clicks/assignments don't work**: on framework pages, directly assigning `value` does not trigger validation — dispatch events in focus→input→change→blur order with `new Event("change")`; for React, call `onChange` from `__reactEventHandlers`; `isTrusted` cannot be forged (synthetic events are always false) — deliver the event to the framework's internal listener instead.
- **querySelectorAll returns a NodeList**: spread it first (`[...list]`) before iterating/deleting — deleting during iteration breaks.
- **Regexes in hooks**: use `([^&]+)` not `.*?` (ReDoS); decide "which request" by URL (`this._url = url` in open) rather than by body content.
- **XHR response hijacking**: `xhr.response` only has a getter on the prototype — shadow it on the individual xhr instance with `Object.defineProperty`; NEVER defineProperty on the prototype (slows every request).
- **Fetch hijack not firing**: the page may call `response.text()` instead of `json()` — wrapping only json never fires. Use a Proxy to probe which methods the page actually calls.
- **GM_xmlhttpRequest**: POST sends cookies by default; the first cross-origin call pops a permission dialog, `@connect` whitelisting removes it; binary downloads MUST use `responseType: "arraybuffer"`.
- **SPA re-render wipes inserted elements**: in the MutationObserver callback, check the node is gone before re-inserting; mark your nodes with a class to avoid reprocessing (your own insertions trigger the observer too).

## References (load on demand)

- `references/metadata.md` — full metadata field reference: match/run-at/grant/require/resource/connect
- `references/gm-api.md` — GM API cheatsheet and cross-origin requests
- `references/network-hijacking.md` — XHR/Fetch/WebSocket/addEventListener/videojs hijack patterns (read before writing a hijack)
- `references/dom-techniques.md` — dynamic elements, shadow DOM, iframe, route watching
- `references/framework-integration.md` — Vue2/Vue3/React/webpack instance access and data injection
- `references/libraries.md` — three ways to load libraries and how to choose
- `references/debugging.md` — debugging, breakpoints, network capture
