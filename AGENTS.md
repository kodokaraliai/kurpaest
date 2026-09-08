# Agent instructions

## Version control

Work on a branch off `main`. After every implementation, push the branch and **open a pull request**. Do not leave finished changes only in the local working tree.

Default merge is **squash and merge** (`gh pr merge --squash`). Do not merge-commit or rebase-merge unless asked. Do not pass `--subject`; GitHub appends `(#N)` on its own.

## Tooling

`uv` for the env and lockfile. After Python edits: `uv run ruff check --fix` then `uv run ruff format`. Package lives in `src/kurpaest/`. HTTP is a seam (`src/kurpaest/app.py`): cheapest-item, dietary, and geo logic must not import FastAPI.

Frontend is React + Vite in `frontend/` (Node 22). After frontend edits: `npm run build`. Must be served (`npm run dev` or `npm run build` + `npm run preview`). `file://` is not a valid run mode.

Money is integer `price_cents`. Dietary tags are explicit; unknown does not match a filter.

## Agent skills

### Issue tracker

GitHub Issues on `kodokaraliai/kurpaest` (`gh`). See `docs/agents/issue-tracker.md`.

### Triage labels

Default roles: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Product and work split: `docs/architecture.md`. See `docs/agents/domain.md`. Do not implement WP-3–WP-6 unless the issue you are on says so.

### Night shift

Unattended drain of `ready-for-agent` issues on a worker clone: `docs/agents/night-shift.md`.
