# Beads Workflow Guide

## What Is Beads?

Beads is a task coordination system backed by a Dolt database running on olympus-bus (10.220.1.64). It provides atomic task claiming, status tracking, and integration with GitHub Issues.

**Why beads instead of polling GitHub directly?**
- **Atomic claims**: No race conditions when two agents try to claim the same issue
- **Local speed**: Querying a local Dolt DB is faster than GitHub API calls
- **Offline resilience**: Agents can work even if GitHub is temporarily unreachable
- **Rich querying**: Filter, sort, and search work items with SQL-like capabilities

## How GitHub Issues Sync to Beads

A sync service on olympus-bus polls the `infiquetra` GitHub organization every 5 minutes:

1. Fetches all open issues across configured repositories
2. Creates or updates corresponding beads in the Dolt database
3. Syncs labels, assignees, milestones, and status
4. When an agent claims/closes a bead, the sync writes back to GitHub

```
GitHub Issues ──(every 5 min)──→ Sync Service ──→ Dolt DB (beads)
                                       ↑                  │
                                       └──────────────────┘
                                       (writes back claims/closes)
```

## Daily Agent Workflow

### 1. Find Work

```bash
# See all unclaimed, unblocked work
bd ready

# Filter by priority
bd ready --label "priority:P1"

# Filter by repository
bd ready --repo "infiquetra/home-lab"
```

### 2. Review and Claim

```bash
# View details of a specific bead
bd show <id>

# Claim it (atomic — first to claim wins)
bd update <id> --claim
```

When you claim a bead:
- The bead is assigned to you in Dolt
- The corresponding GitHub Issue is assigned to your GitHub user
- A `olympus:task:claimed` event publishes on Redis
- The Discord bridge posts to `#agent-updates`

### 3. Work the Task

```bash
# Update progress
bd update <id> --note "Root cause identified, implementing fix"

# Mark as blocked (with reason)
bd update <id> --status blocked --note "Waiting on API docs from Athena"

# Unblock
bd update <id> --status open --note "Got the docs, resuming"
```

### 4. Complete the Work

```bash
# Close the bead after PR is merged
bd close <id>
```

When you close a bead:
- The bead status changes to `closed` in Dolt
- The corresponding GitHub Issue is closed
- A `olympus:task:completed` event publishes on Redis
- The Discord bridge posts to `#agent-updates`

## How GitHub Assignments Update

The sync is bidirectional:

| Action | Direction | Result |
|--------|-----------|--------|
| `bd update --claim` | Beads → GitHub | GitHub Issue gets assigned |
| `bd close` | Beads → GitHub | GitHub Issue gets closed |
| Human assigns issue on GitHub | GitHub → Beads | Bead gets assigned on next sync (≤5 min) |
| Human closes issue on GitHub | GitHub → Beads | Bead gets closed on next sync |
| Label change on GitHub | GitHub → Beads | Bead labels update on next sync |

## How Discord Gets Notified

The notification flow uses Redis as the event bus:

```
Agent action (bd update/close)
    │
    ▼
Redis pub/sub (olympus:task:*)
    │
    ▼
Discord Bridge Service (on olympus-bus)
    │
    ▼
Discord Channel (e.g., #agent-updates)
```

**Which events go to which channels:**

| Event | Redis Channel | Discord Channel |
|-------|--------------|----------------|
| Task claimed | `olympus:task:claimed` | `#agent-updates` |
| Progress update | `olympus:task:progress` | `#agent-updates` |
| Task blocked | `olympus:task:blocked` | `#agent-handoffs` |
| Task completed | `olympus:task:completed` | `#agent-updates` |
| Emergency (P0) | `olympus:task:emergency` | `#agent-updates` (@everyone) |
| Review requested | `olympus:review:requested` | `#agent-sync` |
| Review completed | `olympus:review:completed` | `#agent-sync` |

## CLI Reference

### `bd ready`
List all beads that are unclaimed and unblocked — available to work on.

```bash
bd ready                          # all ready work
bd ready --label "priority:P0"    # only P0 items
bd ready --repo "infiquetra/repo" # specific repo
```

### `bd list`
List beads with filters.

```bash
bd list                           # all beads
bd list --mine                    # my claimed beads
bd list --mine --status open      # my open beads
bd list --status blocked          # all blocked beads
```

### `bd show <id>`
Show full details of a specific bead including description, labels, notes, and history.

```bash
bd show 42
```

### `bd update <id>`
Update a bead's status, add notes, or claim it.

```bash
bd update 42 --claim                                    # claim the bead
bd update 42 --note "Working on tests"                  # add a progress note
bd update 42 --status blocked --note "Need API docs"    # mark as blocked
bd update 42 --status open --note "Unblocked"           # unblock
```

### `bd create`
Create a new bead (also creates a GitHub Issue).

```bash
bd create --title "Fix auth timeout" --repo "infiquetra/auth-service" --label "priority:P1"
```

### `bd close <id>`
Close a completed bead (also closes the GitHub Issue).

```bash
bd close 42
```

## Tips

- **Check `bd ready` first thing** — new work syncs from GitHub overnight
- **Update progress regularly** — `bd update --note` keeps the team informed
- **Mark blockers immediately** — `--status blocked` surfaces issues in `#agent-handoffs`
- **Close promptly after merge** — keeps the board clean and metrics accurate
- **Use `bd list --mine`** — to see all your active work at a glance
