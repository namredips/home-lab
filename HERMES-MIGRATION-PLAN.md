# Hermes Migration Plan for Mount Olympus

Date: 2026-03-24
Status: Draft
Author: Hermes

## Goal

Migrate the `home-lab` agent infrastructure from OpenClaw to Hermes while preserving the named-agent model, keeping Discord as the human-visible surface, and establishing the mac mini control node as the real orchestration point.

## Key Decisions Already Made

1. The current VM named `Hermes` is now semantically wrong.
   - The real Hermes assistant lives on the mac mini control node.
   - The old `Hermes` VM should be renamed to `Hephaestus` and eventually given the appropriate personality and role.

2. `HERMES_BOT_TOKEN` should be treated as the token for the mac mini conductor Hermes only.
   - Do not assume it should be reused blindly for all future VM agents.

3. The mac mini should be modeled as part of the lab.
   - Not as a Proxmox host.
   - As a first-class control/orchestration node.

4. Prior Discord coordination research is binding architectural input.
   - Discord is good as the human-visible interface.
   - Discord is weak as the actual bot-to-bot control plane.
   - Agent coordination should use structured orchestration rather than free-form bot chat.

5. Desired end state remains:
   - full Hermes replacement
   - every agent VM runs Hermes instead of OpenClaw
   - one Hermes instance per named VM
   - Discord/messaging remains the human-visible surface
   - mac mini remains the orchestration/control node

## Architectural Position

### Recommended interpretation of the target state

The desired end state is accepted, but with one important refinement:
- Discord remains the human-facing UI.
- Discord should not be treated as the authoritative machine control plane for agent-to-agent coordination.

This implies a layered architecture:

1. Human-visible layer
   - Discord
   - human interaction, visibility, status, lightweight control

2. Control/orchestration layer
   - mac mini control node
   - planning, deployment, supervision, GitHub operations, coordination

3. Worker/specialist layer
   - named agent VMs in the Proxmox cluster
   - Hermes runtimes replacing OpenClaw over time

4. Machine coordination layer
   - structured orchestration / task passing
   - not free-form Discord bot-to-bot chat

## Phase 1 Preflight Results (Executed)

The following checks were run from the mac mini control node.

### 1. Workspace and repo status
- Workspace root created:
  - `~/workspace/infiquetra/`
- Repo cloned:
  - `~/workspace/infiquetra/home-lab`

### 2. Network reachability to Proxmox hosts
All Proxmox host IPs responded to ping:
- `10.220.1.7`
- `10.220.1.8`
- `10.220.1.9`
- `10.220.1.10`
- `10.220.1.11`
- `10.220.1.12`

Result:
- basic L3 reachability from the mac mini to the cluster is good

### 3. DNS observations
Name resolution is partial / inconsistent from this machine:
- Resolved successfully:
  - `r420.infiquetra.com`
  - `r720xd.infiquetra.com`
  - `r820.infiquetra.com`
- Did not resolve in the same check:
  - `r640-1.infiquetra.com`
  - `r640-2.infiquetra.com`
  - `r640-3.infiquetra.com`

Result:
- IP connectivity is stronger than DNS consistency
- any automation that assumes all hostnames resolve may be brittle from the mac mini

### 4. SSH access to Proxmox hosts
SSH as `root` works from this mac mini to all Proxmox hosts, though some are currently more reliable by IP than DNS.

Verified working:
- `root@r420.infiquetra.com`
- `root@r720xd.infiquetra.com`
- `root@r820.infiquetra.com`
- `root@10.220.1.8` -> `r640-1`
- `root@10.220.1.9` -> `r640-2`
- `root@10.220.1.12` -> `r640-3`

Result:
- root SSH access from the mac mini to all 6 Proxmox hosts is effectively available
- DNS consistency should be improved or abstracted

### 5. Reachability to agent/service VM IPs
The tested agent/service VM IPs responded to ping:
- `10.220.1.50` through `10.220.1.57`
- `10.220.1.60`
- `10.220.1.62`
- `10.220.1.63`

Result:
- VM network reachability from the mac mini appears good

### 6. SSH access to agent VMs
Direct SSH as `agent` to the named agent VMs failed in batch mode during this preflight.

Result:
- VM IPs are reachable
- but the mac mini does not currently have proven non-interactive SSH access to the agent VMs as `agent`
- this is a real prerequisite gap for cluster-side agent management

### 7. Ansible runtime readiness
Findings:
- `uv` is installed and working
- repo Python environment was not yet present initially
- `uv run ansible --version` succeeded and created `.venv`
- Ansible is runnable from the repo via `uv run`
- inventory graph renders successfully

Result:
- Ansible runtime on the mac mini is viable
- standard pattern should be: run from `~/workspace/infiquetra/home-lab/ansible` using `uv run ...`

### 8. Ansible collections readiness
- `ansible-galaxy collection list` succeeded within the `uv` environment
- collections are present enough for Ansible to enumerate them

Result:
- collection layer appears at least partially usable
- full deployment playbooks still require vault access for real execution

### 9. Vault readiness
Findings:
- `~/.vault_pass.txt` is currently missing on this machine
- `ANSIBLE_VAULT_PASSWORD_FILE` env var is not set
- `uv run ansible ... -m ping` against `proxmox_hosts` failed because encrypted vars (notably `become_pass`) could not be decrypted

Result:
- the mac mini is not yet fully vault-enabled for real playbook execution
- this is the main preflight blocker

### 10. Hermes token availability
Findings:
- `HERMES_BOT_TOKEN` is present in the environment on this machine

Result:
- the new conductor Hermes token is available locally for future vault update work

## Phase 1 Conclusion

Phase 1 outcome: partially successful.

What is ready now:
- repo available locally
- network reachability to cluster and VMs
- root SSH path to Proxmox hosts
- Ansible/uv runtime available on mac mini

What is not ready yet:
- consistent DNS for all hosts from mac mini
- non-interactive SSH to agent VMs as `agent`
- vault password setup on mac mini
- therefore: no safe real Ansible execution requiring encrypted vars yet

## Main Risks Identified

1. Identity collision
- `Hermes` currently refers to both the real mac mini assistant and a cluster VM

2. Control-plane ambiguity
- without explicit modeling, the mac mini remains operationally important but undocumented

3. Discord overreach
- using Discord as the actual machine bus would recreate known weaknesses from the coordination experiments

4. Repo drift
- some OpenClaw-era docs and deployment summaries are stale or contradictory

5. Secret strategy ambiguity
- current repo appears optimized for per-agent OpenClaw-era Discord tokens
- future Hermes token strategy must be made explicit

## Recommended Next Phases

### Phase 2 — Topology and identity correction

Goals:
- make repo truth match runtime truth

Tasks:
1. Add the mac mini as a first-class control node in inventory/design
2. Decide its canonical hostname/identity in the repo
3. Rename the old `Hermes` VM to `Hephaestus` in the design
4. Update docs to reflect:
   - mac mini = conductor/control node
   - VM fleet = cluster-side specialists/workers

### Phase 3 — Hermes support in parallel

Goals:
- add Hermes support without ripping out OpenClaw immediately

Tasks:
1. Add `ansible/hermes_cluster.yml`
2. Add `ansible/roles/hermes/`
3. Keep OpenClaw roles/playbooks intact during transition
4. Define coexistence rules:
   - ports
   - service names
   - config locations
   - Discord identities

### Phase 4 — Secret and token strategy

Goals:
- define exactly how Hermes identities map to tokens

Tasks:
1. Update Ansible vault with the conductor Hermes token from `HERMES_BOT_TOKEN`
2. Decide whether cluster-side Hermes instances will:
   - each get their own Discord identity/token
   - or initially run as non-human-facing workers
3. Document the strategy clearly

### Phase 5 — Pilot migration

Recommended pilot:
- mac mini conductor Hermes
- one renamed VM (`Hephaestus`) as the first cluster-side Hermes pilot

Goals:
- validate conductor/worker model
- validate deployment mechanics
- validate observability and rollback

### Phase 6 — Fleet migration

Goals:
- replace OpenClaw with Hermes across the named VM fleet

Notes:
- preserve named personas
- migrate in role-based batches rather than all at once
- retire OpenClaw only after Hermes proves stable

## Open Questions for Future Planning

1. Should all cluster-side Hermes nodes be independently human-facing in Discord from day one?
2. What structured control-plane mechanism should mediate inter-agent coordination?
3. What exact personality/role should `Hephaestus` take on?
4. Should the mac mini be represented only in Ansible inventory, or also in top-level architecture docs and runbooks?
5. Which cluster-side agent should be the first true Hermes pilot after repo scaffolding is added?

## Immediate Actionable Follow-Ups

Before any real migration execution beyond preflight:
1. Obtain / install vault password access on the mac mini
2. Decide how the mac mini will be represented in inventory
3. Confirm the rename of VM 104 from `Hermes` to `Hephaestus`
4. Decide whether cluster-side Hermes nodes are initially workers-only or fully Discord-visible

## Notes from Prior Discord Coordination Research

This plan incorporates the earlier report saved in iCloud:
- `~/Library/Mobile Documents/com~apple~CloudDocs/AI-Drafts/Agent-Coordination/2026-03-23_hermes-openclaw-discord-coordination-report.md`

Key inherited guidance:
- Discord is excellent as a human-visible coordination surface
- Discord is weak as a raw bot-to-bot transport layer
- structured orchestration is preferred over free-form cross-bot chat
