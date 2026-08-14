# GM API cheatsheet

Everything needs an `@grant` declaration. In Tampermonkey most calls are synchronous except `GM_getResourceText/URL`; in Greasemonkey they are asynchronous (Promise-based). Confirm the target platform before writing cross-platform scripts.

## Storage
- `GM_setValue(name, value)` / `GM_getValue(name, defaultValue?)` — KV storage; the default choice for saving settings (a script update does not overwrite values). Note: asynchronous in Greasemonkey.
- `GM_deleteValue(name)` — deletes a key.
- `GM_listValues()` — lists all keys.
- `GM_addValueChangeListener(name, (name, old_value, new_value, remote) => {})` — listens for value changes, returns a listener id; `remote` is `true` when the change came from another tab/script instance (usable for cross-tab messaging).
- `GM_removeValueChangeListener(id)` — removes a listener.
- Storage is not shared across scripts (each script has its own namespace).

## Menu
- `GM_registerMenuCommand(caption, fn, accessKey?)` — registers an extension popup menu item, returns an id; `accessKey` is the shortcut letter.
- `GM_unregisterMenuCommand(id)` — removes a menu item.
- Alternative: `@run-at context-menu` — the script name appears in the page context menu and executes on click.

## Network
- `GM_xmlhttpRequest(options)` — requests that bypass the same-origin policy (page XHR/fetch is CORS-restricted; this goes through extension permissions):
  ```javascript
  GM_xmlhttpRequest({
    url: "https://api.example.com/x",
    method: "POST",
    data: "a=1&b=2",                 // POST body; set the header yourself for form-urlencoded
    headers: { "Content-type": "application/x-www-form-urlencoded" },
    responseType: "json",            // use "arraybuffer" for binary downloads
    timeout: 5000,
    onload: (xhr) => console.log(xhr.responseText, xhr.status),
    onerror: (err) => console.error(err),
  });
  ```
  - Sends the target domain's cookies by default; the first cross-origin call pops a permission dialog — `@connect` whitelisting removes it.
  - Binary downloads (e.g. zip) MUST use `responseType: "arraybuffer"`, or `JSZip.loadAsync` fails to unzip.
  - Capture: GM_xhr requests do not appear in the normal Network panel — use the userscript manager panel or Firefox remote debugging.
- `GM_download(url, name)` — triggers an extension download (alternative for cross-origin downloads).

## Styles and resources
- `GM_addStyle(css)` — injects global styles; combine with `!important` so the page cannot override them:
  ```javascript
  GM_addStyle("#HMRichBox{display:none !important}");
  ```
- `GM_getResourceText(name)` / `GM_getResourceURL(name)` — reads the content/dataURL of a `@resource`-preloaded resource.

## Other
- `GM_setClipboard(text)` — writes to the clipboard.
- `GM_info` — script info object (script/scriptMetaStr/version, etc.).
- `unsafeWindow` — page window reference (needs `@grant unsafeWindow`). Use it to call page functions and read/write page data; it bypasses the security model, so data obtained through it is not trustworthy.
- `GM_cookie` — reads/writes cookies; officially beta, not stable — do not depend on it.
- `GM_notification` — desktop notification.
- `GM_openInTab(url)` — opens a new tab.

## Cross-origin decision
- Target API allows CORS → a page-level fetch is enough (same-origin also works).
- Target API has no CORS or needs arbitrary cookies → `GM_xmlhttpRequest` + `@connect`.
- When you cannot read CSRF-like tokens from cookies, use in-page XHR (`withCredentials`) for same-origin scenarios instead of GM.
