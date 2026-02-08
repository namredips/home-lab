# Agent VM Provisioning Session - 2026-02-07

## ✅ Successfully Completed

### 6 VMs Fully Provisioned
- **athena, apollo, artemis, hermes, perseus, prometheus** are all updated and have all required tools

### System Updates
- All packages upgraded to latest versions
- Kernel updates applied (VMs rebooted where needed)
- Go updated to 1.25.7

### New Tools Installed
**LSP Servers:**
- clangd (C/C++ LSP)
- pyright (Python LSP)
- yaml-language-server (YAML LSP)
- vscode-langservers-extracted (JSON LSP)
- dot-language-server (Graphviz DOT LSP)

**Linters & Formatters:**
- ruff (Python linter/formatter)
- isort (Python import sorter)
- prettier (Code formatter)
- jsonlint (JSON linter)
- fixjson (JSON fixer)

**Build Tools:**
- tree-sitter CLI (via cargo - for nvim-treesitter parser compilation)
- tree (directory listing tool added to base_packages)

### Configuration Updates
- Neovim configs force-refreshed from dotfiles repo
- oh-my-posh theme refreshed
- bin scripts refreshed
- Claude config refreshed

### Code Fixes Committed
1. **bd007b0** - Fixed uv tool install to use `bash -lc` for proper PATH sourcing
2. **7b5352c** - Added missing dev tools, force-refresh mechanism, and reboot handling
3. **1d31e70** - Moved zeus host to r820 for better performance

## ⚠️ Incomplete: Zeus VM

### Issue
Zeus migration from r420 to r820 encountered multiple issues:
- Network interface not coming up after cold migration
- VM was using TCG (software emulation) instead of KVM hardware acceleration
- DHCP not assigning IP address (expected at 10.220.1.199 per inventory)

### Root Cause
Likely r420 doesn't have KVM enabled, causing zeus to run slowly with TCG emulation. Migration preserved the TCG configuration instead of using KVM on r820.

### Current State
- Zeus VM definition exists on r820 but needs to be rebuilt
- Old zeus disk/seed images cleaned up from both r420 and r820
- agent_vm defaults updated to point zeus to r820

### Next Steps (Choose One)

**Option 1: Quick - Provision zeus on r420** (5 minutes)
```bash
# Move zeus back to r420 in agent_vm/defaults/main.yml
# Run provisioning
cd ansible
ansible-playbook -i inventory/hosts.yml openclaw_cluster.yml \
  -u agent --vault-password-file ~/.vault_pass.txt \
  --limit zeus.infiquetra.com --tags agent_provision
```
Pros: Fast, works immediately
Cons: Zeus will be slow if r420 lacks KVM

**Option 2: Rebuild zeus on r820** (needs debugging)
```bash
# First verify agent_vm role can create zeus properly
cd ansible
ansible-playbook -i inventory/hosts.yml openclaw_cluster.yml \
  -u jefcox --vault-password-file ~/.vault_pass.txt \
  --limit r820.infiquetra.com --tags agent_vm
# Then provision it
ansible-playbook -i inventory/hosts.yml openclaw_cluster.yml \
  -u agent --vault-password-file ~/.vault_pass.txt \
  --limit zeus.infiquetra.com --tags agent_provision
```
Pros: Zeus will be fast with KVM
Cons: May need debugging of VM creation

**Option 3: Manual creation with virt-install**
Manually create zeus on r820 with explicit KVM settings, then provision.

## Verification Commands

### Check installed tools on VMs:
```bash
for vm in athena apollo artemis hermes perseus prometheus; do
  echo "=== $vm ==="
  ssh agent@$vm.infiquetra.com '
    tree-sitter --version 2>/dev/null || echo "tree-sitter: NOT FOUND"
    ruff --version 2>/dev/null || echo "ruff: NOT FOUND"
    pyright --version 2>/dev/null || echo "pyright: NOT FOUND"
    prettier --version 2>/dev/null || echo "prettier: NOT FOUND"
    clangd --version 2>/dev/null | head -1 || echo "clangd: NOT FOUND"
  '
done
```

### Check system updates:
```bash
ansible -i ansible/inventory/hosts.yml agent_vms -u agent \
  -m shell -a "uname -r && apt list --upgradable 2>/dev/null | wc -l" \
  --vault-password-file ~/.vault_pass.txt
```

## Files Modified

### ansible/roles/agent_provision/defaults/main.yml
- Added `tree` to base_packages
- Added `install_dev_tools: true`
- Added `force_dotfiles_refresh: false`

### ansible/roles/agent_provision/tasks/setup.yml
- Added reboot check and conditional reboot after apt upgrade
- Added clangd installation (C/C++ LSP)
- Added tree-sitter CLI installation via cargo
- Added Python dev tools (ruff, isort) via uv
- Added Node.js dev tools (pyright, prettier, etc.) via npm
- Added force-refresh mechanism for nvim config, oh-my-posh, bin scripts, Claude config
- Fixed uv tool install to use `bash -lc` for proper PATH

### ansible/roles/agent_provision/tasks/reset.yml
- Added Claude config removal for consistency

### ansible/roles/agent_vm/defaults/main.yml
- Changed zeus host from r420.infiquetra.com to r820.infiquetra.com

## Known Issues

1. **Prometheus SSH host key changed** - Fixed by removing old key
2. **uv not in PATH** - Fixed by using `bash -lc` to source environment
3. **Zeus migration complexity** - Needs proper rebuild on r820

## Recommendations

1. **Immediate**: Choose one of the zeus options above to complete provisioning
2. **Future**: Document the proper VM migration procedure for r420 → r820
3. **Future**: Verify KVM is enabled on all hypervisors for optimal performance
4. **Future**: Consider using cloud-init to handle network configuration more reliably
