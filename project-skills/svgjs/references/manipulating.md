# Manipulating — attributes, positioning, sizing, paint, transforms, structure, geometry

## Attributes — `attr()`

```js
rect.attr('x', 50)                        // set one
rect.attr({ fill: '#f06', 'fill-opacity': 0.5, stroke: '#000', 'stroke-width': 10 })
rect.attr('x', 50, 'http://www.w3.org/2000/svg')  // namespaced
rect.attr('fill', null)                   // remove
rect.attr('x')                            // get one
rect.attr()                               // get all as object
rect.attr(['x', 'y'])                     // get several
```

Animateable for numbers, arrays, colors, ... via `animate()`.

## Positioning

All work for EVERY element type (unlike raw `attr`, see SKILL.md gotcha):

```js
rect.move(200, 350)     // upper-left corner
rect.x(200) / rect.y(350)   // single axis; getters without args
rect.center(150, 150)   // by center
rect.cx(200) / rect.cy(350)
rect.dmove(10, 30)      // shift relative to current position
rect.dx(200) / rect.dy(200)
```

All animateable. `dmove`/`dx`/`dy` values must use the same unit as the element's current position.

## Sizing

```js
rect.size(200, 300)     // width, height
rect.size(200)          // proportional (keeps ratio)
rect.size(null, 200)    // only height
rect.width(200) / rect.height(325)   // single side; getters without args
circle.radius(10)       // circle r; ellipse/rect: radius(rx, ry) or radius(r) both
```

## Fill / stroke / opacity

```js
rect.fill({ color: '#f06', opacity: 0.6 })
rect.fill('#f06')
rect.fill('images/shade.jpg')         // image fill by URL
rect.fill(draw.image('img.jpg', fn))  // or an Image instance

rect.stroke({ color: '#f06', opacity: 0.6, width: 5, linecap: 'round',
              linejoin: 'round', miterlimit: 4, dasharray: '10,5', dashoffset: 2 })
// keys map to stroke-* attributes: linecap -> stroke-linecap, dasharray -> stroke-dasharray
rect.stroke('#f06')
rect.stroke('images/shade.jpg')

rect.opacity(0.5)
```

## Transforms

`transform()` replaces the local transform by default; pass `true` (or an element/matrix) as second arg to compose. Sugar helpers always compose.

```js
element.transform({ rotate: 125, translateX: 50, translateY: 100, scale: 3 })
```

Transform object keys:

| Transform | Accepted forms |
| --- | --- |
| Translation | `translate: [x, y]`, `translate: {x, y}`, `translateX`, `translateY`, `tx`, `ty` |
| Rotation | `rotate: degrees` / `theta: degrees` |
| Scale | `scale: factor`, `scale: [x, y]`, `scaleX`, `scaleY` |
| Skew | `skew: degrees`, `skew: [x, y]`, `skewX`, `skewY` |
| Shear | `shear: factor` |
| Flip | `flip: 'x' | 'y' | 'both' | true` |
| Origin | `origin: [x, y]`, `origin: {x, y}`, `originX`, `originY`, `ox`, `oy` |
| Final origin position | `position: [x, y]`, `positionX`, `positionY`, `px`, `py` |
| Relative origin move | `relative: [x, y]`, `relativeX`, `relativeY`, `rx`, `ry` |

Origin defaults to the element's bbox center; string forms like `origin: 'top left'` work. Raw matrix: `transform({ a: 1, b: 0, c: 0, d: 1, e: 10, f: 20 })`.

Getter (no args) decomposes the local matrix: `translateX`, `translateY`, `shear`, `scaleX`, `scaleY`, `rotate` (deg), `originX`/`originY` (= 0), and `a`–`f`. `transform('rotate')` gets one value. Parent transforms excluded — use `ctm()`/`screenCTM()` for those.

Helpers:

```js
element.rotate(45)                 // around center; rotate(45, cx, cy) for an origin
element.scale(2) / scale(0.5, -1)  // uniform or per-axis; origin args optional
element.skew(0, 45)                // degrees; skew(x, y, cx, cy)
element.shear(0.5)
element.translate(0.5, -1)         // relative
element.relative(20, 10)           // moves the transform origin relatively
element.flip('x')                  // 'y' | 'both' | true; origin as 2nd arg
```

Matrix API:

```js
element.matrix(new SVG.Matrix().translate(20, 30))  // replaces transform (no compose)
element.matrix(1, 0, 0, 1, 20, 30)
const m = element.matrix()                          // getter -> SVG.Matrix
const local = element.matrixify()                   // own transform attr as one matrix (no parents)
const viewport = element.ctm()                      // to SVG viewport coords (getCTM wrapper)
const screen = element.screenCTM()                  // to screen coords
const localPoint = element.point(clientX, clientY)  // screen -> local
element.untransform()                               // remove transform attribute
```

`screenCTM()` needs the element rendered; otherwise it logs a warning and returns identity.

## Styles, ids, classes, data, memory

```js
element.css('cursor', 'pointer')          // style attribute
element.css({ cursor: 'pointer', fill: '#f03' })
element.css('cursor', null)               // delete
element.css('cursor') / element.css() / element.css(['cursor', 'fill'])

element.hide() / element.show() / element.visible()

rect.id()                    // getter creates a unique id if none
rect.id('my-unique-id') / rect.id(null)

element.addClass('pink') / element.removeClass('pink') / element.toggleClass('pink')
element.hasClass('purple') / element.classes()   // array

rect.data('key', { value: 0.3 })   // stored as JSON by default
rect.data({ a: 1, b: 2 })          // multiple
rect.data('key', 'value', true)    // 3rd arg = store raw, no JSON
rect.data('key') / rect.data() / rect.data(['k1', 'k2']) / rect.data('key', null)

rect.remember('oldBBox', rect.bbox())   // in-memory storage
rect.remember({ a: 1, b: 2 })
rect.remember('oldBBox')                // getter
rect.forget('oldBBox') / rect.forget()  // one / all
```

## Document tree

```js
group.add(rect)               // rect becomes child of group; returns group
group.add('#someEl')          // selector, node, or '<rect>' string accepted
group.add(rect, 0)            // 2nd arg = insert position
rect.addTo(group)             // rect becomes child of group; returns rect

rect.clone()                  // deep clone, new ids: clone(deep=true, assignNewId=true)
group.put(rect)               // add + return the CHILD (wraps non-svgjs args)
rect.putIn(group)             // add + return the PARENT
rect.remove()
rect.replace(draw.circle(100))   // swap at same position
rect.toParent(group)          // move, keeping visual appearance (merges transforms)
rect.toRoot()                 // toParent with root as target
group.ungroup()               // move children to parent, keeping appearance
drawing.flatten()             // break up all nested containers
rect.wrap('<g>')              // wrap rect in a new group
```

Note: `Defs` cannot be `ungroup()`ed or `flatten()`ed.

## Arranging

```js
rect.after(circle)        // insert circle after rect
rect.before(circle)
rect.insertAfter(circle)  // insert SELF after circle
rect.insertBefore(circle)
rect.back() / rect.backward() / rect.front() / rect.forward()
rect.next() / rect.prev() / rect.siblings() / rect.position()
```

## Geometry

```js
var point = path.point(e.pageX, e.pageY)   // screen -> element coords (SVG.Point)
rect.inside(60, 70)                        // bbox hit test (relative position only)
element.bbox()   // untransformed tightest box (SVG.Box)
element.rbox()   // transformed box; rbox(drawing) -> in drawing's coordinate system
drawing.viewbox(10, 10, 500, 600)          // setter: coords | '10 10 500 600' | box
drawing.viewbox()                          // getter
drawing.zoom(10)                           // setter; zoom(10, {x: 20, y: 20}) zooms into point
drawing.zoom()                             // getter
```
