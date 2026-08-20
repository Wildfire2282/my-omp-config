# Install reference

Skills live in the collection `~/workspace/my-omp-config/skills/` and are exposed via a symlink, not a copy (same pattern as `extensions` and `rules`).

```bash
ln -s ~/workspace/my-omp-config/skills ~/.omp/agent/skills      # user-wide
ln -s ~/workspace/my-omp-config/skills <project>/.omp/skills    # per-project
```

- Create every new skill at its permanent home — `~/workspace/my-omp-config/skills/<name>/` (always via `~`, never a hardcoded username).
- Confirm link: `readlink ~/.omp/agent/skills` must resolve to `~/workspace/my-omp-config/skills` (user-wide) or `<project>/.omp/skills` (per-project).
  - Missing or pointing elsewhere → create it as above. Never copy the skill into the skills root — the link exposes the whole folder.
  - On this machine the link target is relative (`../../workspace/my-omp-config/skills` from `~/.omp/agent`) so it survives username changes — keep it relative; don't replace with absolute `/home/...`.
- Verify: `test -f ~/.omp/agent/skills/<name>/SKILL.md` must succeed. If it fails, wrong folder or broken link — fix before delivering.
- After files exist, restart omp (or reload skills) to register the new directory. omp discovers skills as `<skills-root>/<name>/SKILL.md`.
