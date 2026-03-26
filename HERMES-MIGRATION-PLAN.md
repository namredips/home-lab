# Hermes Migration Plan for Mount Olympus

Date: 2026-03-25
Status: In Progress (Phase 6)
Author: Hermes

## Goal

Migrate the `home-lab` agent infrastructure from OpenClaw to Hermes while preserving the named-agent model, keeping Discord as the human-visible surface, and establishing the mac mini control node as the real orchestration point.

## Key Decisions Made

1. The VM previously named `Hermes` (VM 104) has been **renamed to Hephaestus**.
   - The real Hermes assistant lives on the mac mini control node.
   - Hephaestus has the infrastructure/automation personality and role.

2. `HERMES_BOT_TOKEN` is the token for the mac mini conductor Hermes only.
   - Each VM agent has its own Discord bot token (`vault_discord_bot_token_<name>`).

3. The mac mini is modeled as a first-class control node in the inventory.
   - Not as a Proxmox host.
   - As part of the `control_nodes` inventory group.
   - DNS: jeffs-mac-mini.infiquetra.com (10.220.1.2)

4. Discord is the human-visible interface only.
   - Agent coordination uses Beads (Dolt) + Redis pub/sub.
   - Discord bridge on olympus-bus surfaces key events to channels.

5. Desired end state:
   - Every agent VM runs Hermes instead of OpenClaw
   - One Hermes instance per named VM
   - Discord/messaging is the human-visible surface
   - Mac mini is the orchestration/control node
   - Beads + Redis handle machine coordination

## Architectural Position

### Layered Architecture (Implemented)

1. **Human-visible layer**
   - Discord
   - Human interaction, visibility, status, lightweight control
   - Channels: #agent-updates, #agent-handoffs, #agent-sync, #architecture

2. **Control/orchestration layer**
   - Mac mini control node (Hermes conductor + Freya)
   - Planning, deployment, supervision, GitHub operations, coordination

3. **Worker/specialist layer**
   - Named agent VMs in the Proxmox cluster
   - Hermes runtimes replacing OpenClaw (in progress)

4. **Machine coordination layer**
   - Beads (Dolt DB) for task management
   - Redis pub/sub for real-time events
   - Discord bridge for human visibility
   - Running on olympus-bus (VM 204, 10.220.1.64)

## Phase 1: Preflight — COMPLETE

**Executed**: 2026-03-24

Results:
- Workspace and repo available on mac mini
- Network reachability to all 6 Proxmox hosts and all VMs confirmed
- Root SSH access to all Proxmox hosts working
- Ansible/uv runtime operational on mac mini
- `HERMES_BOT_TOKEN` present in environment

Resolved blockers:
- DNS inconsistency for R640s — using IP-based inventory for reliability
- Vault password — installed at `~/.vault_pass.txt` on mac mini
- Agent VM SSH — keys distributed during agent_provision role

## Phase 2: Topology & Identity Correction — COMPLETE

**Executed**: 2026-03-24

Completed:
- Mac mini added as control node in inventory (`control_nodes` group)
- Canonical hostname set: jeffs-mac-mini.infiquetra.com
- VM 104 renamed from `Hermes` to `Hephaestus` in all configs and docs
- Documentation updated to reflect:
  - Mac mini = conductor/control node
  - VM fleet = cluster-side specialists/workers
  - Hephaestus = infrastructure/automation role

## Phase 3: Hermes Role — COMPLETE

**Executed**: 2026-03-24

Completed:
- `ansible/hermes_cluster.yml` playbook created
- `ansible/roles/hermes/` role added with setup/reset tasks
- Coexistence rules defined (Hermes replaces OpenClaw, same ports/service names)
- Hermes systemd service template created

## Phase 4: Secret & Token Strategy — COMPLETE

**Executed**: 2026-03-24

Strategy implemented:
- Conductor Hermes token: `vault_hermes_conductor_token` (mac mini only)
- Per-VM agent tokens: `vault_discord_bot_token_<name>` (one per agent)
- Freya token: `vault_discord_bot_token_freya` (mac mini only)
- All tokens stored in Ansible vault (`group_vars/all/all.yml`)
- Each cluster-side Hermes instance is independently Discord-visible from day one

## Phase 5: Pilot Migration — COMPLETE

**Executed**: 2026-03-24

Pilot targets:
- Mac mini conductor Hermes — validated
- Hephaestus (VM 104) — first cluster-side Hermes instance, validated

Results:
- Conductor/worker model confirmed working
- Deployment mechanics validated via Ansible
- Observability confirmed (Discord events visible)
- Rollback procedure tested

## Phase 6: Fleet Migration — IN PROGRESS

**Started**: 2026-03-25

Goals:
- Replace OpenClaw with Hermes across the named VM fleet
- Preserve named personas
- Migrate in role-based batches

Batch plan:
1. ~~Hephaestus (pilot)~~ — Done
2. Leadership: Zeus — In progress
3. Senior: Athena — Pending
4. Developers: Apollo, Artemis, Perseus, Prometheus, Ares — Pending

## Open Questions — Resolved

| Question | Decision |
|----------|----------|
| Should all cluster-side Hermes nodes be independently human-facing in Discord? | **Yes** — each agent has its own Discord bot token and identity |
| What structured control-plane mechanism mediates inter-agent coordination? | **Beads (Dolt) + Redis pub/sub** — Discord bridge for human visibility only |
| What personality/role should Hephaestus take? | **Infrastructure & Automation** — the craftsman/builder of the pantheon |
| Should the mac mini be in inventory and architecture docs? | **Yes** — as `control_nodes` group, documented in all architecture docs |
| Which cluster-side agent is the first Hermes pilot? | **Hephaestus (VM 104)** — renamed from the old Hermes VM |

## Notes from Prior Discord Coordination Research

This plan incorporates the earlier report saved in iCloud:
- `~/Library/Mobile Documents/com~apple~CloudDocs/AI-Drafts/Agent-Coordination/2026-03-23_hermes-openclaw-discord-coordination-report.md`

Key inherited guidance:
- Discord is excellent as a human-visible coordination surface
- Discord is weak as a raw bot-to-bot transport layer
- Structured orchestration (Beads + Redis) is preferred over free-form cross-bot chat
