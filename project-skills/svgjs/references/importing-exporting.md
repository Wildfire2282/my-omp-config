# Importing / exporting SVG, HTML, XML

## Export — `svg()` getter

```js
draw.svg()          // full markup string of the element and contents
rect.svg()          // works on any element
draw.svg(false)     // contents only, no wrapper element
```

Export modifier — run a function on every node before serializing; return `false` to remove, return a new element to replace:

```js
var rounded = draw.svg(function (node) { node.round(4) }, false)

var tidied = draw.svg(function (node) {
  if (node.fill() == 'blue') return false                       // drop
  return new Circle().radius(5).fill(node.fill())               // replace
}, false)
```

## Import — `svg()` setter

```js
draw.svg('<g><rect width="100" height="50" fill="#f06"></rect></g>')
draw.svg('<rect><rect><rect>')   // multiple children at once
group.svg('<rect><rect>', true)  // true = replace the element itself with the import
```

The setter returns the PARENT of the element `svg()` was called on (replacing a node with multiple nodes has no single return node).

## HTML and XML

```js
draw.html('<div></div>')   // import with HTML namespace
draw.html()                // export

draw.xml('<my-element></my-element>', myNamespace)  // import with a namespace
draw.xml()                 // export
```

## Node.js output

`canvas.svg()` (or `canvas.node.outerHTML`) serializes; write with `fs` — see `references/nodejs.md`.
