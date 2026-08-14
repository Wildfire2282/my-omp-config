# Environment, Config, Exit Codes

## Authentication environment variables

Precedence per host type:

| Variable | Used when | Precedence |
|---|---|---|
| `GH_TOKEN`, `GITHUB_TOKEN` | targets github.com or `*.ghe.com` | first-listed wins |
| `GH_ENTERPRISE_TOKEN`, `GITHUB_ENTERPRISE_TOKEN` | GitHub Enterprise Server host | first-listed wins |

- Env tokens avoid prompts and take precedence over stored credentials.
- Fine-grained PATs: prefer `GH_TOKEN` over `gh auth login --with-token`
  (scoped tokens can behave confusingly when stored as the default credential).

## Other environment variables

- `GH_HOST` — default GitHub hostname when none is inferable.
- `GH_REPO` — default repository in `[HOST/]OWNER/REPO` format (same as
  `-R/--repo` for every command that accepts it).
- `GH_EDITOR`, `GIT_EDITOR`, `VISUAL`, `EDITOR` — editor for authoring text
  (first-listed wins).
- `GH_BROWSER`, `BROWSER` — browser for `--web` (first-listed wins).
- `GH_DEBUG` — verbose stderr; `api` additionally logs HTTP traffic.
- `GH_PAGER`, `PAGER` — pager program (e.g. `less`).
- `NO_COLOR` / `CLICOLOR=0` — disable ANSI colors; `CLICOLOR_FORCE` — force.
- `GH_FORCE_TTY` — force terminal-style output even when piped; a number
  sets the column count, a percentage scales with viewport width.
- `GH_PROMPT_DISABLED` — disable interactive prompting (headless runs).
- `GH_NO_UPDATE_NOTIFIER` — suppress the update check notice.
- `GH_CONFIG_DIR` — config dir (default `$XDG_CONFIG_HOME/gh`,
  `$AppData/GitHub CLI` on Windows, else `$HOME/.config/gh`).
- `GH_TELEMETRY=log` — print telemetry to stderr; `false`/`0` disables it
  (overrides `DO_NOT_TRACK`).
- `GH_SPINNER_DISABLED` — replace spinner with text progress.

## Config keys (`gh config get/set`)

| Key | Values | Default |
|---|---|---|
| `git_protocol` | `https` \| `ssh` | `https` |
| `editor` | program name | — |
| `prompt` | `enabled` \| `disabled` | `enabled` |
| `prefer_editor_prompt` | `enabled` \| `disabled` | `disabled` |
| `pager` | program | — |
| `browser` | program | — |
| `http_unix_socket` | socket path | — |
| `color_labels` | `enabled` \| `disabled` | `disabled` |
| `telemetry` | `enabled` \| `disabled` \| `log` | `enabled` |

`gh config set <key> <value>` writes to the user config; `--host` scopes to
a host. `gh config clear-cache` clears the CLI cache.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | success |
| 1 | failure (any reason) |
| 2 | running but cancelled |
| 4 | authentication required |

Note: a specific command may define additional codes — check its docs when
scripting on exit codes.

## Telemetry

gh collects usage telemetry by default. Opt out with
`gh config set telemetry disabled` or `GH_TELEMETRY=false`. See
`gh help telemetry` for what is collected.
