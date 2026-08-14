---
name: github-cli
description: >-
  Operate GitHub from the command line with the official GitHub CLI (`gh`):
  authenticate, create and manage issues and pull requests, work with
  repositories (create, clone, fork, delete), releases, gists, and labels;
  run and inspect GitHub Actions workflows and runs; manage secrets and
  variables; search code, issues, PRs, commits, and repos; query the REST and
  GraphQL APIs via `gh api`; manage codespaces and projects; and configure
  aliases, extensions, and settings. Use when the user asks to do anything
  with GitHub through a terminal or shell — "create a PR", "open an issue",
  "list my repos", "trigger a workflow", "set a secret", "search GitHub code",
  "call the GitHub API", "clone a repo", "check workflow run status", "look
  at a codespace", or any task where `gh` is the right tool — including
  scripting GitHub automation in CI, shell, or agent workflows. The manual is
  bundled at references/ (full command reference in references/commands.md).
license: MIT
disable-model-invocation: true
compatibility: Requires the GitHub CLI (`gh`) installed and authenticated. Linux/macOS/Windows; works with GitHub.com and GitHub Enterprise Server.
metadata:
  author: Wildfire2282
  author-url: https://github.com/Wildfire2282
  version: "1.0"
---

# GitHub CLI (gh)

`gh` is GitHub's official CLI. It wraps the REST v3 and GraphQL v4 APIs, and
can authenticate `git` itself. Run `gh --help` for the command tree; every
command is documented in `references/commands.md`.

## When to use this skill

Reach for `gh` whenever the task is GitHub-shaped and the user is working in
a terminal, a script, a CI pipeline, or an agent environment. If the request
is "use the GitHub API", prefer `gh api` over raw `curl` — it handles auth,
`{owner}/{repo}` placeholder substitution, pagination, and jq/template output
for free.

## Authentication (do this first)

- Interactive setup: `gh auth login` (web or token flow). Stores credentials
  in the system keyring; falls back to a plaintext file.
- Token from stdin (scripts/CI): `echo $TOKEN | gh auth login --with-token`
  — the token needs at least `repo`, `read:org`, and `gist` scopes.
- Headless/automation: set `GH_TOKEN` (or `GITHUB_TOKEN`) env var. This takes
  precedence over stored credentials and avoids prompts entirely.
- GitHub Actions: `env: GH_TOKEN: ${{ github.token }}`.
- Multi-account: `gh auth switch`; check state with `gh auth status`.
- Enterprise hosts: `gh auth login --hostname <host>`; or set
  `GH_ENTERPRISE_TOKEN` for scripts.
- Git integration: `gh auth setup-git` configures git to use gh's
  credentials for https pushes/clones.
- Extra scopes (e.g. projects): `gh auth refresh -s project`.

## Core command map (fast path)

| Task | Command |
|---|---|
| View/open a repo | `gh repo view [owner/repo]` (add `--web`) |
| Create a repo | `gh repo create name --public --clone` |
| Clone | `gh repo clone owner/repo` |
| Fork / sync | `gh repo fork` / `gh repo sync` |
| List repos | `gh repo list [owner]` |
| Delete/rename | `gh repo delete owner/repo` / `gh repo rename` |
| List issues | `gh issue list [--state open/closed/all]` |
| Create issue | `gh issue create -t "Title" -b "Body"` (add `--label`) |
| View/comment/close | `gh issue view 12` / `gh issue comment 12 -b "…"` / `gh issue close 12` |
| List PRs | `gh pr list` (add `--state`, `--author @me`) |
| Create PR | `gh pr create --fill` or `-t/-b` (add `--draft`, `--reviewer`) |
| Check out a PR | `gh pr checkout 12` |
| View PR | `gh pr view 12` (add `--web`, `--comments`) |
| PR checks | `gh pr checks 12` |
| Merge PR | `gh pr merge 12 --squash --delete-branch` |
| Releases | `gh release create v1.0.0 --generate-notes` / `gh release list` |
| Workflows | `gh workflow list` / `gh workflow run triage.yml -f name=x` |
| Runs | `gh run list` / `gh run view` / `gh run watch <id>` |
| Secrets | `gh secret set NAME` / `gh secret list` / `gh secret delete NAME` |
| Variables | `gh variable set NAME` / `gh variable list` / `gh variable get NAME` |
| Search | `gh search code/issues/prs/repos/commits "<query>"` |
| API | `gh api repos/{owner}/{repo}` / `gh api graphql -f query='…'` |
| Codespaces | `gh codespace list` / `gh codespace create` / `gh codespace ssh` |
| Projects | `gh project list` / `gh project view <number>` |
| Gists | `gh gist create file.txt` / `gh gist list` / `gh gist view` |
| Browse | `gh browse` (open current repo in browser) |
| Status | `gh status` (issues/PRs assigned to you) |
| Alias | `gh alias set prd "pr create --draft"` |
| Extensions | `gh extension install owner/repo` (repos named `gh-*`) |

## Common patterns

### JSON output & filtering (scripting)

Most list/view commands accept `--json <fields>` plus `--jq <expr>` or
`--template <template>`:

```bash
gh pr list --json number,title,author --jq '.[] | "\(.number) \(.title)"'
gh issue list --json number,title,labels --jq 'map(select((.labels | length) > 0))'
```

- Run `gh pr list --json` (no field list) to print the available field names.
- `--jq` uses jq syntax — no jq binary needed. `--template` uses Go templates
  plus helpers: `tablerow`, `pluck`, `join`, `timeago`, `color`, `autocolor`,
  `hyperlink`, `truncate`, `contains`, `hasPrefix`, `hasSuffix`, `regexMatch`.
- In scripts, prefer `--json ... --jq ...` over text parsing — output is
  stable and locale-independent.

### Select the repository explicitly

Use `-R/--repo [HOST/]OWNER/REPO` on any repo-scoped command to target a repo
other than the current directory, e.g. `gh issue list -R cli/cli`.
`GH_REPO=OWNER/REPO` env var does the same for non-interactive use.

### Non-interactive execution

- Provide all required flags (`-t/--title`, `-b/--body`, etc.) so gh never
  prompts.
- Set `GH_PROMPT_DISABLED=1` to force prompt-less behavior in scripts.
- `gh pr create --recover` restores a draft from a previous interrupted run.

### gh api — REST and GraphQL

```bash
# REST GET (placeholders filled from current repo)
gh api repos/{owner}/{repo}/releases
# POST with parameters (method auto-switches to POST when params are given)
gh api repos/{owner}/{repo}/issues/123/comments -f body='Hi from CLI'
# Typed fields: -F converts true/false/null/numbers, @file reads a file
gh api repos/{owner}/{repo}/pulls -F 'title=Hello' -F 'body=@desc.md'
# GraphQL
gh api graphql -f query='query($n:Int!){ viewer { login } }' -F n=1
# Paginate through all pages
gh api --paginate repos/{owner}/{repo}/issues --jq '.[].number'
```

- `-f key=value` = raw string param; `-F key=value` = typed (JSON types,
  `{owner}/{repo}/{branch}` placeholders, `@file` or `@-` stdin).
- Nested/array params: `-F 'files[a][content]=@a.txt'` or `-F 'tags[]=x'`.
- `--paginate` walks Link headers; add `--slurp` to wrap pages in one array.
- For GraphQL pagination, the query must accept `$endCursor: String` and fetch
  `pageInfo { hasNextPage endCursor }`.

## Gotchas (things that bite)

- **Prompts hang automation.** Without flags, `gh issue create`/`pr create`
  prompt interactively. Always pass `-t`/`-b` (or `--fill`) in scripts; also
  set `GH_PROMPT_DISABLED`.
- **`gh pr create` pushes first.** If the branch isn't pushed, gh offers to
  push or fork. Use `--head` to control the head branch explicitly; a fork
  created this way contains only the upstream default branch.
- **`--fill` vs explicit flags.** `--title`/`--body` given alongside `--fill`
  override the autofilled values.
- **`gh pr merge` needs a strategy.** Choose `--merge`, `--squash`, or
  `--rebase`; add `--delete-branch` to clean up, `--auto` for auto-merge.
- **Exit codes.** 0 success, 1 failure, 2 cancelled, 4 auth required —
  script against these. Some commands may define more; check the manual.
- **`gh search` exclusions.** `-label:bug` must be protected from flag
  parsing: `gh search issues -- "query -label:bug"` (note the `--`).
- **Secrets/variables scoping.** Default is repository level. Use `--env` for
  a deployment environment, `--org` for organization (then `--visibility`
  and/or `--repos`), `--user` for codespaces user secrets.
- **Secret values never echo.** `gh secret set NAME` reads stdin if no
  `--body`; don't put the value on the command line in CI logs.
- **`gh api` on PowerShell** needs quoting around `{owner}` — curly braces
  are special.
- **Enterprise/auth ambiguity.** Commands can fail with exit 4 when no token
  is found; verify with `gh auth status` before debugging further.
- **`GH_TOKEN` vs stored creds.** Env vars win over stored credentials; a
  stale `GH_TOKEN` in a shell can make commands act as a different account.

## References (load on demand)

- `references/commands.md` — full command reference (every `gh` command and
  subcommand with flags, from the official manual)
- `references/api.md` — `gh api` REST/GraphQL deep dive: field types,
  pagination, jq/template output recipes
- `references/environment.md` — environment variables, config settings,
  exit codes, telemetry
