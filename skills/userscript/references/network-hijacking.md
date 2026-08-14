# Network request hijacking

Hijacking is a frontend man-in-the-middle: save a reference to the original function → replace it with a wrapper → call the original inside the wrapper with `call`/`apply` so `this` stays correct. Any method reachable through the prototype chain or global object can be hooked.

**General prerequisite**: the script MUST be `@run-at document-start` so the replacement happens before the page grabs the original function; in the sandbox, hijack the API on `unsafeWindow`.

## The three-step hook

```javascript
// 1. save the original  2. replace it  3. call the original with call/apply
const origin = XMLHttpRequest.prototype.send;
XMLHttpRequest.prototype.send = function (...args) {
  // hijack logic
  return origin.apply(this, args); // `this` is mandatory or the instance is lost
};
```

## XHR hijacking (request + response)

XHR lifecycle: `new` → `open` (method/url) → `send` (body) → load. So hook `open` to record the URL and `send` to modify the submission.

```javascript
const oldOpen = XMLHttpRequest.prototype.open;
XMLHttpRequest.prototype.open = function (method, url, async, user, password) {
  this._url = url; // stash on the instance for send to read
  return oldOpen.call(this, method, url, async, user, password);
};
const oldSend = XMLHttpRequest.prototype.send;
XMLHttpRequest.prototype.send = function (body) {
  if (this._url && this._url.indexOf("/share/set?channel=") !== -1) {
    // modify the submission (defensive: check arguments.length, then indexOf exists)
    if (body && body.indexOf("pwd=") !== -1 && body.indexOf("vcode") === -1) {
      body = body.replace(/pwd=[a-zA-Z0-9]{0,4}&/i, "pwd=" + myCode + "&");
    }
  }
  return oldSend.apply(this, [body]);
};
```

**Response hijacking**: `xhr.response`/`responseText` only have getters on the prototype and cannot be assigned directly; shadow the prototype getter on the **individual instance** with `Object.defineProperty` (affects only that one request):

```javascript
const oldOpen = XMLHttpRequest.prototype.open;
XMLHttpRequest.prototype.open = function (...args) {
  const xhr = this;
  if (args[1] && args[1].indexOf("/api/target") !== -1) {
    const getter = Object.getOwnPropertyDescriptor(
      XMLHttpRequest.prototype, "response"
    ).get;
    Object.defineProperty(xhr, "response", {
      get: () => {
        const result = getter.call(xhr);
        return JSON.parse(result) && modify(result); // tamper before returning
      },
    });
  }
  return oldOpen.apply(this, args);
};
```
NEVER defineProperty on the prototype (slows every request, and `response` has no setter so it cannot be redefined).

**Listen to the response (no data change)**: hook `send` and attach a `load` listener to the xhr:
```javascript
const oldSend = XMLHttpRequest.prototype.send;
XMLHttpRequest.prototype.send = function (...args) {
  this.addEventListener("load", () => {
    if (this.readyState == 4 && this.status == 200 &&
        this.responseURL.indexOf("/web/aweme/post") !== -1) {
      const data = JSON.parse(this.response); // extract / process
    }
  });
  return oldSend.apply(this, args);
};
```

## Fetch hijacking (request + response)

Replace `window.fetch`; the return must be wrapped in a Promise, and `Response` methods (`json`/`text`/`clone`) need individual re-wrapping:

```javascript
const oldFetch = window.fetch;
window.fetch = function (...args) {
  // request hijack: modify args[0] (url) or args[1] (init) directly
  return new Promise((resolve, reject) => {
    oldFetch.apply(this, args).then((response) => {
      if (urlMatches(args)) {
        const oldJson = response.json;
        response.json = function () {
          return new Promise((resolve2, reject2) => {
            oldJson.apply(this, arguments).then((result) => {
              modifyData(result); // tamper with the response data
              resolve2(result);
            });
          });
        };
      }
      resolve(response);
    });
  });
};
```

Key points and traps:
- Filter URLs defensively: `args[0] && args[0].indexOf && args[0].indexOf("/api/x") !== -1` (args[0] is not always a string).
- **The page may call `text()` instead of `json()`** — wrapping only json never fires. Use a Proxy to print `get` and probe which methods the page actually calls:
  ```javascript
  function proxyResponseFactory(response) {
    return new Proxy(response, {
      get(target, property) {
        const result = Reflect.get(target, property);
        if (typeof result === "function") {
          return (...args) => {
            let r = result.call(target, ...args);
            if (property === "clone") r = proxyResponseFactory(r); // wrap clone recursively
            return r;
          };
        }
        return result;
      },
    });
  }
  ```
- Distinguish operations on the same endpoint by the semantics of the submitted body (e.g. GraphQL's `operationName` field: the list query returns ids, the detail query returns watermark-free URLs).
- When re-requesting with `GM_xmlhttpRequest`, newlines in the body must be escaped as `\n` strings.

## WebSocket hijacking

Wrap the `window.WebSocket` constructor: hijack `ws.send` for submissions; hijack `onmessage` for responses — it can only hold one callback and the page overwrites it, so take over the setter with `Object.defineProperty` and manage the callback yourself; `evt.data` is read-only, change it via a Proxy's `get`:

```javascript
const originSocket = window.WebSocket;
window.WebSocket = function (...args) {
  let callback;
  const ws = new originSocket(...args);
  const originSend = ws.send;
  ws.send = function (...args) {
    args[0] = args[0] + "[hijacked]";          // modify the submission
    return originSend.apply(this, args);
  };
  ws.onmessage = function (evt) {             // take over the callback (page overwrites, see below)
    const proxyEvent = new Proxy(evt, {
      get: (t, p) => (p === "data" ? t[p] + "[hijacked]" : t[p]), // modify the response
    });
    callback && callback(proxyEvent);
  };
  Object.defineProperty(ws, "onmessage", {   // when the page assigns onmessage, stash it in callback
    get: () => callback,
    set: (fn) => { callback = fn; },
  });
  return ws;
};
```

## addEventListener hijacking

`addEventListener` comes from `EventTarget.prototype`, inherited by every DOM element — hooking it can suppress state-detection (e.g. "mouse left the tab" prompts, "minimized → pause"):

```javascript
const oldEL = EventTarget.prototype.addEventListener;
EventTarget.prototype.addEventListener = function (...args) {
  if (args[0] === "mouseout" && shouldBlock(this)) return; // filter out
  return oldEL.call(this, ...args);
};
```

## Countering defenses (detection / protection)

- **writable: false**: hook `Object.defineProperty` first, force the target descriptor's `writable` to true, then replace normally.
- **native code detection**: the page regex-tests `Function.prototype.toString` for `native code` to detect a hijacked API. If `toString` was already held early, hijack `RegExp.prototype.test` instead and return true when `this.source` contains `function`/`native code`:
  ```javascript
  RegExp.prototype._test = RegExp.prototype.test;
  RegExp.prototype.test = function (s) {
    if (this.source.includes("function") || this.source.includes("native code")) return true;
    return this._test(s);
  };
  ```
- **Timer detection**: the page runs detection inside `setInterval`/`setTimeout` callbacks → hijack the timers and `return` directly when `new Error().stack.indexOf("detectorName") !== -1` (pair with `window.onerror` returning true to swallow your own errors).
- **Tracing the underlying API**: when the upper-level function is anonymized and has no signature, read `err.stack` via `new Error()` inside a wrapper around a low-level API (e.g. `window.setTimeout`) and filter by the upper level's distinctive name.

## videojs hijacking (players)

Four-level escalation:
1. Hook the `unsafeWindow.videojs` entry (defineProperty intercepts the assignment).
2. Counter `writable:false` (see above).
3. Use official hooks `videojs.hook("setup", player => {})` / `"beforesetup"` to get the player instance, then hook `player.on` to replace event callbacks (e.g. the playing-ad callback).
4. If hooks are blocked, read the source: the Player lives at `videojs.getComponent("Component").components_["Player"]` — replace it wholesale (note: registering throws while a live player exists, so replace only when no player is alive).

```javascript
unsafeWindow._videojs = undefined;
Object.defineProperty(unsafeWindow, "videojs", {
  get() { return unsafeWindow._videojs; },
  set(obj) {
    obj.hook("setup", function (player) {
      const originOn = player.on;
      player.on = function (...args) {
        if (args[0] === "playing") args[1] = () => player.play();
        return originOn.apply(this, args);
      };
    });
    unsafeWindow._videojs = obj;
  },
});
```

## Initial page data fallback (SSR)

First-screen data is often inlined in `<script id="RENDER_DATA">`, URL-encoded:

```javascript
const data = JSON.parse(
  decodeURIComponent(document.querySelector("#RENDER_DATA").innerText)
);
// try encoding pairs one by one: escape/unescape, encodeURI/decodeURI, encodeURIComponent/decodeURIComponent
```
Note: the SSR data structure and the XHR-returned object may use different field names (e.g. `playAddr` vs `play_addr`) — re-confirm the paths.
