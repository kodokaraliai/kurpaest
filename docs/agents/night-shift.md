# Night shift

Unattended drain of **every** `ready-for-agent` issue. There is no human on the other side of this chat: **finish or bounce** each issue, squash-merge finished work, then take the next. Never wait for a reply. Bounce is not the end of the run.

Spend tokens only on scoping, implementing, verifying, merging, or bouncing. If an issue will not finish in this process, bounce it. Do not retry it. Do not start another `grok`. Do not run `scripts/night-shift.sh`.

## Launch (operator)

On a **worker clone** — a spare VPS or a separate user. Not production hosting, not the live `kurpaest.lt` database, not production `.env`.

`tmux new -s night-shift` fails if that session already exists. Kill it first, then start:

```bash
tmux has-session -t night-shift 2>/dev/null && tmux kill-session -t night-shift

cd ~/kurpaest
git pull --ff-only
uv sync --group dev
# Node 22 + npm: Vite frontend in `frontend/`. `npm run build` after frontend edits.
# grok: XAI_API_KEY or `grok login --device-auth`
# gh:  `gh auth status` must see kodokaraliai/kurpaest
# local PostGIS (for persistence tests): docker compose up -d && cp -n .env.example .env
tmux new -s night-shift ./scripts/night-shift.sh
# detach: Ctrl-b d
```

Look: `tmux ls` then `tmux attach -t night-shift` (detach: `Ctrl-b d`). Kill only: `tmux kill-session -t night-shift`.

The script — not this prompt — restarts Grok. It **does not start Grok** if the drainable queue is empty. It **stops for good** when Grok exits non-zero, leftover is not a number, leftover does not shrink twice in a row, start count exceeds queue-at-start + 2, or `NIGHT_SHIFT_MAX_HOURS` (default 8) elapses. That is the token fuse.

Needs: `grok`, `gh`, `uv`, `node` (22, same as the Vite app), `npm`, `git`, `tmux` (or systemd) so SSH logout does not kill the run.

If the script prints `node not on PATH`, install Node 22 on the worker (Debian/Ubuntu):

```bash
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs
node -v   # v22.x
npm -v
```

## You

You are the night-shift agent on this worker clone. Follow `AGENTS.md`. Tracker verbs: `docs/agents/issue-tracker.md`. Claim with `gh` (or the github-cli skill's `with-gh` wrapper if `gh` is missing). Product and work split: `docs/architecture.md`.

This run is sequential. One working tree. One issue at a time. Keep going until **Select** finds nothing.

Squash-merge your own finished PRs (`gh pr merge --squash --delete-branch`; no `--subject`). Do not wait for CI. One merge command per PR; if it fails, bounce `ready-for-human`.

### One attempt

Each issue number is touched **at most once** in this process: either it merges or it bounces. Record the numbers you already claimed or bounced. **Select** never returns one of those again.

If implement cannot finish (tests fail, brief holes show up mid-work, merge fails, you would have to guess): bounce, do not start over on the same issue.

### Done for the whole run

No open `ready-for-agent` issue is unassigned or assigned to you, or every remaining one is in your already-touched set. Print the **Run report** as the final message (stdout is the log).

Auth failure, a dirty tree you cannot clean without discarding someone else's work, or `gh`/`git` unusable: before you exit, bounce (or unassign) every issue you claimed that is not merged, then report. Do not leave a claimed `ready-for-agent` issue sitting: that is how a launcher would see leftover and spend another process. Draft + stay assigned only when this process is actually being killed.

"I would have to guess" is a **bounce**, then **Reset** and **Select** again.

---

## Drain

Repeat until the run is done.

### 1. Prep

On `main`, working tree clean, `git pull --ff-only`.

**Done when:** `git status` is clean and `HEAD` is `main`.

### 2. Select

Oldest first:

```bash
gh issue list --repo kodokaraliai/kurpaest --state open --label ready-for-agent \
  --json number,title,assignees,url
```

Take the first issue that is **unassigned** or **assigned to you**, is **not** in this process's already-touched set, and is not assigned to someone else.

If that issue already has an open PR that references `#<number>`:

```bash
gh pr list --repo kodokaraliai/kurpaest --state open --search "<number>"
```

- PR is **yours** and not a draft: go to **Merge**, then **Reset**.
- PR is **yours** and a draft: this is your one attempt — resume **Implement** on that branch. If you still cannot finish, bounce.
- PR is **someone else's**: skip (do not claim).

If none remain, the queue is empty.

**Done when:** you have a number to work, or the queue is empty.

### 3. Claim

If you are not already the assignee, assign yourself. First write to that issue besides this claim:

```bash
gh issue edit <n> --add-assignee @me
```

Add `<n>` to the already-touched set.

**Done when:** `gh issue view <n> --json assignees` includes you.

### 4. Scope

Read the issue (`gh issue view <n> --comments`), including the agent brief. Then only what that issue needs: `docs/architecture.md`, `docs/agents/`, `README.md` for how tests, API, and Vite start.

Choose one path:

| Path | When |
| --- | --- |
| **Implement** | The agent brief is complete and you can finish it on this clone. |
| **Bounce `needs-info`** | A specific fact, copy, asset, or credential is missing. |
| **Bounce `ready-for-human`** | A judgement call, domain DNS, production hosting, scraping a live menu, or a thin brief on money/dietary-tag inference. |

HTTP is a seam (`src/kurpaest/app.py`). Query/filter logic must not import FastAPI. Money is integer `price_cents`. Dietary tags are explicit; unknown does not match. Do not infer tags from dish names. Vite must be served — do not treat `file://` as a run mode.

**Done when:** you have chosen implement or bounce.

### 5. Bounce

Comment, then relabel, then unassign. Comment shape:

```markdown
> *Night shift (unattended agent).*

## Blocked

**Need:** the exact question, placeholder, or credential
**Tried:** what you already read or ran
```

```bash
gh issue comment <n> --body "..."
gh issue edit <n> --remove-label ready-for-agent --add-label needs-info   # or ready-for-human
gh issue edit <n> --remove-assignee @me
```

**Done when:** the issue is not `ready-for-agent` and not assigned to you. Go to **Reset**.

### 6. Implement

Branch off `main` (`issue-<n>-<slug>`), or check out your existing draft-PR branch. Do the work. After Python edits: `uv run ruff check --fix` then `uv run ruff format`. After `frontend/` edits: `npm run build` in `frontend/`.

Verify on this clone:

```bash
uv run pytest
uv run ruff check
uv run ruff format --check
```

When the change is HTTP, also hit `uv run kurpaest` (or the issue's stated entry) with a real request. When the change is the Vite UI, `npm run build` in `frontend/` must succeed; do not stall for a headed browser.

Push the branch and open a pull request (or mark the draft ready). PR body includes `Closes #<n>`. The PR is finished when the brief's acceptance criteria hold on this clone.

If this process is being killed mid-issue: push, open or keep a **draft** PR, comment the draft URL on the issue, stay assigned. Only a later launcher start (and only one stall) may resume it.

**Done when:** a non-draft PR exists for `#<n>`. Go to **Merge**.

### 7. Merge

```bash
gh pr merge <pr> --squash --delete-branch
```

No `--subject`. Do not wait for checks. If merge fails, bounce `ready-for-human`, unassign, **Reset**. Do not run merge again.

After a successful merge: confirm the issue closed (GitHub closes it from `Closes #<n>`; if not, `gh issue close <n>`).

**Done when:** the PR is merged and `#<n>` is closed.

### 8. Reset

```bash
git checkout main
git pull --ff-only
```

Working tree clean. Then **Select**.

If the tree is dirty and you cannot make it clean without discarding someone else's work: bounce anything you claimed that is not merged, then **stop the run**.

---

## Run report

Final message, nothing after it:

```markdown
## Night shift report

**Merged:** #… (`issue title`) → PR #…
**Bounced needs-info:** #… (one-line reason)
**Bounced ready-for-human:** #… (one-line reason)
**Skipped (assigned to someone else or their open PR):** #…
**Left in queue:** #…
**Stopped because:** queue empty | <reason>
```
