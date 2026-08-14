# gh Command Reference

Condensed from the official manual (https://cli.github.com/manual). Every
top-level command group with its subcommands and the flags that matter most.
Run `gh <command> --help` for the authoritative, version-specific details.

## Repository (`gh repo`)

```
gh repo clone <repository> [<directory>] [-- <gitflags>...]
gh repo create [<name>] [flags]        # --public/--private/--internal, --clone, --source=., --push, --template=owner/repo, --add-readme
gh repo list [<owner>] [flags]         # --limit, --json, --jq
gh repo view [<repository>] [flags]    # --web, --branch, --json
gh repo fork [<repository>]            # --clone, --remote, --fork-name
gh repo sync [<destination>]           # --source, --force
gh repo edit [<repository>]            # --default-branch, --description, --enable-issues, --homepage, --add-topic, --remove-topic
gh repo rename [<new-name>]
gh repo delete [<repository>]          # --yes, --confirm
gh repo archive [<repository>] / gh repo unarchive [<repository>]
gh repo set-default [<repository>]
gh repo read-file <path>               # read a file's content without cloning; --commit
gh repo read-dir [<path>]              # list a directory without cloning
gh repo deploy-key add/list/delete     # --title, --allow-write, --key-file
gh repo autolink create/delete/list/view
gh repo gitignore list/view            # gh repo gitignore view <name> --output
gh repo license list/view              # gh repo license view <name>
```

Aliases: `gh repo new` = `gh repo create`.

## Pull requests (`gh pr`)

```
gh pr list [flags]                     # --state {open|closed|merged|all}, -a assignee, -A author, -l label, -B base, -H head, -S search, -d draft, --limit
gh pr create [flags]                   # -t title, -b body, -F body-file, --fill, --fill-first, --draft, -r reviewer, -a assignee, -l label, -B base, -H head, --template, --web, -e editor, --recover, --dry-run
gh pr view [<number>|url|branch]       # --web, --comments, --json, -c for current branch
gh pr checkout [<number>|url|branch]   # -b new-branch, --detach
gh pr diff [<number>|url|branch]       # --patch, --name-only, --color
gh pr checks [<number>|url|branch]     # --watch, --fail-fast, --required
gh pr merge [<number>|url|branch]      # --merge/-m, --squash/-s, --rebase/-r, --delete-branch, --auto, --admin, --subject, --body
gh pr close / reopen / ready [--undo]
gh pr comment [<number>] -b "…"        # --edit-last, --web
gh pr review [<number>]                # -a approve, -r request-changes, -c comment, -b body, --approve
gh pr edit [<number>]                  # --title, --body, --add-label, --remove-label, --add-reviewer
gh pr status                           # PRs relevant to you (authored, assigned, requested review)
gh pr update-branch                    # --rebase
gh pr revert [<number>]                # revert the PR's merge commit; -b body, --revert-id
gh pr lock {<number>|url} --reason <off_topic|resolved|spam|too_heated>  # gh pr unlock to undo
```

Aliases: `gh pr ls` = `gh pr list`, `gh pr new` = `gh pr create`.

## Issues (`gh issue`)

```
gh issue list [flags]                  # --state {open|closed|all}, -a assignee, -A author, -l label, -m milestone, -S search, --mention, --limit
gh issue create [flags]                # -t title, -b body, -F body-file, -a assignee (@me, @copilot), -l label, -m milestone, -p project, -T template, --type, --parent, --blocked-by, --blocking, --web, --recover
gh issue view [<number>|url]           # --web, --comments, --json
gh issue status                        # open issues assigned to you, created by you, mentioning you
gh issue close / reopen                # --reason, -c comment
gh issue comment [<number>] -b "…"     # --edit-last, --web
gh issue edit [<number>]               # --title, --body, --add-label, --remove-label, --add-assignee
gh issue transfer <number> <dest-repo>
gh issue delete <number>               # --yes
gh issue develop <number>              # check out a branch for the issue; --branch, -c, -b (create branch)
gh issue pin / unpin / lock / unlock
```

Aliases: `gh issue ls` = `gh issue list`, `gh issue new` = `gh issue create`.

## Releases (`gh release`)

```
gh release create <tag> [files...]     # --title, --notes, --notes-file, --generate-notes, --draft, --prerelease, --latest, --target
gh release list                        # --limit, --exclude-drafts, --exclude-pre-releases
gh release view <tag>                  # --web, --json
gh release download <tag>              # --pattern, --dir, --clobber; omit tag for latest
gh release upload <tag> <files...>     # --clobber
gh release delete <tag>                # --yes, --cleanup-tag
gh release delete-asset <tag> <name>
gh release edit <tag>                  # --title, --notes, --draft, --prerelease
gh release verify [<tag>]              # verify attestation for a release
gh release verify-asset [<tag>] <file>
```

## GitHub Actions

```
gh workflow list                       # --all, --limit
gh workflow run <workflow-id|name>     # -f key=value inputs, --ref <branch/tag>, --json (inputs via stdin)
gh workflow view <workflow-id|name|file>   # --web, -r ref, --yaml, --json
gh workflow enable <id|name> / gh workflow disable <id|name>
gh run list                            # -s status, -b branch, -w workflow, -u user, -c commit, -e event, --created, --limit, -a (include disabled)
gh run view [<run-id>]                 # --log, --log-failed, --job, --web, --json; no arg = latest run
gh run watch <run-id>                  # watch until completion, exit non-zero on failure
gh run rerun [<run-id>]                # --failed, --job
gh run cancel <run-id>
gh run delete <run-id>
gh run download [<run-id>]             # --dir, --name, --pattern, --artifact
gh cache list                          # -k key prefix, -r ref, --sort, --order, --limit
gh cache delete <cache-id|key|--all>   # --ref, --all
```

Aliases: `gh run ls` = `gh run list`, `gh workflow ls` = `gh workflow list`.

## Secrets & variables

```
gh secret set <name>                   # value from --body, stdin, or interactive prompt
gh secret set -f .env                  # bulk import from dotenv file/stdin
gh secret list / gh secret delete <name>
# scope flags (secret set): --env <environment>, --org <org>, --user, --app {actions|agents|codespaces|dependabot}
# org visibility: --visibility {all|private|selected}, --repos a,b,c, --no-repos-selected

gh variable set <name> <value>         # also reads from --body/stdin; same scope flags as secrets
gh variable get <name> / gh variable list / gh variable delete <name>
```

Secrets/variables scopes: repository (default) → environment (`--env`) →
organization (`--org`) → user/codespaces (`--user`).

## Search

```
gh search code <query>                 # --language, --extension, --filename, --match {file|path}, --repo, --owner, --size
gh search commits [<query>]            # --author, --committer, --author-date, --merge, --hash, --order, --sort
gh search issues [<query>]             # --state, -A author, --assignee, --label, --language, --created, --closed, --updated, --comments, --no-assignee, --no-label, --include-prs
gh search prs [<query>]                # --state, --base, --head, --draft, -A author, --assignee, --label, --review, --checks
gh search repos [<query>]              # --owner, --language, --topic, --stars, --forks, --archived, --visibility
```

All search commands support `--json`, `--jq`, `--template`, `--limit`,
`--order`, `--sort`, `--web`. Negative qualifiers need `--` before the query:
`gh search issues -- "query -label:bug"`.

## API (`gh api`) — see references/api.md

```
gh api <endpoint>                      # REST path or `graphql`
gh api -X PATCH /endpoint -F 'key=value'
gh api --paginate --slurp /endpoint
```

## Auth

```
gh auth login                          # --web, --clipboard, --with-token, --hostname, --git-protocol {ssh|https}, --scopes, --skip-ssh-key
gh auth logout                         # --hostname, --user
gh auth refresh                        # --scopes, --reset-scopes, --remove-scopes
gh auth status                         # --show-token, --active, --hostname, --json
gh auth switch                         # --hostname, --user
gh auth token                          # --hostname, --user
gh auth setup-git                      # configure git credential helper
```

## Codespaces (`gh codespace`, alias `gh cs`)

```
gh codespace list                      # --repo, --repo-owner
gh codespace create                    # --repo, --branch, --machine, --default, --devcontainer-path
gh codespace code                      # open in VS Code; --web, --insiders
gh codespace ssh                       # -- [<ssh flags>] [<command>]
gh codespace cp <sources...> <dest>    # copy files (scp-style, -e expand, -r recursive)
gh codespace jupyter                   # open in JupyterLab
gh codespace ports / ports forward / ports visibility
gh codespace view                      # --json, -c codespace
gh codespace edit                      # edit devcontainer.json
gh codespace rebuild                   # --full
gh codespace stop / delete / logs
```

## Projects (`gh project`)

```
gh project list                        # --owner, --format, --limit
gh project view <number>               # --owner, --format (json with --json)
gh project create                      # --owner, --title, --format
gh project close / delete / edit
gh project field-list <number>         # --owner, --limit
gh project field-create <number>       # --name, --data-type {TEXT|NUMBER|DATE|SINGLE_SELECT|ITERATION}
gh project field-delete
gh project item-list <number>          # --owner, --limit, --format
gh project item-create <number>        # --title
gh project item-add <number>           # --url (issue/PR url), --owner
gh project item-edit <number>          # --id, --field-id, --project-id, --value
gh project item-archive / item-delete
gh project link <number>               # --repo or --team
gh project unlink / copy / mark-template
```

Requires `project` scope: `gh auth refresh -s project`.

## Gists

```
gh gist create [files...]              # -d description, -p (public), --web, -f filename
gh gist list                           # --public, --secret, --limit
gh gist view {<id>|url}                # -f filename, --web, --raw
gh gist edit {<id>|url} [filename]     # --add, --remove
gh gist rename {<id>|url} <old> <new>
gh gist clone <gist> [<dir>] [-- <gitflags>]
gh gist delete {<id>|url}
```

## Misc commands

```
gh status                              # issues/PRs assigned to you; --active
gh browse [<number>|path|sha]          # --repo, --branch, --commit, --settings, --no-browser (print URL)
gh search repos/issues/prs/code/commits (see Search)
gh label create/list/edit/delete/clone
gh org list                            # --limit, --json
gh gpg-key add/list/delete
gh ssh-key add/list/delete
gh extension install/upgrade/list/remove/search/browse/exec/create
gh alias set/list/delete/import        # gh alias set <name> "gh pr create --draft"
gh config get/set/list/clear-cache     # keys: git_protocol, editor, prompt, pager, browser, telemetry…
gh completion -s <bash|zsh|fish|powershell>
gh copilot [flags] [args]              # Copilot CLI (if installed)
gh skill install/list/search/preview/publish/update   # agent skills (preview)
gh agent-task create/list/view         # agent tasks (preview)
gh attestation download/verify/trusted-root
gh ruleset list/view/check
gh discussion list/view/create/edit/comment
gh preview prompter                    # preview-only commands
```

## Universal flags

- `-R, --repo <[HOST/]OWNER/REPO>` — target a repo other than the current
  directory. Inherited by most repo-scoped commands.
- `--json <fields>` — machine-readable output; run `--json` with no fields to
  list available fields.
- `--jq <expr>` — filter JSON output (jq syntax, no jq binary needed).
- `--template <tmpl>` — Go-template formatting with gh helpers
  (`tablerow`, `pluck`, `join`, `timeago`, `color`, `hyperlink`, `truncate`,
  `contains`, `hasPrefix`, `hasSuffix`, `regexMatch`).
- `--web` — open the result in the browser instead of printing.
- `--limit N` — cap result count.
- `-h, --help` — per-command help with the full flag list.
