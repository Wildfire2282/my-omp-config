# Extending and plugins

## SVG.extend()

Add methods at any level of the inheritance stack (`SVG.Base > SVG.EventTarget > SVG.Dom > SVG.Element > SVG.Shape > ...`). Methods on a base class apply to all descendants; more specific classes override.

```js
SVG.extend(SVG.Shape, {
  paintRed: function () { return this.fill('red') }
})

SVG.extend(SVG.Ellipse, {
  paintRed: function () { return this.fill('orangered') }  // overrides for ellipses
})

SVG.extend(SVG.Svg, {
  paintAllPink: function () {
    this.each(function () { this.fill('pink') })
  }
})

SVG.extend([SVG.Ellipse, SVG.Path, SVG.Polygon], { /* multiple at once */ })
```

Container-level extension adds new constructors:

```js
SVG.extend(SVG.Container, {
  rounded: function (width, height) {
    return this.put(new SVG.Rounded).size(width, height)
  }
})
```

## Subclassing — custom elements

```js
SVG.Rounded = class extends SVG.Rect {
  size(width, height) {
    return this.attr({ width, height, rx: height / 5, ry: height / 5 })
  }
}

SVG.extend(SVG.Container, {
  rounded: function (width, height) {
    return this.put(new SVG.Rounded).size(width, height)
  }
})

var rounded = draw.rounded(200, 100)
```

## Plugins (official ecosystem)

- `svg.easing.js` — more easing equations for animations
- `svg.draggable.js` — make elements draggable
- `svg.filter.js` — SVG filters on elements
- `svg.topath.js` — convert any shape to a path
- `svg.topoly.js` — convert a path to polygon/polyline
- `svg.panzoom.js` — wheel/pinch zoom for viewbox elements
- `svg.colorat.js`, `svg.math.js`, `svg.path.js`, `svg.shapes.js` — color, math, path, and shape helpers
- `ngx-svg` — Angular wrapper

All under the `svgdotjs` GitHub org (e.g. `@svgdotjs/svg.draggable.js`).
