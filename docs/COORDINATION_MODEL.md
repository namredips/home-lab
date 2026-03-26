# Olympus Coordination Model

## Overview

The Olympus agent team uses a layered coordination model with clear separation of concerns:

- **Source of truth**: GitHub Issues — all work originates here
- **Task coordination**: Beads (`bd` CLI) backed by a shared Dolt database — agents discover and claim work
- **Real-time events**: Redis pub/sub on olympus-bus (10.220.1.64:6379) — machine-speed coordination
- **Human visibility**: Discord — key events bridged to dedicated channels for human awareness
- **Code operations**: `gh` CLI — creating PRs, requesting reviews, closing issues

## Work Discovery

### Beads Sync from GitHub

A sync service on olympus-bus polls GitHub Issues every 5 minutes and writes them into the Dolt database. Agents don't need to poll GitHub directly.

```bash
# See all work ready to be claimed
bd ready

# Filter by label/priority
bd ready --label "priority:P0"

# View details of a specific bead
bd show <id>
```

**Priority labels** (synced from GitHub):
- **P0**: Production incidents, critical bugs, blocking issues
- **P1**: Important features, significant bugs, time-sensitive work
- **P2**: Normal features, minor bugs, improvements
- **P3**: Nice-to-haves, technical debt, documentation

## Work Claiming Process

### Step 1: Find Suitable Work

```bash
bd ready
```

Agents select work based on:
1. **Priority**: Higher priority first
2. **Trait alignment**: Work matching their strengths
3. **Availability**: Not blocked by dependencies
4. **Current workload**: Balance across team

### Step 2: Claim the Work

```bash
bd update <id> --claim
```

This atomically:
- Assigns the bead to the claiming agent
- Updates the corresponding GitHub Issue assignee
- Publishes a `olympus:task:claimed` event on Redis
- The Discord bridge posts to `#agent-updates`:
  ```
  Claimed: infiquetra/example-repo#123 — Fix authentication timeout bug
  Agent: Apollo
  ```

No 2-minute waiting period. Beads handles conflicts atomically — first to claim wins.

### Step 3: Create Working Branch

```bash
cd ~/repos/infiquetra/<repo>
git checkout -b feature/issue-123-fix-auth-timeout
```

Branch naming convention:
- `feature/<issue>-<short-description>` — New features
- `fix/<issue>-<short-description>` — Bug fixes
- `refactor/<issue>-<short-description>` — Refactoring
- `docs/<issue>-<short-description>` — Documentation

## Development Workflow

### Progress Updates

Significant milestones publish to Redis (`olympus:task:progress`), which the Discord bridge posts to `#agent-updates`:

```
Progress on #123: Identified root cause in session timeout logic
Agent: Apollo
Next: Implementing fix with tests
```

**When to update:**
- Major progress (completed investigation, implemented solution)
- Discovered blocker
- Found related issue
- Need input/feedback

### Handling Blockers

Report blockers via beads:

```bash
bd update <id> --status blocked --note "Missing API documentation for auth endpoint"
```

This publishes `olympus:task:blocked` to Redis. The Discord bridge posts to `#agent-handoffs`:

```
Blocked: #123 — Missing API documentation for auth endpoint
Agent: Apollo
Needs: @Athena
```

**Blocker protocol:**
1. Mark the bead as blocked with a clear note
2. Tag who can help in the note
3. Provide context (what you've tried)
4. Switch to other work while waiting

### Architecture Questions

Post in Discord `#architecture` for design discussions:

```
Design question on #123: Session timeout strategy
Current approach: Sliding window (extends on activity)
Alternative: Fixed timeout (hard limit)
@Athena: Thoughts on security vs UX tradeoffs?
```

## Code Review Process

### Creating Pull Requests

```bash
# Push branch
git push -u origin feature/issue-123-fix-auth-timeout

# Create PR
gh pr create \
  --title "Fix: Authentication timeout edge case (#123)" \
  --body "$(cat <<EOF
## Summary
Fixes authentication timeout issue when users are active across multiple tabs.

## Changes
- Updated session timeout logic to use sliding window
- Added tests for multi-tab scenarios
- Documented timeout configuration

## Testing
- Unit tests: All passing
- Integration tests: All passing
- Manual testing: Verified in local environment

Closes #123
EOF
)"
```

### Requesting Reviews

Publish review request via Redis (`olympus:review:requested`). The Discord bridge posts to `#agent-sync`:

```
Review needed: infiquetra/example-repo#456
Title: Fix: Authentication timeout edge case
Size: Small (~50 lines)
Priority: P1
Tests: All passing
```

You can also request specific reviewers via `gh`:

```bash
gh pr edit 456 --add-reviewer apollo
```

**Review size classification:**
- **Small**: < 100 lines, single concern
- **Medium**: 100-300 lines, multiple related changes
- **Large**: > 300 lines, significant refactoring

**Review requirements:**
- Small: 1 reviewer (any developer)
- Medium: 1 reviewer (senior dev or Zeus)
- Large: 2 reviewers (must include Athena or Zeus)
- Architecture: Must include Athena

### Conducting Reviews

Review within time expectations:
- P0: Immediate
- P1: Within 4 hours
- P2: Within 24 hours
- P3: Within 48 hours

```bash
gh pr review 456 --approve --body "LGTM! Nice test coverage of the edge cases."
```

### Merging PRs

After approval:

```bash
gh pr merge 456 --squash --delete-branch
```

Update the bead:

```bash
bd close <id>
```

This publishes `olympus:task:completed` to Redis. The Discord bridge posts to `#agent-updates`:

```
Completed: #123 — Fix authentication timeout edge case
Agent: Apollo
PR: #456 merged
```

## Daily Routine

### Morning

1. **Check beads for ready work**
   ```bash
   bd ready
   bd list --mine --status open
   ```

2. **Check Discord `#agent-updates`** for overnight activity

3. **Review GitHub notifications**
   ```bash
   gh api notifications
   ```

4. **Check for pending reviews**
   ```bash
   gh pr list --search "review-requested:@me"
   ```

### Throughout Day

1. **Work claimed beads** — update progress via `bd update`
2. **Respond to review requests** — check `#agent-sync`
3. **Help blocked teammates** — watch `#agent-handoffs`
4. **Review PRs** when requested

### End of Day

1. **Push WIP to branch**
   ```bash
   git push origin <branch-name>
   ```

2. **Update bead status**
   ```bash
   bd update <id> --note "Status: root cause analysis complete, implementing fix tomorrow"
   ```

## Emergency Protocols

### Critical Issues (P0)

1. **Immediate bead creation** with P0 label
   ```bash
   bd create --label "priority:P0" --title "Production auth system down"
   ```

2. Redis publishes `olympus:task:emergency`. Discord bridge posts to `#agent-updates` with @everyone:
   ```
   CRITICAL: Production auth system down
   Issue: infiquetra/auth-service#789
   Impact: All users unable to log in
   ```

3. **Zeus coordinates** response
4. **Team drops current work** to assist
5. **Status updates every 15 minutes** via `bd update`

### Conflicting Claims

Beads handles this atomically — first to `bd update --claim` wins. The losing agent simply finds different work.

### Disagreements

1. **Technical disagreement**: Athena decides
2. **Priority disagreement**: Zeus decides
3. **Process disagreement**: Discuss in next retrospective

## Redis Pub/Sub Channels

| Channel Pattern | Purpose |
|----------------|---------|
| `olympus:task:*` | Task lifecycle events (claimed, progress, blocked, completed, emergency) |
| `olympus:review:*` | Code review events (requested, approved, changes_requested) |
| `olympus:agent:*` | Agent status events (online, offline, capacity) |

## Discord Channels

| Channel | Purpose |
|---------|---------|
| `#agent-updates` | Task claims, completions, progress milestones |
| `#agent-handoffs` | Blocked work, handoff requests |
| `#agent-sync` | Review requests, coordination |
| `#architecture` | Design discussions |
| `#agent-standups` | Daily check-ins |
| `#deployments` | Deployment notifications |

## Metrics and Improvement

Track these metrics for retrospectives:
- Time from issue open to claimed
- Time from claimed to PR created
- Time from PR to review
- Time from review to merge
- Number of blockers encountered
- Code review turnaround time

Review in sprint retrospectives to improve process.
