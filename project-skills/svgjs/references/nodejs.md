# SVG.js in Node.js (with svgdom)

SVG.js does not ship a DOM. Register one first; the recommended implementation is `svgdom`.

## Setup

```sh
npm install @svgdotjs/svg.js svgdom
```

```js
import { createSVGWindow } from 'svgdom'
import { SVG, registerWindow } from '@svgdotjs/svg.js'

const window = createSVGWindow()          // window with document + <svg> root
const document = window.document
registerWindow(window, document)          // REQUIRED before creating any SVG.js object

const canvas = SVG(document.documentElement)
canvas.rect(100, 100).fill('yellow').move(50, 50)
```

## Write to a file

```js
import { writeFileSync } from 'node:fs'
import { createSVGWindow } from 'svgdom'
import { SVG, registerWindow } from '@svgdotjs/svg.js'

const window = createSVGWindow()
registerWindow(window, window.document)

const canvas = SVG(window.document.documentElement).size(300, 300)
canvas.rect(100, 100).fill('#f06').move(50, 50)
canvas.circle(80).fill('none').stroke({ color: '#000', width: 4 }).move(160, 70)

writeFileSync('drawing.svg', canvas.svg())   // or canvas.node.outerHTML
```

## HTML and XML documents

```js
import { createHTMLWindow } from 'svgdom'   // full HTML document
import { SVG, registerWindow } from '@svgdotjs/svg.js'
const window = createHTMLWindow()
registerWindow(window, window.document)
const canvas = SVG().addTo('body').size(300, 300)

import { createWindow } from 'svgdom'       // any XML namespace
const window = createWindow('http://www.w3.org/1998/Math/MathML', 'math')
registerWindow(window, window.document)
```

## CommonJS

On Node 22.13+ both packages load with `require()`:

```js
const { createSVGWindow } = require('svgdom')
const { SVG, registerWindow } = require('@svgdotjs/svg.js')
```

## Fonts for text measurement

svgdom loads Open Sans Regular by default and needs configured font files for accurate text bounding boxes:

```js
import { config } from 'svgdom'
config
  .setFontDir('./fonts')
  .setFontFamilyMappings({ Arial: 'arial.ttf', 'Arial-italic': 'arial_italic.ttf' })
  .preloadFonts()
```

Bold/italic variants only exist when the matching font file is loaded and mapped.

## Window management

```js
registerWindow(window, document)   // set global window; registerWindow() clears it
getWindow()                        // currently registered window (DOM constructors, CustomEvent, ...)
withWindow(window, (win, document) => {
  // temporarily switch; previous window/document restored afterwards
})
```

Use `withWindow()` for short-lived or test-only DOM switches; register once for most scripts.

## Limitations

- Browser/layout/rendering APIs are unavailable in a headless DOM; `screenCTM()` and friends that need rendering give no meaningful result.
- DOM API coverage depends on the registered implementation — check the svgdom README for selector support.

## Browser compatibility (transpiled builds)

The standard build targets modern browsers (`last 1 version or > 0.25% or not maintained node versions or not dead`). For IE11-only needs, load `polyfillsIE.js` from the release archive BEFORE your transpiled bundle — it supplies IE-specific SVG APIs but does not transpile syntax; configure your own build's syntax transforms.
