# gh api — REST & GraphQL Deep Dive

`gh api <endpoint>` makes an authenticated request to the GitHub API and
prints the response. This is the recommended way to call the API: auth,
hostname, and repo placeholders are handled for you.

## Endpoint argument

- A GitHub REST v3 path: `gh api repos/{owner}/{repo}/issues`
- Or the literal `graphql` for the GraphQL v4 API.
- Placeholders `{owner}`, `{repo}`, `{branch}` are filled from the current
  repo (or `GH_REPO` env var). Quote them in PowerShell (curly braces are
  special there).
- For API URLs that live under `/repos/{owner}/{repo}/...`, note that REST
  paths use the endpoint prefix without the `https://api.github.com` base.

## HTTP method

- Default: `GET` — unless request parameters were added, in which case it
  auto-switches to `POST`.
- Override explicitly: `-X/--method <GET|POST|PATCH|PUT|DELETE>`.
- Add a GET query string instead: `gh api -X GET search/issues -f q='…'`.

## Request parameters

Two flag families:

| Flag | Behavior |
|---|---|
| `-f, --raw-field key=value` | Raw **string** parameter. Always a string. |
| `-F, --field key=value` | **Typed** parameter: `true`/`false`/`null`/integers become JSON types; `{owner}`/`{repo}`/`{branch}` placeholders are populated; `@file` or `@-` reads the value from a file/stdin. |

- Nested object: `-F 'files[myfile.txt][content]=@myfile.txt'`
- Arrays: repeat `-F 'tags[]=x' -F 'tags[]=y'`; empty array: `-F 'tags[]'`
- Request body from file: `--input file.json` (or `-` for stdin). When a body
  is passed this way, field flags go into the query string instead.
- Headers: `-H 'Accept: application/vnd.github.v3.raw+json'`
- Previews: `-p/--preview <name>` (omit the `-preview` suffix; comma-separate
  multiple).

## Pagination

- `--paginate` — keep requesting pages until exhausted (follows Link
  headers for REST).
- `--slurp` — wrap all pages (arrays/objects) into one outer JSON array.
  `--slurp` only makes sense together with `--paginate`.
- GraphQL pagination requires the query to accept `$endCursor: String` and
  fetch `pageInfo { hasNextPage endCursor }` from the collection:

```graphql
query($endCursor: String) {
  repository(owner: "cli", name: "cli") {
    issues(first: 100, after: $endCursor) {
      nodes { number title }
      pageInfo { hasNextPage endCursor }
    }
  }
}
```

## Output formatting

- `-q/--jq '<expr>'` — filter with jq syntax (built in; no jq binary needed).
  `gh api repos/cli/cli/issues --jq '.[].title'`
- `-t/--template '<go-template>'` — Go template formatting with gh helper
  functions (`pluck`, `join`, `color`, `tablerow`…): see
  `gh help formatting`.
- `--silent` — suppress the response body (useful with `--method POST`).
- `-i/--include` — print HTTP status line and headers too.
- `--verbose` — full HTTP request/response dump (debugging).
- `--cache <duration>` — cache the response (e.g. `3600s`, `60m`, `1h`).
- `--hostname <host>` — target a specific GitHub host (default github.com).

## GraphQL notes

- Every field other than `query` and `operationName` is treated as a GraphQL
  variable: `gh api graphql -f query='query($n:Int!){viewer{login}}' -F n=1`.
- For `--paginate`, use `$endCursor` as shown above; each page is a separate
  JSON object, so pipe through jq or use `--slurp`.

## Recipes

```bash
# List release titles, newest first
gh api repos/{owner}/{repo}/releases --jq '.[] | .tag_name + " " + .name'

# Post an issue comment
gh api repos/{owner}/{repo}/issues/123/comments -f body='Hi from CLI'

# Update a file's content (needs base64 content)
gh api -X PUT repos/{owner}/{repo}/contents/path/file.md \
  -f message='Update docs' -f content="$(base64 -w0 file.md)" \
  -f sha=<current-blob-sha>

# Create a repo
gh api user/repos -f name=my-repo -F private=true

# Paginate every open issue number across all pages
gh api --paginate repos/{owner}/{repo}/issues --jq '.[].number'

# Get authenticated user's login
gh api user --jq .login
```
