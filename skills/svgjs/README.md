# svgjs

An [Agent Skill](https://agentskills.io) that gives AI assistants expert-level
knowledge of [SVG.js](https://svgjs.dev/) v3 (`@svgdotjs/svg.js`), the
dependency-free library that wraps the SVG DOM in a chainable, object-oriented
API.

A progressive-disclosure skill: a compact `SKILL.md` with quick-start recipes,
core concepts, and gotchas, plus focused reference files loaded on demand.

## What it covers

- **Quick start** — browser CDN, ES modules, Node.js with `svgdom`
- **Core concepts** — the `SVG()` function, chainable setters, container constructors, `animate()`/Runner, per-element Timelines, getter/setter duality
- **Gotchas** — `attr()` positioning limits, groups vs `nested()`, absolute vs relative transforms, path animation constraints, masks vs clip paths, animation scheduling, controller runners, events, `transform()` decomposition, Node.js registration order
- **Decision order** — environment → canvas → container → elements → references → reuse paints/geometry → animation → export
- **References (loaded on demand)** — elements, manipulating, animating, events, classes, importing/exporting, extending, Node.js

## Structure

```
svgjs/
├── SKILL.md            # metadata + core instructions (<100 lines)
└── references/         # focused topic files, loaded on demand
    ├── elements.md / manipulating.md / animating.md / events.md
    ├── classes.md / importing-exporting.md / extending.md
    └── nodejs.md
```

## Installation

Clone the repository and link the folder into omp's user skills directory:

```bash
git clone https://github.com/Wildfire2282/my-skills.git
mkdir -p ~/.omp/agent/skills
ln -s "$(pwd)/my-skills/svgjs" ~/.omp/agent/skills/svgjs
```

Or copy the folder into `~/.omp/agent/skills/` (user-wide) or `<project>/.omp/skills/` (per-project). omp discovers skills as `<skills-root>/<name>/SKILL.md`; restart omp (or reload skills) to pick them up.

## Usage

Trigger manually — the skill is not auto-invoked:

```
/skill:svgjs
```

## Source & verification

- API details distilled from the official SVG.js v3 documentation
- `SKILL.md` instructs the agent to verify the deliverable in a browser or Node, because SVG.js silently ignores invalid attribute targets rather than throwing

## License

MIT — see [LICENSE](LICENSE).
