# Three ways to load libraries, and how to choose

## Trade-offs of the three ways

1. **`@require` (default choice)**: the manager loads the library automatically; it shares the sandbox scope with the script. Good for libraries you do not need to modify; supports SRI (`#md5=`/`#sha256=`).
   Gotcha: `var X = ...` inside the library does not attach to the global scope; libraries that depend on `window`/`this` (see below) need a `data:`-protocol require:
   ```
   // @require data:application/javascript,unsafeWindow.Vue%3DVue%3Bthis.Vue%3DVue%3B
   ```
2. **script-tag injection**: `document.createElement("script")` + `document.documentElement.appendChild` — the library runs in the page context and the page can use it too. Note that CSP blocks it (`Refused to load the script ... violates CSP script-src`; GitHub is a classic case); insertion position affects load timing, use `onload` to run after load; inject as early as possible with `@run-at document-start`.
3. **`@resource` + `GM_getResourceText/URL`**: preload the resource, fetch the content/URL at runtime and inject it (`eval` for JS, `GM_addStyle` for CSS).

## Common library gotchas

| Library | Gotcha | Fix |
|---|---|---|
| Vue | `@require`'d global build is `var Vue = (function(exports){})()` — no global in the sandbox → `Vue is not defined` | Script first line: `unsafeWindow.Vue = Vue;`, or a `data:` require with `unsafeWindow.Vue%3DVue%3B` |
| Element Plus | The UMD factory `factory((global.ElementPlus = {}), global.Vue)` — its `global` is `this`, and `this` has no Vue in the sandbox → `vue is undefined` | `data:` require injecting `this.Vue%3DVue%3BunsafeWindow.Vue%3DVue%3B`; CSS via `@resource` + `GM_addStyle` |
| Layui | Extension-module paths come from `currentScript.src`, which becomes the manager's user.js after `@require` → modules load incorrectly | Inject the global config before layui.js: `@require data:application/javascript,window.LAYUI_GLOBAL%3D%7Bdir:'https://unpkg.com/layui@2.6.8/dist/'%7D`, or script-inject with onload |
| jQuery | With `@grant none` and a page that already has jQuery, two jQuery instances conflict | `this.$ = this.jQuery = jQuery.noConflict(true);`; use the page's copy when present, only load your own when absent |

## Library selection (one-liners)

- **toastr** — toast notifications; `toastr.success("msg", "title", {timeOut: 0})`; the CSS MUST be injected or there is no styling.
- **SweetAlert2** — dialogs; `@require` and use, `Swal.fire({title, html, icon})`; hooks like didOpen fire asynchronously.
- **JSZip** — zip/unzip; `zip.file("a.txt", content)`, `generateAsync({type:"blob"})`; binary reads MUST go through `GM_xmlhttpRequest` with `responseType: "arraybuffer"` or unzipping errors; no encryption/multi-volume support.
- **FileSaver** — frontend downloads; `saveAs(blob, filename)`; cross-origin resources ignore `a[download]` — fetch first, then convert to a Blob.
- **Downloader triggers** — Xunlei: `thunder://` + base64 (`"AA" + url + "ZZ"`), encoded with `btoa`.
- **Element Plus / Layui / toastr / SweetAlert2** — UI components; prefer Element Plus in the Vue ecosystem.
- **jQuery** — CSS selectors, unified ajax; no longer mainstream — skip it when native APIs suffice.
- Libraries attach to globals (`JSZip`, `Swal`, `toastr`, etc.); when the script reports `xxx is not defined`, add a `/*global xxx*/` comment.

## Publishing modified libraries (NPM)

Platforms restrict `@require` domains but jsdelivr is essentially unrestricted → publish the modified library as an npm package to bypass:
`npm login` → `npm init` → write index.js → `npm publish`; for updates bump the version in package.json then publish again. CDN address `https://cdn.jsdelivr.net/npm/<lib>`; refresh the cache at `https://purge.jsdelivr.net/npm/<lib>`, or use the exact `@<version>` address.
Note: modified libraries cannot go directly onto script platforms (audits forbid external imports) — put them in ScriptCat's dependency-library section / GreasyFork user libraries instead.
