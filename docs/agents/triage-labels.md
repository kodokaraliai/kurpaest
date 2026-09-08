# Triage Labels

The skills speak in terms of five canonical triage roles. This file maps those roles to the actual label strings used in this repo's issue tracker.

| Label in mattpocock/skills | Label in our tracker | Meaning                                  |
| -------------------------- | -------------------- | ---------------------------------------- |
| `needs-triage`             | `needs-triage`       | Maintainer needs to evaluate this issue  |
| `needs-info`               | `needs-info`         | Waiting on reporter for more information |
| `ready-for-agent`          | `ready-for-agent`    | Fully specified, ready for an AFK agent  |
| `ready-for-human`          | `ready-for-human`    | Requires human implementation            |
| `wontfix`                  | `wontfix`            | Will not be actioned                     |

When a skill mentions a role (e.g. "apply the AFK-ready triage label"), use the corresponding label string from this table.

Night shift (`docs/agents/night-shift.md`) drains only open issues labelled `ready-for-agent` that are unassigned or assigned to the worker.

## Category roles

Work-package issues also carry area labels already in use:

| Label         | Meaning                    |
| ------------- | -------------------------- |
| `work-package` | Architecture WP-n unit    |
| `backend`     | Python API / domain       |
| `frontend`    | React + Vite              |
| `data`        | Persistence, seed, contribution |
