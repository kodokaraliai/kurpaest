#!/usr/bin/env bash
# Night-shift launcher. Circuit breakers live here — not in the model.
#
# Stops (and does not start another grok) when any of these is true:
#   - the drainable queue is already 0
#   - grok exits non-zero (including SIGINT)
#   - leftover count is not an integer (gh glitch)
#   - leftover did not shrink vs the previous grok (one crash-resume allowed, then halt)
#   - grok starts would exceed queue-at-start + 2
#   - wall clock exceeded NIGHT_SHIFT_MAX_HOURS (default 8)
#
# Usage (worker clone, inside tmux):
#   tmux has-session -t night-shift 2>/dev/null && tmux kill-session -t night-shift
#   tmux new -s night-shift ./scripts/night-shift.sh

set -u

ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"

PROMPT="$ROOT/docs/agents/night-shift.md"
REPO="kodokaraliai/kurpaest"
MAX_HOURS="${NIGHT_SHIFT_MAX_HOURS:-8}"
MAX_STALLS=1

if [ ! -f "$PROMPT" ]; then
  echo "night-shift: missing $PROMPT" >&2
  exit 1
fi
command -v grok >/dev/null || { echo "night-shift: grok not on PATH" >&2; exit 1; }
command -v gh >/dev/null || { echo "night-shift: gh not on PATH" >&2; exit 1; }
command -v node >/dev/null || { echo "night-shift: node not on PATH (Node 22 for frontend/)" >&2; exit 1; }
command -v npm >/dev/null || { echo "night-shift: npm not on PATH" >&2; exit 1; }

me=$(gh api user --jq .login) || {
  echo "night-shift: gh not authenticated" >&2
  exit 1
}

queue_count() {
  local out
  out=$(gh issue list --repo "$REPO" --state open --label ready-for-agent \
    --json assignees --jq \
    "[.[] | select((.assignees | length) == 0 or any(.assignees[]; .login == \"$me\"))] | length") || return 1
  printf '%s' "$out"
}

is_int() {
  [[ "${1:-}" =~ ^[0-9]+$ ]]
}

queue=$(queue_count) || { echo "night-shift: could not list issues" >&2; exit 1; }
if ! is_int "$queue"; then
  echo "night-shift: queue count not an integer: $queue" >&2
  exit 1
fi
if [ "$queue" -eq 0 ]; then
  echo "night-shift: nothing drainable; not starting grok"
  exit 0
fi

# One grok per remaining issue, plus two extra for a crash resume / context refill.
max_starts=$((queue + 2))
deadline=$((SECONDS + MAX_HOURS * 3600))
starts=0
stalls=0
prev=$queue

echo "night-shift: $queue drainable, cap ${max_starts} grok starts, ${MAX_HOURS}h wall clock, user $me"

while :; do
  if [ "$SECONDS" -ge "$deadline" ]; then
    echo "night-shift: time cap (${MAX_HOURS}h) reached; stopping" >&2
    exit 0
  fi
  if [ "$starts" -ge "$max_starts" ]; then
    echo "night-shift: start cap ($max_starts) reached; stopping" >&2
    exit 0
  fi

  remain=$((deadline - SECONDS))
  starts=$((starts + 1))
  echo "night-shift: grok start $starts/$max_starts (${remain}s left, queue $prev)"

  grok_status=0
  if command -v timeout >/dev/null 2>&1; then
    timeout "$remain" grok -p "$(cat "$PROMPT")" --always-approve --cwd "$ROOT" || grok_status=$?
  else
    grok -p "$(cat "$PROMPT")" --always-approve --cwd "$ROOT" || grok_status=$?
  fi

  if [ "$grok_status" -ne 0 ]; then
    echo "night-shift: grok exited $grok_status; not retrying" >&2
    exit "$grok_status"
  fi

  leftover=$(queue_count) || { echo "night-shift: could not list issues after grok" >&2; exit 1; }
  if ! is_int "$leftover"; then
    echo "night-shift: leftover not an integer: $leftover" >&2
    exit 1
  fi
  echo "night-shift: leftover $leftover (was $prev)"

  if [ "$leftover" -eq 0 ]; then
    echo "night-shift: queue empty"
    exit 0
  fi
  if [ "$leftover" -lt "$prev" ]; then
    stalls=0
    prev=$leftover
    continue
  fi

  stalls=$((stalls + 1))
  echo "night-shift: queue did not shrink (stall $stalls/$((MAX_STALLS + 1)))" >&2
  if [ "$stalls" -gt "$MAX_STALLS" ]; then
    echo "night-shift: no progress; stopping so this cannot burn tokens" >&2
    exit 0
  fi
  prev=$leftover
done
