# Follow-up Tasks — Post Fleet Deployment

**Date**: 2026-03-29
**Context**: Hermes fleet migration complete. All 8 agents running. olympus-bus live. These are the remaining items to finish the stack.

---

## Status Summary

| Task | Priority | Status |
|------|----------|--------|
| 1. Init Beads Database | HIGH | ✅ DONE |
| 2. Fix `bd` PATH for non-interactive sessions | HIGH | ✅ DONE |
| 3. Update GitHub PAT — SSH key scope | MEDIUM | ⚠️ PARTIAL |
| 4. Fix tool download 404s | LOW | ✅ DONE |
| 5. Hermes conductor stability on mac mini | MEDIUM | 🔲 OPEN |

---

## 1. Init the Beads Database ✅ DONE

**Resolved 2026-03-29.**

Dolt server was running at `10.220.1.64:3306` but the agent user wasn't created and
the beads project wasn't initialized. Fixed by:
- Running `CREATE USER / CREATE DATABASE / GRANT` in embedded Dolt mode (Ansible task)
- Writing `~/.beads/metadata.json` directly to all agents with the canonical project ID
  (`24542c48-1e8f-4b94-bb60-353973b37f5b`) instead of running `bd init` per-agent

`bd list` returns "No issues found." on all 8 agents.

---

## 2. Fix `bd` PATH for Non-Interactive Sessions ✅ DONE

**Resolved 2026-03-29.**

Added to `ansible/roles/hermes/templates/hermes.service.j2`:
```ini
Environment="PATH=/home/{{ hermes_service_user }}/.local/bin:..."
```

Also added `BEADS_DOLT_PASSWORD` to `hermes.env.j2` so Hermes systemd has DB access.

---

## 3. Update GitHub PAT — Add SSH Key Scope ⚠️ PARTIAL

**Partially resolved 2026-03-29.**

New classic PATs created and vaulted:
- `vault_github_pat` — `olympus_team` token — scopes: repo, admin:public_key, workflow. Expires 2027-03-29.
- `vault_github_pat_admin` — `olympus_team_admin` (full admin) — for Hermes/Ansible infra use. Expires 2027-03-29.

**Remaining issue**: The `olympus_team` PAT is missing the `read:org` scope, so
`gh auth login` returns a non-zero exit code on all agents. This is `ignored_errors: yes`
in the playbook so it doesn't block, but `gh api` calls to list org repos will fail.

**Fix when convenient**:
1. Go to github.com → Settings → Developer settings → Personal access tokens (classic)
2. Edit `olympus_team` — add `read:org` scope (under `admin:org`)
3. If token value changes, re-vault:
   ```bash
   cd ansible
   ansible-vault encrypt_string 'NEW_TOKEN' --name 'vault_github_pat' --vault-password-file ~/.vault_pass.txt
   ```
4. Update `inventory/group_vars/all/all.yml` and re-run `--tags agent_provision`

SSH key registration (admin:public_key) is already included — agents should be able to
push SSH keys to GitHub once `gh auth login` succeeds.

---

## 4. Fix Tool Download 404s ✅ DONE

**Resolved 2026-03-29.**

Pinned versions in `ansible/roles/agent_provision/defaults/main.yml`:
- `git_delta_version: "0.19.2"`
- `lazygit_version: "0.60.0"`

Updated download URLs to use versioned filenames. Removed `ignore_errors: yes` from
these tasks. Also made Nerd Font download non-fatal (`ignore_errors: yes`) since the
129MB zip gets transient 502s from GitHub CDN.

---

## 5. Hermes Conductor Stability on Mac Mini 🔲 OPEN

**Added 2026-03-29.**

Hermes conductor runs natively on the mac mini (10.220.1.2) rather than as a Proxmox VM.
Grafana alerts fire intermittently reporting Hermes as down.

**Possible causes**:
- Mac mini going to sleep → network drops → Hermes process pauses/dies
- No keepalive / restart policy in the launchd plist
- The discord bot token being rate-limited or session-expired

**To investigate**:
```bash
# Check Hermes conductor launchd status on mac mini
ssh jefcox@jeffs-mac-mini.infiquetra.com "launchctl list | grep hermes"

# Check last Hermes log entries
ssh jefcox@jeffs-mac-mini.infiquetra.com "tail -50 ~/Library/Logs/hermes-conductor.log 2>/dev/null"

# Check if mac sleep is disabled
ssh jefcox@jeffs-mac-mini.infiquetra.com "pmset -g | grep -E 'sleep|displaysleep'"
```

**Fix checklist**:
- [ ] Verify launchd plist has `KeepAlive: true` and `RunAtLoad: true`
- [ ] Disable mac mini sleep (`sudo pmset -a sleep 0`)
- [ ] Confirm Grafana alert target points to correct mac mini IP (10.220.1.2)
- [ ] Check Hermes discord token isn't being shared with an agent VM bot

---

## Done (for reference)

- [x] All 8 agents running Hermes + Ollama
- [x] olympus-bus (VM 204): Redis + Dolt + Discord bridge + beads sync timer
- [x] All vault secrets: Google OAuth, GitHub PAT, Redis/Dolt passwords, Discord webhook
- [x] Docs updated: DEPLOYMENT_RUNBOOK, BACKUP_STRATEGY, TROUBLESHOOTING, HERMES-MIGRATION-PLAN
