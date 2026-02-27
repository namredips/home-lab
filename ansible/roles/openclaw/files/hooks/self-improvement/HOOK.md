# Self-Improvement Hook

## What This Does

This hook fires on the OpenClaw internal trigger to process the agent's workspace files and maintain `MEMORY.md`.

Specifically it:
1. Ensures `MEMORY.md` has standard section headers
2. Reads today's notes (`workspace/notes/YYYY-MM-DD.md`)
3. Flags recurring blockers or new learnings in the Watch List
4. Signals to the agent when manual consolidation is needed (exit code 1)

## When It Fires

Configured as an internal hook in `openclaw.json`:
```json
"hooks": {
  "internal": {
    "enabled": true,
    "entries": {
      "self-improvement": {
        "enabled": true,
        "path": "~/.openclaw/hooks/self-improvement/handler.js"
      }
    }
  }
}
```

## Memory Structure

The hook maintains these sections in `MEMORY.md`:

```markdown
# Agent Memory

## Learnings
- [date] <insight worth keeping>

## Patterns
- [date] <recurring pattern observed>

## Decisions
- [date] <decision made and why>

## Watch List
- [date] <thing to keep an eye on>
```

## Manual Use

You can call the hook directly to process today's notes:
```bash
node ~/.openclaw/hooks/self-improvement/handler.js
```

Exit code 0 = nothing needs attention.
Exit code 1 = agent should review MEMORY.md for consolidation opportunities.

## Extending

To add more processing logic:
1. Edit `handler.js`
2. Add pattern matching against notes content
3. Write structured entries to appropriate sections in MEMORY.md

Keep it simple — the hook should take < 1 second to run.
