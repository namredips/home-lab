# OpenClaw Coordination Model

## Overview

The OpenClaw team uses a hybrid coordination model combining GitHub for work tracking and Mattermost for real-time communication. Agents operate autonomously but collaborate transparently.

## Work Discovery

### GitHub Monitoring

Agents actively monitor the `infiquetra` GitHub organization for new work:

```bash
# Check for unassigned issues across all repos
gh issue list --repo infiquetra/<repo> --state open --assignee ""

# Filter by priority labels
gh issue list --label "priority:P0" --state open

# View issue details
gh issue view <number> --repo infiquetra/<repo>
```

**Monitoring Frequency:**
- P0 (Critical): Continuous monitoring
- P1 (High): Every 15 minutes
- P2 (Normal): Every hour
- P3 (Low): Twice daily

### Issue Prioritization

Issues are prioritized by labels:
- **P0**: Production incidents, critical bugs, blocking issues
- **P1**: Important features, significant bugs, time-sensitive work
- **P2**: Normal features, minor bugs, improvements
- **P3**: Nice-to-haves, technical debt, documentation

## Work Claiming Process

### Step 1: Find Suitable Work

Agents select work based on:
1. **Priority**: Higher priority first
2. **Trait alignment**: Work matching their strengths
3. **Availability**: Not blocked by dependencies
4. **Current workload**: Balance across team

### Step 2: Announce Intent

Post in Mattermost `#dev` channel:

```
🔔 Claiming: infiquetra/example-repo#123
Title: Fix authentication timeout bug
Reason: Matches my precision trait, edge case handling

Objections? Replying in 2 minutes ⏱️
```

**Required information:**
- Issue identifier (repo + number)
- Issue title
- Reason (why you're suited)
- Timing (always 2 minutes)

### Step 3: Wait for Objections

**2-minute window** for team to respond.

**Valid objections:**
- "I'm already working on this"
- "This is blocked by my other work"
- "This should wait for X to complete"
- Zeus/Athena: "Assign to [agent] instead"

**Invalid objections:**
- "I might want this later"
- General disagreement without reason
- Personal preference without justification

### Step 4: Self-Assign

If no objections after 2 minutes:

```bash
gh issue edit <number> --add-assignee @me --repo infiquetra/<repo>
```

Post confirmation:
```
✅ Assigned: infiquetra/example-repo#123
Starting work now.
```

### Step 5: Create Working Branch

```bash
cd ~/repos/infiquetra/<repo>
git checkout -b feature/issue-123-fix-auth-timeout
```

Branch naming convention:
- `feature/<issue>-<short-description>` - New features
- `fix/<issue>-<short-description>` - Bug fixes
- `refactor/<issue>-<short-description>` - Refactoring
- `docs/<issue>-<short-description>` - Documentation

## Development Workflow

### Progress Updates

Post significant milestones in `#dev`:

```
📍 Progress on #123: Identified root cause in session timeout logic
Next: Implementing fix with tests
```

**When to update:**
- Major progress (completed investigation, implemented solution)
- Discovered blocker
- Found related issue
- Need input/feedback

### Handling Blockers

Immediately report in `#dev`:

```
🚧 Blocked on #123: Missing API documentation for auth endpoint
@hermes: Can you share the endpoint specs?
```

**Blocker protocol:**
1. Describe the blocker clearly
2. @ mention person who can help
3. Provide context (what you've tried)
4. Switch to other work while waiting

### Asking for Help

Architecture questions go to `#architecture`:

```
🤔 Design question on #123: Session timeout strategy
Current approach: Sliding window (extends on activity)
Alternative: Fixed timeout (hard limit)

@athena: Thoughts on security vs UX tradeoffs?
```

**Question format:**
- Context (what you're working on)
- Current approach
- Alternatives considered
- Specific person to consult
- What you need (decision, review, guidance)

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

Post in `#pr-reviews`:

```
🔍 Review needed: infiquetra/example-repo#456
Title: Fix: Authentication timeout edge case
Changes: Session timeout logic, ~50 lines
Size: Small
Priority: P1
Tests: ✅ All passing

@apollo: Could use your eye on the test coverage
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
# Review PR
gh pr review 456 --approve --body "$(cat <<EOF
LGTM! Nice test coverage of the edge cases.

Suggestions:
- Consider adding a comment explaining the sliding window logic
- Might want to make timeout configurable via env var

Approving as-is, suggestions are optional.
EOF
)"
```

### Merging PRs

After approval:

```bash
# Merge PR (squash for clean history)
gh pr merge 456 --squash --delete-branch
```

Post completion:
```
✅ Merged: infiquetra/example-repo#456
Closes: #123
```

## Daily Routine

### Morning Check-in

1. **Check Mattermost `#dev`**
   - Overnight activity
   - @ mentions
   - Team status

2. **Review GitHub notifications**
   ```bash
   gh api notifications
   ```

3. **Check assigned work**
   ```bash
   gh issue list --assignee @me --state open
   ```

4. **Look for new high-priority work**
   ```bash
   gh issue list --label "priority:P1" --assignee "" --state open
   ```

### Throughout Day

1. **Monitor `#dev` channel** for coordination
2. **Respond to @ mentions** within 30 minutes
3. **Post progress updates** at milestones
4. **Review PRs** when requested
5. **Help teammates** when they're blocked

### End of Day

1. **Push WIP to branch**
   ```bash
   git push origin <branch-name>
   ```

2. **Update issue with status**
   ```bash
   gh issue comment <number> --body "Status: <update>"
   ```

3. **Post summary if significant progress**
   ```
   📊 End of day: #123
   Completed: Root cause analysis, test cases written
   Tomorrow: Implement fix, validate solution
   ```

## Emergency Protocols

### Critical Issues (P0)

1. **@channel notification** in `#dev`
   ```
   🚨 @channel Critical: Production auth system down
   Issue: infiquetra/auth-service#789
   Impact: All users unable to log in
   ```

2. **Zeus coordinates** response
3. **Team drops current work** to assist
4. **Status updates every 15 minutes**

### Conflicting Assignments

If two agents claim same issue:
1. **First to post** in Mattermost gets priority
2. **Zeus decides** if simultaneous
3. **Loser finds different work** immediately

### Disagreements

1. **Technical disagreement**: Athena decides
2. **Priority disagreement**: Zeus decides
3. **Process disagreement**: Discuss in next retrospective

## Communication Best Practices

### Do:
- ✅ Be clear and concise
- ✅ Provide context
- ✅ @ mention relevant people
- ✅ Update status proactively
- ✅ Acknowledge messages
- ✅ Share learnings

### Don't:
- ❌ Silent work (update team on progress)
- ❌ Work on assigned issues without claiming
- ❌ Ignore @ mentions
- ❌ Skip code reviews
- ❌ Merge without approval
- ❌ Hoard knowledge

## Metrics and Improvement

Track these metrics for retrospectives:
- Time from issue open to claimed
- Time from claimed to PR created
- Time from PR to review
- Time from review to merge
- Number of blockers encountered
- Code review turnaround time

Review in sprint retrospectives to improve process.
