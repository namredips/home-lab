# Model Routing Guide

## Architecture

Hermes Agent (ChatGPT/OpenAI OAuth) is the orchestrator. It invokes specialized CLI tools for execution. This separation means the orchestrator handles planning, context, and delegation while each tool handles its specific domain optimally.

## Routing Table

| Task | Orchestrator | Execution Tool | Notes |
|------|-------------|----------------|-------|
| Planning/architecture | Hermes (ChatGPT) | `claude` (opus model) | Best complex reasoning |
| Code implementation | Hermes | Ollama cloud (kimi-k2.5 or qwen3-coder) → `claude` to refine | Draft cheap, refine with quality |
| Code review | Hermes | `gemini` or `claude` (sonnet) | Compare in practice, update this guide |
| Vision/image tasks | Hermes | `gemini` (pro model) | Strongest multimodal |
| Refactoring | Hermes | `codex` or `claude` | Compare in practice |
| Test generation | Hermes | `claude` or Ollama cloud | Depends on complexity |
| Security analysis | Hermes | `claude` (opus) | Best security reasoning |
| Documentation | Hermes | Ollama cloud (gemini-flash) | Fast, good prose |
| Task coordination | Hermes | `bd` (beads CLI) | Work discovery and claiming |
| GitHub operations | Hermes | `gh` CLI | Issues, PRs, reviews |

## How It Works

1. **Hermes receives a task** — via beads claim, human request, or another agent's handoff
2. **Hermes decides the routing** — based on task type, complexity, and cost constraints
3. **Hermes invokes the appropriate CLI tool** — passing context, constraints, and expected output format
4. **Tool executes and returns** — Hermes validates the output and decides next steps
5. **Hermes reports results** — via beads update, Redis event, and Discord bridge

## Cost Optimization Strategy

The "draft cheap, refine with quality" pattern applies broadly:

- **First pass**: Use Ollama cloud or smaller models for initial drafts
- **Refinement**: Use Claude or Gemini to review and improve
- **Final validation**: Use the best-suited model for the task type

This keeps costs manageable while maintaining quality where it matters.

## CLI Tool Reference

| Tool | Provider | What It Does |
|------|----------|-------------|
| `claude` | Anthropic | Code generation, reasoning, security analysis |
| `gemini` | Google | Vision, multimodal, code review |
| `codex` | OpenAI | Refactoring, code transformation |
| `bd` | Beads | Task management (ready, claim, update, close) |
| `gh` | GitHub | Issues, PRs, reviews, releases |
| Ollama cloud | Self-hosted | Fast drafting, documentation, low-cost inference |

## Updating This Guide

This is a living document. When you find a better tool/model combination for a task:

1. Update the routing table above
2. Add a note in the section below explaining the change
3. Include the date and what was compared

### Change Log

| Date | Change | Reason |
|------|--------|--------|
| 2026-03-25 | Initial routing table created | Baseline from architecture planning |
