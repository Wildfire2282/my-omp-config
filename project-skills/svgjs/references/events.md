# Events

## Sugar methods

```js
element.click(function () { this.fill({ color: '#f06' }) })
element.click(null)   // remove
```

Available: `click`, `dblclick`, `mousedown`, `mouseup`, `mouseover`, `mouseout`, `mousemove`, `mouseenter`, `mouseleave`, `touchstart`, `touchmove`, `touchleave`, `touchend`, `touchcancel`, `contextmenu`, `wheel`, `pointerdown`, `pointermove`, `pointerup`, `pointerleave`, `pointercancel`.

Pointer/mouse events give screen coordinates — convert with `point()`:

```js
element.pointerdown(function (event) {
  var point = this.point(event.clientX, event.clientY)  // local coords, all transforms applied
})
```

## on / off / fire / dispatch

```js
element.on('click', handler)                 // `this` in handler = element
element.on(['click', 'mouseover'], handler)  // array or 'click mouseover' string
element.on('click', handler, window)         // custom `this` context
element.off('click', handler)                // specific
element.off('click')                         // all for one type
element.off()                                // everything

element.fire(event)                          // fire; returns itself
element.fire(event, { arbitrary: data })     // data lands in event.detail
element.fire(event, data, { cancelable: false })  // event options
var event = element.dispatch(event)          // fire + return the event (check defaultPrevented)
```

`SVG.on(window, 'click', handler)` / `SVG.off(...)` work on non-element targets too.

## Custom events

```js
element.on('myevent', function (e) { alert(e.detail.some) })
element.fire('myevent', { some: 'data' })
```

Cancelable defaults to `true` in SVG.js (override with the third `fire()` argument).

## Namespaced events

Syntax `event.namespace`; use for cleanup without touching other handlers. Prefer specific namespaces (`event.wicked`) over generic ones (`event.svg`).

```js
element.on('myevent.namespace', fn)
element.off('myevent.namespace')   // only this namespace
element.off('.namespace')          // all events of this namespace
element.off('myevent')             // all handlers of myevent (all namespaces)
```

You cannot FIRE a namespaced event — `element.fire('myevent.namespace')` does nothing; `element.fire('myevent')` fires all handlers of the event.
