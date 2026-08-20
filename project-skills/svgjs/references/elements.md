# Elements — creating, referencing, containers, shapes, paints

## Creating elements

Two equivalent ways — container constructor (appends immediately) or bare constructor (needs `addTo`):

```js
var rect = draw.rect(100, 100)                    // appended to draw
var rect = new Rect().size(100, 100).addTo(draw)  // manual
var rect = new Rect(node)                          // wrap an existing node
```

Attributes can be passed to the constructor (shorthand for `attr()`):

```js
var rect = new Rect({ width: 100, height: 100 }).addTo(draw)
var rect = draw.rect({ width: 100, height: 100 })
```

Generic element for anything SVG.js has no class for (`SVG.Dom`):

```js
var el = draw.element('title', { id: 'myId' })
el.words('This is a title.')   // -> <title>This is a title.</title>
```

Create from markup / HTML namespace:

```js
var rect = SVG('<rect width="100" height="100">')
var input = SVG('<input type="text">', true)   // true = HTML namespace
```

## Referencing elements

```js
var rect = SVG('rect.my-class')         // first match, any CSS selector
var list = SVG.find('.someClass')       // SVG.List of all matches
var list = SVG.find('.someClass', group) // search inside a node
var one  = group.findOne('rect')        // first match inside element
var list = group.find('.myClass')
```

Every wrapper has `element.node` (native SVGElement) and every native node has `node.instance` (SVG.js wrapper). To adopt a native element: `SVG(domNode)`.

Child references: `children()`, `each(fn, deep?)` (deep traversal with `true`), `first()`, `last()`, `get(i)`, `has(el)`, `index(el)`, `clear()`.

Parent references: `parent()` (or `parent(SVG.Svg)` / `parent('.test')` to find a matching ancestor), `parents()` (all ancestors up to root or a matcher), `root()` (root SVG), `defs()` via `rect.root().defs()`.

Linked elements (`<use>`, fill gradients, clip paths, ...) resolve through `reference(attrName)`:

```js
use.reference('href')          // -> used element instance
rect.reference('fill')         // -> gradient or pattern instance
circle.reference('clip-path')  // -> clip instance
path.reference('marker-end')
```

## Containers

### SVG.Svg (the `SVG()` result)

`nested()` creates a nested SVG document inside another (a container WITH its own geometry — use when you need `x/y/width/height`). `isRoot()`, `namespace()`/`removeNamespaces()` manage the xmlns attributes.

### Group — `group()`

No geometry of its own; transforms apply to the set as one. Children keep positions relative to the group. Reposition via `translate()`, NOT `move()`. `group.add(rect)` moves an element in; `group.path('M10,20L30,40')` constructs directly.

### Symbol — `symbol()`

Like a group but never rendered — ideal as a reusable master for `use()`:

```js
var symbol = draw.symbol()
symbol.rect(100, 100).fill('#f09')
var use = draw.use(symbol).move(200, 200)
```

### Defs — `defs()`

Container for referenced elements; children are not rendered directly. Where gradients/patterns/markers and reusable `use()` masters live. `draw.defs()`; also reachable from any element via `root().defs()`.

### Link — `link(url)` / `element.linkTo(url)`

```js
var link = draw.link('http://svgdotjs.github.io/')
var rect = link.rect(100, 100)          // rect becomes the link target
link.to('http://apple.com')             // change href
link.target('_blank')                   // target attribute
rect.linkTo('http://...')               // wrap the other way round
rect.linkTo(function (link) { link.to('http://...').target('_blank') })
rect.unlink()                           // remove <a> wrapper
rect.linker()                           // the <a> element or null
```

### Fragment — `new Fragment()`

Document-fragment wrapper; not a Container but constructs elements on itself and can be added in one go:

```js
const frag = new Fragment()
frag.rect(100, 100)
frag.circle(100)
draw.add(frag)      // both appear in draw
frag.svg()          // '<rect ... /><circle ... />'
```

## Shapes

Rect: `draw.rect(w, h)`; rounded corners via `rect.radius(10)` or `rect.radius(10, 20)` (rx, ry).

Circle: `draw.circle(diameter)`; `circle.radius(75)`.

Ellipse: `draw.ellipse(w, h)`; `ellipse.radius(75, 50)`.

Line: `draw.line(x1, y1, x2, y2)`; update with `plot()` in any of four forms:

```js
line.plot(50, 30, 100, 150)                 // coords
line.plot('0,0 100,150')                    // string
line.plot([[0, 0], [100, 150]])             // point array
line.plot(new SVG.PointArray([[0,0],[100,150]]))
```

Polyline/Polygon: `draw.polyline('0,0 100,50 50,100')` or arrays `[[x,y],...]` or flat `[0,0,100,50,50,100]`. Polygons auto-close (first and last point connect). `plot()` to update (animatable); `array()` returns the `SVG.PointArray`; `clear()` clears the parse cache.

Path: `draw.path('M0 0 H50 A20 20 0 1 0 100 50 v25 C50 125 0 85 0 85 z')`.

```js
path.length()          // total length
path.pointAt(105)      // SVG.Point on the path at length 105
path.plot('M10 80 C ...')  // update; animatable only between same command sets
path.text('SVG.js rocks!') // creates a textPath on this path
path.targets()         // all textPath elements referencing this path
```

### Text

Two construction modes — newline-split string, or a builder block:

```js
var text = draw.text("Lorem ipsum.\nCras sodales.")   // tspan per line
var text = draw.text(function (add) {
  add.tspan('Lorem ipsum ').newLine()
  add.tspan('consectetur').fill('#f06')
  add.newLine('Shortcut for a new line')
})
var text = draw.plain('Single unstyled line, no newlines')  // also text.plain()
```

Key methods:

- `text.amove(x, y)` — position by baseline and text-anchor (regular `move()` uses the upper-left corner); `ax()`/`ay()` for one axis.
- `text.font({ family, size, anchor, leading, stretch, style, variant, weight })` — any other key falls through to `attr()`. Getter: `text.font('leading')`.
- `text.leading(1.3)` — sets `dy` of each line to 130% of font size. Assumes one tspan per line (see SKILL.md gotcha).
- `text.build(true/false)` — toggle build mode; off means `plain()`/`tspan()` first `clear()`. Auto-toggled around builder blocks.
- `text.path(pathString)` — returns a `SVG.TextPath`; `text.textPath()` retrieves it; `textpath.track()` returns the linked `<path>`.
- `text.rebuild(true/false)` — rebuilds tspans when `font-size`/`x`/`leading` change; fires the `rebuild` event.
- `text.text()` getter/setter for raw content; `text.length()` total computed text length; `text.clear()`.
- `text.animate(500).amove(100, 50)` — amove is animatable.

Tspan: `text.tspan('...')`; `tspan.newLine()`, `tspan.dx()`, `tspan.dy()` (relative offsets, animatable), nested `tspan.tspan(...)`, `tspan.text(string|block)`, `tspan.plain()`, `tspan.length()`, `tspan.clear()`. `SVG.TextPath` inherits from `SVG.Text`.

TextPath constructor: `draw.textPath('Some text', 'M 100 200 C ...')`. `startOffset` in non-percentage units is a distance along the path in user units.

### Image

```js
var image = draw.image('/path/to/image.jpg', function (event) {
  // loaded; event.target.naturalWidth / naturalHeight
})
image.load('/other.jpg', callback)   // swap source
image.on('load', fn)                 // or bind 'load'/'error' events
```

## Paints & effects

### Gradient

```js
var gradient = draw.gradient('linear', function (add) {
  add.stop(0, '#333')
  add.stop(1, '#fff')
})
rect.fill(gradient)            // or rect.attr({ fill: gradient })
gradient.url()                 // 'url(#SvgjsGradient1234)'
gradient.from(0, 0).to(0, 1)   // direction in percent
gradient.radius(0.5)           // radial only
gradient.update(function (add) { add.stop(0.1, '#333', 0.2) })  // rebuild stops
gradient.get(0)                // nth stop
gradient.targets()             // elements whose fill references it
```

`stop(offset, color, opacity?)` — offset is float 0–1 or percent string; object form `stop({ offset, color, opacity })`. Update a stop: `stop.update(0, '#333')`.

### Pattern

```js
var pattern = draw.pattern(20, 20, function (add) {
  add.rect(20, 20).fill('#f06')
})
rect.fill(pattern)             // or attr({ fill: pattern })
pattern.url()                  // 'url(#SvgjsPattern1234)'
pattern.update(function (add) { add.circle(15).center(10, 10) })
pattern.targets()
```

### Mask

```js
var mask = draw.mask().add(draw.ellipse(80, 40).move(10, 10).fill('#fff'))
rect.maskWith(mask)            // or rect.maskWith(ellipse) directly
rect.unmask()                  // remove mask
rect.masker()                  // the mask instance (to mutate it)
mask.targets()                 // masked elements
mask.remove()                  // also unmask()es all masked elements
```

Fill color drives visibility: white = 100% visible. Gradients work as mask fills too.

### ClipPath

Same shape as masks; clipped elements adopt the clip geometry; no opacity support.

```js
var clip = draw.clip().add(text).add(ellipse)   // draw.clip() puts it in defs
rect.clipWith(clip)            // or clipWith(ellipse)
rect.unclip()
rect.clipper()                 // the clipPath instance
```

Direct constructor creates a detached element — add it to defs yourself before referencing:

```js
import { ClipPath } from '@svgdotjs/svg.js'
var clip = new ClipPath()
draw.defs().add(clip)
clip.add(draw.circle(80))
rect.clipWith(clip)
```

### Use

```js
var rect = draw.defs().rect(100, 100).fill('#f09')  // master in defs = not rendered
var use  = draw.use(rect).move(200, 200)            // clone-ish instance
var use  = draw.use('elementId', 'path/to/file.svg') // external file reference
```

Edits to the master reflect on all uses.

### Marker

```js
var marker = draw.marker(10, 10, function (add) { add.rect(10, 10) })  // reusable, in defs
path.marker('start', 10, 10, function (add) { add.circle(10).fill('#f06') })  // direct
path.marker('mid', marker)     // apply a reusable marker
```

Positions: `start`, `mid`, `end`. Marker API: `marker.width()`, `marker.height()`, `marker.size(w, h)`, `marker.ref(x, y)` (refX/refY; defaults to half size), `marker.orient(50)`, `marker.update(block)`. Get from target: `path.reference('marker-end')`.

### Style & ForeignObject

```js
var style = draw.style('#myId', { color: 'blue' })
style.rule('.myClass', { fontSize: 16 })
var style = draw.fontface('Arial', 'url', { /* other font-face params */ })

var foreignObject = draw.foreignObject(width, height)
foreignObject.add(SVG('<input type="text">', true))  // HTML in SVG
```
