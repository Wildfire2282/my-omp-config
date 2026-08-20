---
name: svgjs
description: >-
  Use this skill when creating, manipulating, animating, importing, or exporting SVG
  with SVG.js v3 (@svgdotjs/svg.js) in JavaScript or TypeScript — building drawings
  programmatically, referencing/painting shapes, moving/resizing/transforming elements,
  chaining animations and timelines, gradients/patterns/masks/clip-paths/text-on-path,
  binding events, serializing a drawing to SVG markup, or generating SVG in Node.js with
  svgdom. Trigger even when the user only says "SVG" or "draw/convert/animate SVG"
  without naming the library. Not for hand-editing SVG XML files or for other SVG
  libraries (D3, snap.svg, Raphael).
license: MIT
disable-model-invocation: true
metadata:
  author: Wildfire2282
  author-url: https://github.com/Wildfire2282
  version: "1.0"
---

# SVG.js v3 — Create, Manipulate, Animate SVG

SVG.js (`@svgdotjs/svg.js`) is a dependency-free library that wraps the SVG DOM in a chainable, OO API. Every SVG element is a JavaScript object with methods like `move()`, `fill()`, `animate()`; a container like `SVG()` can construct elements directly.

## Quick start

Browser (CDN):

```html
<script src="https://cdn.jsdelivr.net/npm/@svgdotjs/svg.js@3/dist/svg.min.js"></script>
<script>
  var draw = SVG().addTo('body').size(300, 300)
  draw.rect(100, 100).fill('#f06').move(50, 50)
</script>
```

ES modules — **import every class and helper individually** (`Color`, `Matrix`, `Runner`, ... are NOT properties of the imported `SVG` function in module builds, unlike the global browser object):

```js
import { SVG, Color, Matrix, Runner, Timeline } from '@svgdotjs/svg.js'
```

Node.js requires a DOM first (`svgdom`) — see `references/nodejs.md`.

`SVG()` does not set a document size automatically; always call `size()` (e.g. `size('100%', '100%')` to match the parent).

## The `SVG()` function

One function, four jobs:

```js
var draw = SVG()                    // new document (SVG.Svg, a Container)
var rect = SVG('#myRect')           // adopt/find existing element via CSS selector
var circle = SVG('<circle>')        // create element from a fragment string
var obj = SVG(domNode)              // wrap an existing native SVGElement
```

## Core concepts

- **Chainable setters**: methods like `move()`, `fill()`, `size()` return the element, so calls chain: `draw.rect(100, 100).fill('#f06').move(20, 20)`.
- **Constructors live on containers**: `draw.rect(...)`, `draw.group()`, `group.circle(...)` — the element is appended to that container. Bare constructors (`new Rect()`) exist for fine control but need explicit `addTo()`.
- **`animate()` returns a `Runner`, not the element.** After `animate()`, chained calls configure the animation; the element only changes as the animation runs: `rect.animate(1000).move(200, 100).fill('#f06')`.
- **Each element owns a Timeline** (created lazily). Runners scheduled on different elements do not share a clock; assign the same `Timeline` to coordinate them.
- **Getter/setter duality**: `rect.x()` with no args reads, `rect.x(10)` writes. This applies to `x/y/cx/cy/size/width/height/radius/opacity/id/transform/data/...`.

## Gotchas (read before writing code)

- **Two `<svg>` elements after first init is not a bug**: SVG.js creates one invisible parser document to compute path data/bboxes of detached elements (see FAQ). Only one is ever created.
- **`attr()` positioning only works with native attributes.** `rect.attr({ cx: 20 })` and `circle.attr({ x: 50 })` are silently ignored. Use the geometry methods (`move`, `x`, `y`, `center`, `cx`, `cy`) which work for every element type.
- **Positioning methods assume unitless user coordinates.** With percentage/unit sizing, native-attribute methods mostly still work but non-native ones give wrong getters AND setters. Keep `dx()`/`dy()`/`dmove()` in the same unit the element is positioned in.
- **Groups have no geometry of their own** — they don't listen to `x/y/width/height`. Reposition a group with `group.translate(x, y)`; `move()` would move the children. For a container with its own geometry use `nested()`.
- **Absolute vs relative transforms**: `transform({...})` replaces the local transform each call (default); `transform({...}, true)` composes. The sugar helpers (`translate()`, `rotate()`, `scale()`...) are relative and always compose.
- **Animating paths** only works when start and target use the same commands (`M`, `C`, `S`, ...).
- **Text `leading()`** assumes every first-level `<tspan>` is one line; multi-tspan single lines render scrambled with it.
- **Masks vs clip paths**: mask visibility is driven by fill color — white = fully visible, so the mask shape usually needs `fill('#fff')`. Clip paths adopt the clip geometry (events only fire inside it) and cannot express opacity.
- **`animate()` scheduling**: default `when: 'after'` queues after the previous runner. `'with-last'`/`'now'` run parallel; `'absolute'` uses an absolute timeline time. Different elements = different timelines, so parallel runners on different elements do NOT sync by default.
- **Controller runners** (`SVG.Spring`, `SVG.PID`) determine their own end time: don't place them in duration-based sequences or play them in reverse. Retargeting is their superpower (see animating reference); `after()` may then fire more than once.
- **Events**: `this` inside a handler is the element. `fire(event, data)` dispatches with `detail` carrying the data; `dispatch()` returns the event so you can check `defaultPrevented`. Custom events should be namespaced (`'myevent.wicked'`) to avoid collisions.
- **`transform()` getter returns a decomposition** of the resulting matrix (translateX/scaleX/rotate/...), not a log of the calls. It excludes parent transforms — use `ctm()`/`screenCTM()` for accumulated matrices.
- **Node.js**: `registerWindow(window, document)` MUST run before creating any SVG.js object; nothing renders headless. Font files must be configured for text measurement.

## Writing SVG.js code — decision order

1. Environment: browser or Node? (Node → `references/nodejs.md`).
2. Create the canvas: `SVG().addTo(selector)`; set `size()`.
3. Pick the container: plain document, `group()`, `nested()`, `symbol()` (not rendered, for `use()`), `defs()` (for reusable paints/markers), `link()`.
4. Build elements with container constructors; set attributes via `attr()` or sugar (`fill()`, `stroke()`, `move()`, `size()`).
5. Reference existing nodes with `SVG(selector)` / `find()` / `findOne()`; traverse with `children()`, `first()`, `parent()`, `parents()`, `root()`.
6. Reuse paints/geometry: gradients, patterns, masks, clip paths, markers, `use()`.
7. Animate with `animate()`; orchestrate with a shared `Timeline` when elements must sync.
8. Export with `svg()`; in Node write `canvas.svg()` to a file.

## References — load on demand

- `references/elements.md` — creating/referencing elements; containers (svg, group, nested, symbol, defs, link, fragment); shapes (rect, circle, ellipse, line, polyline, polygon, path, text, tspan, textpath, image); paint & effects (gradient, pattern, mask, clipPath, use, marker, style, foreignObject).
- `references/manipulating.md` — attr(), positioning, sizing, fill/stroke/opacity, transforms, css/classes/data/remember, document tree ops, arranging, geometry (bbox, viewbox, zoom).
- `references/animating.md` — animate(), Runner, scheduling, easing, controllers (Spring/PID), Timeline, orchestrating multi-element animation.
- `references/events.md` — event sugar, on/off/fire/dispatch, custom & namespaced events, coordinate conversion with `point()`.
- `references/classes.md` — Box, List, Array, PointArray, PathArray, Color, Matrix, Number, Point, Morphable, EventTarget.
- `references/importing-exporting.md` — svg() getter/setter, export modifiers, html(), xml().
- `references/extending.md` — SVG.extend(), subclassing, custom elements, official plugins.
- `references/nodejs.md` — svgdom setup, registerWindow/getWindow/withWindow, writing SVG to files, font config, compatibility.

Read the relevant reference before writing the corresponding code; the SKILL.md above plus the references replace guessing at SVG.js API details. Verify the deliverable in a browser (or Node) — SVG.js does not throw on most mistakes, it silently ignores invalid attribute targets.
