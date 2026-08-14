# Debugging and verification

## Console and breakpoints

- A `console.log` output proves the code executed; clicking the console output jumps to the source breakpoint.
- A `debugger;` statement pauses when reached.
- Breakpoint types:
  - Line/conditional breakpoints (set via right-click on the line number; right-click also offers "never pause here" to fight infinite debugger).
  - XHR breakpoints: pause automatically on URL match (find "who sent this request").
  - DOM breakpoints: pause on subtree modification / attribute modification / node removal (find "who deleted my node").
  - Event breakpoints (e.g. click/playing).
- Debug panel: watch (scope-limited), scope (includes closures), call stack ("initiator/stack trace" traces the source function of a request).

## Network capture

- Page XHR/fetch: visible in the normal Network panel.
- **GM_xmlhttpRequest requests are invisible in the normal Network panel** — capture from the network page of the userscript manager; Firefox needs remote debugging or the background page console.
- "POST doesn't work" checklist: compare request headers (the server may validate headers), check whether the JS encrypts the body, compare against the manager-panel capture.

## Common failure scenarios

| Symptom | Cause | Fix |
|---|---|---|
| Script does not run | `@match` does not match (including pages inside iframes) | F12 to confirm the address, add `@match` |
| Hijack has no effect | Injected too late, the page already holds the original function | `@run-at document-start` |
| GM function undefined | Missing `@grant` | Declare it |
| Element not found | Async rendering / iframe / shadow DOM | See dom-techniques.md |
| value change does not submit | Framework validation not triggered | Dispatch focus→input→change→blur; for React call onChange (see framework-integration.md) |

## Storage selection (when the script must persist data)

- Small data such as config: `GM_setValue/GetValue` (recommended — survives script updates).
- Cookies: <4KB per entry, sent with every request.
- LocalStorage: 2.5–10MB, no indexes.
- Large data: IndexedDB.

## Verification workflow

1. Console confirms the script runs without errors and the target behavior works (leave `console.log` traces).
2. Refresh and reproduce once, confirming timing stability (refresh several times for async-rendering scenarios).
3. For framework/hijack changes, confirm the rest of the page still works (the defensive nature of injected code).
