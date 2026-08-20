---
name: install-skill
description: >-
  Install a skill by symlinking the skills collection into omp and verifying discoverability. Use when the user asks to install, link or make a skill available in omp.
license: MIT
disable-model-invocation: true
metadata:
  author: Wildfire2282
  author-url: https://github.com/Wildfire2282
  version: "1.0"
---

# Install Skill

Make a skill available in omp. Skills live in the collection `~/workspace/my-omp-config/skills/` and are exposed via a symlink — not a copy (same pattern as `extensions` and `rules`).

## Workflow

### 1. Pre-check

- Target directory exists: `~/workspace/my-omp-config/skills/<name>/SKILL.md` must exist. If not, abort and tell the user to run `/skill:create-skill` first.
- If the skill was recently reviewed, check the latest `review-skill` report — if `MUST FIX` remains, warn and ask for explicit confirmation to proceed anyway.

### 2. Ensure collection link

The collection folder is the install point; there is no per-skill install step.

- User-wide: `readlink ~/.omp/agent/skills` must resolve to `~/workspace/my-omp-config/skills` (on this machine relative: `../../workspace/my-omp-config/skills` from `~/.omp/agent`).
  - Missing or wrong target → create it: `ln -s ~/workspace/my-omp-config/skills ~/.omp/agent/skills`. Keep it relative; do not replace with absolute `/home/...` target.
  - Never copy the skill into the skills root — the link exposes the whole folder.
- Per-project: link into `<project>/.omp/skills` instead when user asks for project scope.

Always use `~`, never a hardcoded username.

### 3. Verify

- `test -f ~/.omp/agent/skills/<name>/SKILL.md` (or `<project>/.omp/skills/<name>/SKILL.md` for per-project) must succeed. If it fails, the skill is in the wrong folder or the link is broken — fix before finishing.
- Report the resolved link target and the verified path.

### 4. Activate

Tell the user to restart omp (or reload skills) to pick up the new directory. No further file changes.

## Gate — stop here

This skill ends here. Do not invoke `create-skill` or `review-skill`. Report link target and verification evidence and stop.

## References — load on demand

- `references/install.md` — link semantics, relative target rationale, per-project vs user-wide
