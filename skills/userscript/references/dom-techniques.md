# DOM techniques: dynamic elements, shadow DOM, iframe, routing

## Waiting for dynamic elements (they appear only after data renders)

Page load ≠ element exists; data renders only after XHR returns, so a direct querySelector returns null. Three options:

1. **setInterval polling** (simplest — remember to clearInterval when done):
   ```javascript
   const timer = setInterval(() => {
     const el = document.querySelector(".main");
     if (el) { clearInterval(timer); handle(el); }
   }, 500);
   ```
2. **MutationObserver** (better performance; detects delete-and-reinsert; separates data layer from logic layer):
   ```javascript
   const observer = new MutationObserver((records) => {
     for (const r of records) {
       if (r.type === "childList") {
         r.addedNodes.forEach((node) => handle(node));
       }
     }
   });
   observer.observe(document.querySelector(".list"), { childList: true, subtree: true });
   ```
   - Handle pre-existing nodes once with `querySelectorAll`, then rely on the observer for increments.
   - **Your own insertions also trigger the callback** — deduplicate with a marker class (`el.classList.add("handled")`).
   - Delete-and-reinsert: scan `removedNodes` and re-insert your element when it is removed.
3. **ElementGetter** (cxxjackie's library; Promise + Observer wrapper; least effort): `const el = await getElement(".target");`

## shadow DOM

- Open mode: the host element carries a `shadowRoot` property — query directly with `el.shadowRoot.querySelector(...)`.
- Closed mode: unreachable from outside; you can only hold a reference from creation time. Hook `attachShadow` and attach the reference to the element (cxxjackie's approach, does not break the original arguments):
  ```javascript
  const originShadow = Element.prototype.attachShadow;
  Element.prototype.attachShadow = function (...args) {
    const shadowRoot = originShadow.call(this, ...args);
    this._shadowRoot = shadowRoot; // closed mode is now reachable
    return shadowRoot;
  };
  ```
- Brute force: set `args[0].mode = "open"` then call the original (catches native-code detection — see the counter-defenses in network-hijacking.md).
- On framework pages the shadowRoot reference often lives on the component instance: on Vue pages `el.__vue__.shadowDom.innerHTML` reads it directly.

## iframe

- Same-origin: the main page can operate directly with `iframe.contentDocument.querySelector(...)`; iframe load timing is not synchronized with the main page, so `contentDocument` may be null → listen for the iframe's `load` event first.
- Cross-origin: `contentDocument` is always null. Two ways around it:
  1. **Add an `@match` for the iframe address** so the script runs directly in the iframe's own document (simplest, recommended).
  2. Run the script on both sides and talk via `postMessage` (the iframe injects late, so the iframe side sends "I'm ready" first; the main page answers using `e.source`):
     ```javascript
     // iframe side
     window.top.postMessage({ cmd: "ready" }, "*");
     // main page side
     window.addEventListener("message", (e) => {
       if (e.data.cmd === "ready") e.source.postMessage({ cmd: "getTitle" }, "*");
     });
     ```
- `window.frames` only contains first-level child iframes; `window.top` is the topmost, `window.parent` the immediate parent.
- Message timing: postMessage to a freshly created iframe is missed because the other side's script is not injected yet — the later-loaded side sends first.

## SPA route watching

- Generic: hijack `history.pushState`/`replaceState` (every site wrapper eventually goes through it) + listen for `popstate`/`hashchange`:
  ```javascript
  const originPush = history.pushState;
  history.pushState = function (...args) {
    console.log("route changed");
    return originPush.apply(this, args);
  };
  window.addEventListener("popstate", handler);
  window.addEventListener("hashchange", handler);
  ```
- Vue2: `document.querySelector("#app").__vue__.$router.afterHooks.push(() => {...})` — the afterEach hook is essentially a push into the `afterHooks` array, so you can inject directly.

## Waiting for asynchronously initialized page objects (script-tag loaded)

Pages load libraries asynchronously (e.g. the ace editor); at document-start `window.ace` is still undefined. Use `waitForProperty` (cxxjackie's utility): hijack `Object.defineProperty` + preinstall get/set interceptors to catch the assignment, walking deep properties level by level:

```javascript
const ace = await waitForProperty(unsafeWindow, "ace", "edit");
```
Note: the `Object.defineProperty` hook only intercepts defineProperty calls — a plain `window.a = 666` assignment does not trigger it, so you need a preinstalled set interceptor; the property may be a `{value}` or a `{get, set}` descriptor, so handle both when reading the value.

## Automation

- Simulated click: `el.click()`.
- Form filling: assign `value`/`checked` directly, then dispatch events in **focus → input → change → blur** order to trigger validation:
  ```javascript
  input.value = "x";
  input.dispatchEvent(new Event("input", { bubbles: true, cancelable: true, composed: true }));
  input.dispatchEvent(new Event("change", { bubbles: true }));
  ```
- Framework pages (value assignment does nothing, `isTrusted` checks): see framework-integration.md.
- Login-state check: whether the login box element exists (`document.querySelector("#login") == null` means logged in).
