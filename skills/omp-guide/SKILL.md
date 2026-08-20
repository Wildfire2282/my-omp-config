---
name: omp-guide
description: >-
  Tiny hint for Oh My Pi (omp). Use when operating on omp itself to remind
  the agent that built-in docs are available via omp://.
license: MIT
disable-model-invocation: false
metadata:
  author: Wildfire2282
  author-url: https://github.com/Wildfire2282
  version: "1.0"
---

# omp-guide

When the user mentions `omp`, use `omp://`.

- `read("omp://")` lists all built-in docs.
- `read("omp://<file>")` reads one (e.g. `skills.md`, `extensions.md`).
