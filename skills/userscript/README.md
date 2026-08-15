# userscript

An [Agent Skill](https://agentskills.io) for Oh My Pi (omp), the AI coding harness — write, debug, and enhance userscripts (Tampermonkey / ScriptCat / Greasemonkey / Violentmonkey).

Give this skill to omp and it can build userscripts end to end: analyze the target page and framework, write spec-compliant metadata (`@match`/`@grant`/`@run-at`), hijack XHR/Fetch/WebSocket, integrate with Vue/React pages, load external libraries, and debug injection issues.

## What it covers

When activated, the skill covers the full userscript development workflow:

1. **Analyze the target** — identify the framework (Vue2 `__vue__`, Vue3 `__vue_app__`, React `__reactProps`/`__reactFiber`, webpack) and locate elements or network requests.
2. **Write metadata** — precise `@match`, correct `@run-at` (`document-start` for hijacking), and every `GM_*`/`unsafeWindow` declared in `@grant`.
3. **Choose the technique** — dynamic elements, XHR/Fetch/WebSocket hijacking, cross-origin `GM_xmlhttpRequest`, framework data injection, library loading.
4. **Defensive implementation** — guards against page-breaking errors, sandbox escape rules, and framework event propagation.
5. **Debug** — console proof, breakpoints, and network capture via the userscript manager.

## Structure

```
userscript/
├── SKILL.md                    # Core workflow: execution model, technique selection, gotchas
├── references/
│   ├── metadata.md             # Metadata fields: match/run-at/grant/require/connect
│   ├── gm-api.md               # GM API reference and cross-origin requests
│   ├── network-hijacking.md    # XHR/Fetch/WebSocket/addEventListener/videojs hijacking
│   ├── dom-techniques.md       # Dynamic elements, shadow DOM, iframe, SPA route watching
│   ├── framework-integration.md# Vue2/Vue3/React/webpack instances and data injection
│   ├── libraries.md            # Loading external libraries (@require vs injection)
│   └── debugging.md            # Debugging, breakpoints, network capture
└── evals/
    └── evals.json              # Test prompts and assertions
```

`SKILL.md` stays under 500 lines; the detail lives in `references/` and is loaded on demand.

## Installation

Clone the repository and link the folder into omp's user skills directory:

```bash
git clone https://github.com/Wildfire2282/my-omp-config.git ~/workspace/my-omp-config
ln -s ~/workspace/my-omp-config/skills ~/.omp/agent/skills
```

Per-project: link into `<project>/.omp/skills` instead. omp discovers skills as `<skills-root>/<name>/SKILL.md`; restart omp (or reload skills) to pick up new skills.

## Usage

Trigger manually — the skill is not auto-invoked:

```
/skill:userscript
```

## License

MIT — see [LICENSE](LICENSE).
