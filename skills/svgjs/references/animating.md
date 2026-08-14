# Animating — animate(), Runner, Timeline, easing, controllers

Architecture: an element owns a `Timeline` (the clock) → `element.animate()` creates and schedules a `Runner` on it → chained element setters (`move()`, `fill()`, `transform()`...) add work to the runner.

```js
const rect = draw.rect(100, 100)
rect.animate(1000).move(200, 100).fill('#f06')
```

**`animate()` returns the Runner, not the element** — subsequent chained calls configure the animation.

## animate()

```js
element.animate(duration, delay, when)
// defaults: 400ms, 0ms, 'after'
rect.animate(2000, 1000, 'now').attr({ fill: '#f03' })
```

Options-object form:

```js
rect.animate({ duration: 2000, delay: 1000, when: 'now', times: 5, swing: true, wait: 200 }).fill('#f03')
```

`when` scheduling:

| Value | Start time |
| --- | --- |
| `after` / `last` | After the most recently scheduled runner (default) |
| `with-last` | At the start of the most recently scheduled runner |
| `now` | At the timeline's current time + `delay` |
| `absolute` / `start` | At absolute timeline time `delay` |
| `relative` | Reschedule: move previous start by `delay` |

Sequence with `after`; parallel with `with-last`/`now`; `absolute` for cross-element coordination on a shared timeline. Note: different elements have different timelines, so `with-last` on another element does NOT sync with this one.

Chaining and delays — call `animate()` on a runner to queue the next segment:

```js
rect.animate(500).fill('#f03').animate(500).move(100, 100)
rect.animate(500).fill('#f03').delay(200).animate(500).move(100, 100)
// equivalent: .animate(500, 200).move(...)
```

## SVG.Runner

Animatable setters include: `attr()`, `css()`, `fill()`, `stroke()`, `move()`, `center()`, `size()`, `plot()`, `transform()`, `rotate()`, `scale()`, `translate()`, `font()`, `viewbox()`, `zoom()`.

Starting values are read when the runner first executes — queued animations begin from the state left by earlier runners.

### Transform animation

`runner.transform(transforms, relative, affine)`:

```js
rect.animate(1000).transform({ rotate: 90, scale: 2 })          // absolute (replaces at endpoint)
rect.animate(1000).transform({ translate: [100, 0] }, true)     // relative (composes)
rect.animate(1000).translate(100, 0).rotate(90)                 // helpers are relative too
```

Relative-transform baselines are read when the runner STARTS (delayed/chained runners compose with the state left by prior animation). Default interpolation is affine (rotation takes the shortest path). Passing a `Matrix` target interpolates the six components directly and can introduce skew/scale — pass `true` as 3rd arg for affine, `false` for matrix.

Avoid overlapping absolute transform runners (they replace relative ones while times overlap).

### Direct runner creation

```js
const runner = new SVG.Runner(1000).element(rect).move(100, 100)
runner.step(250)                             // manual stepping, no timeline needed
const timeline = new SVG.Timeline()
runner.schedule(timeline)                    // automatic playback needs a timeline
timeline.play()
```

Binding: `runner.element()` / `runner.element(rect)`; `runner.timeline()` / `runner.timeline(tl)`; `runner.schedule(200, 'now')` (uses bound timeline) / `runner.schedule(timeline, 200, 'now')`; `runner.unschedule()`. `schedule()` without a timeline throws.

### Playback position

Getters without args, fluent setters with: `runner.time(ms)`, `runner.position(0..1)` (current loop; accounts for swing/reverse), `runner.progress(0..1)` (all loops + waits), `runner.loops(2.5)`. Others: `duration()`, `step(ms)` (negative = backwards), `reset()`, `finish()`, `reverse([bool])`, `active(false)` (skip while timeline advances).

### Looping

```js
runner.loop(times, swing, wait)
rect.animate(500).move(100, 0).loop(4, true, 100)   // 4 iterations, swing, 100ms between
rect.animate(500).move(100, 0).loop(true, true)     // forever (no args or true)
```

### Callbacks & events

```js
runner.during(function (position) { /* every step; `this` = runner */ })
runner.after(function (event) { /* at finished state */ })
runner.on('start' | 'step' | 'finished', fn)
```

`start`/`finished` describe forward progress across boundaries — reversing across them does NOT re-fire. For side effects that must reverse correctly, derive state from `position` in `during()` (0 = before, 1 = after). `queue(init, run)` is the low-level extension point behind animated setters; prefer `during()`.

### Persistence

Completed timed runners are normally removed from the timeline; controller runners persist by default. Keep a timed runner for seeking/reversing after finish:

```js
runner.persist()       // read
runner.persist(1000)   // retain 1000ms after ending
runner.persist(true)   // indefinitely
```

Set persistence BEFORE scheduling. Runner setting overrides the timeline default.

### Text: `amove()`

`text.animate(500).amove(100, 50)` animates by anchor/baseline; use `move()` for the visual bbox.

## Easing

Default is ease-out (`>`).

```js
rect.animate(1000).ease('<>').move(200, 0)
// '<>' in-out | '>' out | '<' in | '-' linear
runner.ease(function (position) { return position * position })
runner.ease(SVG.easing.bezier(0.42, 0, 0.58, 1))
runner.ease(SVG.easing.steps(5, 'jump-end'))
```

More equations via the svg.easing.js plugin.

## Controllers — SVG.Spring, SVG.PID

Controllers compute the next value from elapsed time and decide when they've converged (no fixed duration):

```js
const spring = new SVG.Spring(500, 10)   // settle time, overshoot %
rect.animate(spring).move(200, 200)
const pid = new SVG.PID(0.1, 0.01, 0)    // p, i, d
circle.animate(pid).move(300, 200)

spring.duration(700).overshoot(5)
pid.p(0.2).i(0.01).d(0.001).windup(500)
```

- Cannot be reliably placed in duration-based sequences or played in reverse.
- Retargeting is the point: calling the same animated setter again retargets from the current state. Absolute `transform()` animations also update their origin on retarget; relative controller transforms add another action instead of retargeting.
- `finished` fires whenever all actions converge — a retargeted controller can fire `after()` multiple times.

```js
const follow = rect.animate(new SVG.Spring()).move(100, 100)
draw.on('pointermove', function (event) {
  const point = this.point(event.clientX, event.clientY)
  follow.move(point.x, point.y)
})
```

## SVG.Timeline

Every element gets a timeline lazily via `element.timeline()` or the first `animate()`; assign one: `rect.timeline(sharedTimeline)`.

```js
timeline.play() / timeline.pause() / timeline.stop()   // seek 0 + pause
timeline.finish()   // settle all runners at targets + pause
timeline.active()   // true while a frame is scheduled

timeline.time() / timeline.time(1000)    // absolute ms
timeline.seek(250) / timeline.seek(-100) // relative
timeline.speed(2) / timeline.speed(-1)   // multiplier; negative = backwards
timeline.reverse()                       // toggle; reverse(true|false) explicit

timeline.schedule(runner, delay, when) / timeline.unschedule(runner)
for (const item of timeline.schedule()) { item.start, item.duration, item.end, item.runner }
timeline.getEndTime()    // end of most recently scheduled runner (next 'after' point)

timeline.persist() / timeline.persist(1000) / timeline.persist(true)  // default for runners
timeline.terminate()     // stop frames, remove ALL runners, reset state, release refs
```

Custom monotonic millisecond clock: `new SVG.Timeline(() => clock)` or `timeline.source(fn)`.

Seek-then-reverse pattern:

```js
rect.animate(3000).move(100, 100)
rect.timeline().seek(3000).reverse()   // start backwards from the final state
```

## Orchestrating animations

Assign ONE timeline to several elements, then schedule with `absolute` times:

```js
const timeline = new SVG.Timeline()
const rect = draw.rect(100, 100).timeline(timeline)
const circle = draw.circle(100).timeline(timeline)

rect.animate(600, 0, 'absolute').move(300, 100)
circle.animate(400, 200, 'absolute').move(300, 250)
timeline.play()    // pause/seek/speed/reverse affects both runners
```

Relative sequence on a shared timeline:

```js
rect.animate(500).move(100, 0)
circle.animate(500, 0, 'with-last').move(100, 0)
rect.animate(300, 0, 'after').fill('#f06')
```
