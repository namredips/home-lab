# Agent VMs Update Plan

**Date:** 2026-02-08
**Goal:** Update all agent VMs with latest configs, packages, and fix deployment issues

## Issues Identified

### 1. Zeus VM Performance (r420 → r820 migration)
- **Current:** zeus on r420 (not handling VM well)
- **Target:** Move zeus to r820
- **Action:** VM migration using libvirt/KVM tools

### 2. Missing oh-my-posh ✅ VERIFIED INSTALLED
- **Status:** oh-my-posh v29.2.0 is installed on zeus
- **Action:** None needed - already working

### 3. Missing tree-sitter CLI ❌ NOT INSTALLED
- **Status:** tree-sitter CLI not found on zeus
- **Current:** Only nvim-treesitter plugin is installed (via vim-plug)
- **Action:** Add tree-sitter CLI installation to agent_provision role
- **Install method:** cargo install tree-sitter-cli (requires Rust which is already installed)

### 4. Outdated System Packages ❌
- **Status:** VMs need package upgrades and kernel updates
- **Action:** Run apt update && apt upgrade on all VMs
- **Kernel:** Install latest kernel and reboot if needed

### 5. Outdated Neovim Configs ❌
- **Status:** nvim configs on VMs are outdated compared to dotfiles repo
- **Example:** zeus has old treesitter.lua (missing incremental_selection, refactor, playground, textobjects)
- **Action:** Re-deploy dotfiles to all VMs with force update for nvim configs only

### 6. .bash_profile Dependencies ❌
**Programs referenced in dotfiles .bash_profile:**
- `brew` - Mac-specific, skip for Ubuntu VMs
- `oh-my-posh` ✅ Already installed
- `jq` ✅ Already in base_packages
- `jenv` ❌ Not installed (Java environment manager)
- `git-prompt.sh` ✅ Already in bin scripts from dotfiles
- `nvim` ✅ Already installed

**Action:** Add jenv installation to agent_provision role (optional, only if Java development needed)

## Implementation Plan

### Phase 1: Update agent_provision Role
- [ ] Add tree-sitter CLI installation
  ```yaml
  - name: Install tree-sitter CLI
    shell: cargo install tree-sitter-cli
    args:
      creates: ~/.cargo/bin/tree-sitter
    when: install_rust
  ```
- [ ] (Optional) Add jenv installation for Java version management
- [ ] Ensure nvim plugin installation runs successfully

### Phase 2: System Upgrades
- [ ] Create upgrade playbook for all agent VMs:
  - apt update
  - apt upgrade -y
  - apt autoremove -y
  - Check kernel version
  - Install latest kernel if needed
  - Reboot if kernel updated

### Phase 3: Dotfiles Refresh
- [ ] Re-run agent_provision on all VMs to pull latest dotfiles
- [ ] Verify nvim configs are updated (treesitter.lua, mason configs)
- [ ] Test nvim LSP and treesitter functionality

### Phase 4: Zeus Migration
- [ ] Shut down zeus VM on r420
- [ ] Export zeus VM disk
- [ ] Import zeus VM to r820
- [ ] Update inventory (zeus ansible_host might change)
- [ ] Start zeus on r820
- [ ] Verify zeus functionality

## Verification Steps

### Per VM Verification
```bash
ssh agent@<vm-ip> '
  echo "=== oh-my-posh ===" && oh-my-posh version
  echo "=== tree-sitter ===" && tree-sitter --version
  echo "=== nvim plugins ===" && nvim --headless +PlugStatus +qall
  echo "=== kernel ===" && uname -r
  echo "=== packages ===" && apt list --upgradable
'
```

### Neovim Config Verification
```bash
ssh agent@<vm-ip> 'nvim --headless -c "TSInstallInfo" -c "q" 2>&1 | head -20'
```

## Priority Order

1. **High:** System upgrades (security + stability)
2. **High:** tree-sitter CLI installation (nvim functionality)
3. **High:** Dotfiles refresh (nvim LSP configs)
4. **Medium:** Zeus migration (performance improvement)
5. **Low:** jenv installation (only if Java development needed)

## Estimated Time

- Phase 1 (role updates): 30 minutes
- Phase 2 (system upgrades): 1-2 hours (includes reboot time)
- Phase 3 (dotfiles refresh): 30 minutes
- Phase 4 (zeus migration): 1 hour

**Total:** ~3-4 hours

## VMs to Update

All agent VMs:
- zeus.infiquetra.com (10.220.1.199) → migrate to r820
- athena.infiquetra.com (10.220.1.123)
- apollo.infiquetra.com (10.220.1.153)
- artemis.infiquetra.com (10.220.1.194)
- hermes.infiquetra.com (10.220.1.198)
- perseus.infiquetra.com (10.220.1.113)
- prometheus.infiquetra.com (10.220.1.156)
