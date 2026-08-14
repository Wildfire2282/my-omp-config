# Classes & utilities

## SVG.Box

Properties: `x`, `y`, `width`, `height`, `x2`, `y2`, `cx`, `cy`.

```js
box.merge(otherBox)            // new box enclosing both
box.transform(matrix)          // transformed copy
box.addOffset()                // copy with window scroll offset added (for getBoundingClientRect-based boxes)
new SVG.Box().isNulled()       // true if x,y,width,height all zero
box.toArray()                  // [x, y, width, height]
box.toString()                 // 'x y width height'
```

## SVG.List

Native-array subclass; element methods apply to every member and return a new List; chaining works.

```js
var list = new SVG.List([rect])
list.push(circle)
list.fill('#ff0')                  // all members
var fills = list.fill()            // collect getter results
list.animate(3000).fill('#ff0')    // animate all
list.each('fill', 'blue')          // call method with args
list.each(function (item) { return item.fill('blue') })
list.toArray()                     // shallow native array
```

## SVG.Array and subclasses

Parses whitespace/comma-delimited number strings; `SVG.PointArray` and `SVG.PathArray` add geometry ops.

```js
new SVG.Array('0.343 0.669 0.119 ...')
var array = new SVG.PointArray([[0, 0], [100, 100]])
array.clone()          // deep clone (multi-dim arrays), same class
array.to('100,0 0,100 200,200')  // returns SVG.Morphable (start and target must match length)
array.move(33, 75)     // PointArray/PathArray only: shift geometry
array.size(222, 333)   // PointArray/PathArray only: resize geometry
array.reverse()
array.bbox()
array.toArray() / array.toSet() / array.toString() / array.valueOf()
```

PointArray extras: `toLine()` → `{ x1, y1, x2, y2 }`; `transform(matrix)` (copy) vs `transformO(matrix)` (in place).

PathArray: segments as `[command, ...args]`, e.g. `['M', 0, 0]`, `['C', 20, 20, 40, 20, 50, 10]`, `['H', 200]`, `['A', 30, 50, 0, 0, 1, 162, 163]`, `['z']`. Both string and flat-array forms parse.

## SVG.Color

Accepted: hex (`'#f06'`, `'#ff0066'`), rgb string (`'rgb(255, 0, 102)'`), objects `{r,g,b}` / `{x,y,z}` / `{h,s,l}` / `{l,a,b}` / `{l,c,h}` / `{c,m,y,k}`, or positional `new SVG.Color(255, 0, 102, 'rgb')`.

```js
color.rgb() / color.xyz() / color.hsl() / color.lab() / color.lch() / color.cmyk()  // convert
new SVG.Color('#ff0066').to('#000').at(0.5).toHex()   // '#7f0033' (morphing)
color.toHex() / color.toRgb()
color.toArray()    // [255, 0, 102, 0, 'rgb'] (4th channel for CMYK)
color.toString()   // hex for RGB, function notation for other spaces
SVG.Color.random('vibrant')  // vibrant|sine|pastel|dark|rgb|lab|grey (vibrant default)
```

## SVG.Matrix

Construct from: nothing (identity), `(a, b, c, d, e, f)`, string, `{a..f}`, transform object `{ translate: [20, 20] }`, native `SVGMatrix`, or an `SVG.Element`.

Most operations return a transformed COPY; `*O` variants mutate in place (`translateO`, `rotateO`, `scaleO`, `skewO`, `shearO`, `flipO`, `inverseO`, `multiplyO`, `lmultiplyO`, `aroundO`).

```js
matrix.transform({ rotate: 20 })
matrix.decompose(cx, cy)                 // affine params (see transform() getter)
matrix.around(cx, cy, otherMatrix)
matrix.to(matrix).at(0.27)               // morph
matrix.clone()
matrix.flip('x') / matrix.flip('y', 150) // axis, optional position
matrix.inverse()                         // throws when not invertible
matrix.multiply(m2) / matrix.lmultiply(m2)  // right / left multiplication
matrix.rotate(45) / matrix.rotate(45, cx, cy)
matrix.scale(2) / matrix.scale(2, 3, cx, cy)
matrix.shear(0.5, cx, cy)
matrix.skew(0, 45) / matrix.skew(0, 45, cx, cy) / matrix.skewX(d) / matrix.skewY(d)
matrix.equals(other)                     // tolerance-compared
matrix.translate(10, 20)
matrix.toArray()  // [a,b,c,d,e,f] | matrix.valueOf()  // {a..f}
matrix.toString() // 'matrix(1,0,0,1,0,0)'
```

## SVG.Number

String-aware number math:

```js
var number = new SVG.Number('78%')
number.plus('3%').toString()   // '81%'
number.valueOf()               // 0.81
number.minus('3%') / number.divide('3%') / number.times(2)
number.convert('px')
new SVG.Number('79%').to('3%').at(0.55).toString()  // '37.2%' (morph)
number.toArray()  // [0.25, '%'] | toString() '25%' | toJSON() '25%'
```

## SVG.Point

```js
new SVG.Point(1) / (1, 1) / ([1, 1]) / ({x, y}) / (anotherPoint)
point.clone()
point.to(new SVG.Point(11, 10)).at(0.5)  // {x: 6, y: 5.5}
point.transform(matrix)      // copy; transformO(matrix) in place
point.toArray()              // [x, y]
```

## SVG.Morphable

Interpolates between compatible values; used internally for animation, exported for plugins/custom value classes.

```js
const morph = new SVG.Morphable().from(0).to(100)
morph.at(0.25).valueOf()   // 25
morph.type() / morph.type(SVG.Point)   // value class get/set
morph.stepper(new SVG.Ease('<>'))
morph.from() / morph.to()  // getters without args, setters with
```

Built-in interpolation: numbers/units, colors, arrays, point arrays, path arrays, points, boxes, matrices, transform objects, plain objects, non-interpolated values.

Custom types: implement `init(value)` + `toArray()`, then `SVG.registerMorphableType(MyClass)` and `SVG.makeMorphable()` (adds `to()`, `fromArray()`, `toConsumable()`, `morph()` to the prototype). Built-ins are configured at load.

## SVG.EventTarget

Base class of every SVG.js object; adds `on()`, `off()`, `fire()`, `dispatch()` (see `references/events.md`).
