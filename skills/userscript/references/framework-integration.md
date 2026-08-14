# Framework page handling (Vue / React / webpack)

Identify the framework first: the Wappalyzer extension, or global markers — Vue2 `__vue__`, Vue3 `__vue_app__`, React `__reactProps`/`__reactFiber$xxx`, webpack `__webpack_require__`.

## Vue2

- Component root DOM elements carry a `__vue__` property (Vue sets `vm.$el.__vue__ = vm` in `_update`); child elements do not → walk up/down from the root; once you have the instance, traverse with `$parent`/`$children`/`$root`.
- Component lifecycle hooks live in arrays like `vm.$options["updated"]` — push to inject:
  ```javascript
  const dom = document.querySelector("#app");
  dom.__vue__.$options["updated"] = dom.__vue__.$options["updated"] || [];
  dom.__vue__.$options["updated"].push(() => console.log("inject"));
  ```
- Data: names starting with `$` are component data (e.g. `dom.__vue__.$parent.data` is the video list); mutating reactive data triggers updates automatically.
- Vuex: global state is at `this.$store.state`. Mutating `mapState`-mapped fields directly on the store bypasses restrictions (`store.state.visitUserInfo.isTaskUser = true`); commits dispatch through the `store._mutations[type]` array, where wrappers can be peeled off layer by layer. Searching for a state name finds every dependency point (including watchers).

## Vue3

- After mount, `rootContainer.__vue_app__` is the app instance.
- **Initialization hook point**: `createApp` processes component objects with `Object.assign` — hook `Object.assign`, and when `args[1]?.render !== undefined`, wrap the root component's render; when render is called, the 6th argument is ctx, so `args[5]["_"].appContext.mixins.push({...})` achieves a global mixin:
  ```javascript
  const assign = Object.assign;
  let isRun = false;
  Object.assign = function (...args) {
    if (args.length == 2 && args[1]?.render !== undefined && !isRun) {
      const b = args[1];
      const originRender = b.render;
      let isInject = false;
      b.render = function (...args) {
        if (!isInject) {
          args[5]["_"].appContext.mixins.push({ mounted() { console.log("mounted"); } });
          isInject = true;
        }
        return originRender.apply(this, args);
      };
      isRun = true;
    }
    return assign.apply(this, args);
  };
  ```
- **Getting router/pinia**: `use` deduplicates plugins with a WeakSet — hook `WeakSet.prototype.has` (needs document-start injection); `args[0].addRoute !== undefined` means router (can `router.afterEach`), `args[0].state !== undefined` means pinia.
- Data locations: `this['_'].setupState` (setup return value), `this['_'].$data` (options API), `this['_'].props`. refs are RefImpl instances — assign `.value` directly to trigger reactivity; props must be replaced wholesale (`instance.props.info = {...instance.props.info, title: "x"}`).
- `__vue_app__` appears only after mount — use the initialization hook when you need it earlier instead of waiting for the property.

## React

- Elements carry `__reactProps$xxx`/`__reactFiber$xxx`/`__reactEventHandlers$xxx` properties; find the key with `Object.keys(el).find(p => p.startsWith("__reactProps"))`.
- **Data extraction**: `el[prop].children[0].props.info` (pick the topmost element and drill down).
- **Triggering input validation** (direct value assignment does nothing): find `onChange` on `__reactEventHandlers` and call it; if missing, try `el.__react`, `__reactProps`, `__reactFiber$xxx.alternate.return.memoizedProps`:
  ```javascript
  const prop = Object.keys(ele).find((p) => p.startsWith("__reactEventHandlers"));
  ele[prop].onChange({ target: { value: "1234" } });
  ```
- **Rich text editors** (Draft.js and others without an input element): onChange needs the framework's editorState object, not a string — build it with `ContentState.createFromText(text)` + `EditorState.createWithContent(content)` and deliver it into the onChange on the Fiber chain. Self-built webpack bundles that expose `library: "draftUtils"` then `@require` it are more reliable than `@require`-ing draft-js (tree-shaking may strip internal functions).
- Dynamic lists: combine MutationObserver (`childList` + `addedNodes`) with `CustomEvent` dispatch for updates.

## webpack hijacking (webpack 4)

When a site shields `__vue__`, hook `Function.prototype.call` to intercept the module invocation of `__webpack_require__` — args[2] of call is the module exports object:

```javascript
const originCall = Function.prototype.call;
Function.prototype.call = function (...args) {
  const result = originCall.apply(this, args);
  if (args[2]?.default?.version === "2.5.2") {
    args[2].default.mixin({
      mounted() { this.$el["__Ivue__"] = this; }, // re-attach the instance property
    });
  }
  return result;
};
```

## Element validation rules and isTrusted

- Generic event order: focus → input → change → blur; dispatching `change` alone often fails — focus+input+blur together usually works:
  ```javascript
  input.focus();
  input.value = "x";
  input.dispatchEvent(new Event("input", { bubbles: true }));
  input.blur();
  ```
- jQuery pages: `$._data(elem, "events")` returns the event table — find `handle` and call it directly.
- Angular: take `callback` from the `dom.__zone_symbol__xxx` array and call `callback({target:{value:"222"}})`.
- **isTrusted cannot be forged** (synthetic events are always false). Approach: take the framework's internal listener function, construct an event object, use a Proxy so reading `isTrusted` returns true, then deliver it to the framework's own handler:
  ```javascript
  const func = $._data(dom).events.input[0].handler;
  function injectChar(c) {
    const event = new InputEvent("input", { inputType: "insertText", data: c });
    const wrapEvent = new Proxy(event, {
      get: (target, property) =>
        property === "isTrusted" ? true : Reflect.get(target, property),
    });
    func({ originalEvent: wrapEvent, target: { value: { normalize: () => "-" + c } } });
  }
  ```
  Key: read the framework source first to find the check point (e.g. `event.originalEvent.isTrusted`); the framework reads `event.target.value` so provide it; when it does `slice(1)`-style reads, provide the sacrificial character.
- React: when changing data directly does not trigger reactivity, call `_owner.memoizedProps.onSelected(data)` with the data, or mutate and then update innerHTML as a fallback.

## Stack-trace exploitation (tracing anonymous functions / blocking files)

When a low-level API is wrapped by an upper layer with no signature, `new Error()` inside the wrapper and use `err.stack` to filter by the upper layer's distinctive name; you can also throw inside a basic API called during file initialization, matching the file name by stack, to block the whole JS file — pair with `window.onerror` returning true to swallow the error.
