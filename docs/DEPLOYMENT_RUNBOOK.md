# Hermes Agent Deployment Runbook

Complete step-by-step guide for deploying the "Mount Olympus" agent cluster.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Phase 1: Infrastructure Setup](#phase-1-infrastructure-setup)
3. [Phase 2: VM Deployment](#phase-2-vm-deployment)
4. [Phase 3: Agent Configuration](#phase-3-agent-configuration)
5. [Phase 4: Integration & Testing](#phase-4-integration--testing)
6. [Troubleshooting](#troubleshooting)
7. [Rollback Procedures](#rollback-procedures)

---

## Prerequisites

### Access Requirements

- SSH access to all 6 Dell servers (r420, r640-1, r640-2, r720xd, r820, r640-3)
- Google Workspace admin access for email configuration
- GitHub organization admin access
- Anthropic, OpenAI, and Google Cloud accounts with API access

### Local Machine Setup

```bash
# Clone the repository
cd ~/workspace/infiquetra/home-lab/ansible

# Install dependencies
uv sync

# Test connectivity to all hosts
ansible all -i inventory/hosts.yml -m ping

# Expected output: All hosts respond with pong
```

### Secrets Management

Create Ansible vault for sensitive data:

```bash
cd ~/workspace/infiquetra/home-lab/ansible

# Vault password file location
# ~/.vault_pass.txt

# Edit encrypted vault
ansible-vault edit inventory/group_vars/all/all.yml --vault-password-file ~/.vault_pass.txt
```

Key vault variables include Discord bot tokens per agent (e.g., `vault_discord_bot_token_zeus`) and API keys for AI services.

---

## Phase 1: Infrastructure Setup

### Step 1.1: Deploy Proxmox Cluster

This step provisions the 6-node Proxmox VE cluster ("olympus"), including networking, Ceph storage, and VM templates.

```bash
cd ~/workspace/infiquetra/home-lab/ansible

# Full cluster deployment (dry run)
ansible-playbook proxmox_cluster.yml \
  --check \
  --vault-password-file ~/.vault_pass.txt

# Execute full cluster deployment
ansible-playbook proxmox_cluster.yml \
  --vault-password-file ~/.vault_pass.txt
```

**Expected duration**: 30-60 minutes (depends on Ceph OSD creation)

**Verification**:
```bash
# Check cluster status
ssh root@10.220.1.7 "pvecm status"

# Check Ceph health
ssh root@10.220.1.7 "ceph status"

# Check storage pools
ssh root@10.220.1.7 "pvesm status"
```

### Step 1.2: Communication Platform

Agents communicate via **Discord**. No self-hosted chat infrastructure is needed.

- Create Discord server with channels: #general, #dev, #pm, #qa
- Create bot applications per agent at https://discord.com/developers/applications
- Store bot tokens in Ansible vault as `vault_discord_bot_token_<agent>`

---

## Phase 2: VM Deployment

### Step 2.1: Create Agent VMs

Create 8 Ubuntu 24.04 VMs distributed across the Proxmox cluster. VMs are cloned from template VM 9000.

```bash
# VM provisioning is part of the cluster playbook
ansible-playbook proxmox_cluster.yml \
  --tags proxmox_vm \
  --vault-password-file ~/.vault_pass.txt
```

**Expected duration**: 20-30 minutes

**VM Distribution**:
- r820: Zeus (100)
- r640-2: Athena (101), Prometheus (106)
- r640-1: Apollo (102), Perseus (105)
- r420: Artemis (103), Hephaestus (104)
- r720xd: Ares (107)

**Verification**:
```bash
# Check VMs are running on each host
ssh root@10.220.1.7 "qm list"

# Test SSH access to VMs
ansible agent_vms -i inventory/hosts.yml -m ping --vault-password-file ~/.vault_pass.txt

# Expected: All 8 agents respond with pong
```

**Troubleshooting VM Access**:
```bash
# If SSH fails, check VM console via Proxmox web UI
# Or use qm terminal:
ssh root@10.220.1.11  # r820 (Zeus's host)
qm terminal 100

# Check cloud-init status
sudo cloud-init status

# View cloud-init logs
sudo cat /var/log/cloud-init-output.log
```

### Step 2.2: Provision Agent Environments

Install development tools, languages, and AI CLIs on all VMs.

```bash
# Execute agent provisioning
ansible-playbook openclaw_cluster.yml \
  --tags agent_provision \
  --vault-password-file .vault_pass
```

**Expected duration**: 45-60 minutes (parallel installation across 8 VMs)

**What gets installed**:
- Language runtimes: Python 3.12, Node.js 22, Dart/Flutter, Rust, Go, C/C++
- Development tools: git, neovim, tmux, docker, aws-cli, aws-cdk
- AI tools: Claude Code CLI (Codex and Gemini require manual setup)
- Shell: Starship prompt

**Verification**:
```bash
# Check installed versions on one VM
ssh agent@10.220.1.50  # Athena

python3 --version  # Should be 3.12+
node --version     # Should be 22+
flutter --version  # Should show Flutter SDK
rustc --version    # Should show Rust version
go version         # Should be 1.22+
docker --version   # Should show Docker
aws --version      # Should show AWS CLI v2
claude-code --version  # Should show Claude Code CLI
nvim --version     # Should show Neovim
```

---

## Phase 3: Agent Configuration

### Step 3.1: Configure Google Workspace Email

Follow the [Google Workspace Setup Guide](GOOGLE_WORKSPACE_SETUP.md) to configure catch-all email routing.

**Summary**:
1. Go to https://admin.google.com
2. Navigate to Apps → Gmail → Default routing
3. Configure catch-all to route all @infiquetra.com emails to jeff@infiquetra.com
4. Test by sending email to test@infiquetra.com

### Step 3.2: Configure Discord Bot Tokens

Each agent has its own Discord bot application. Tokens are stored in Ansible vault.

```bash
# Edit vault to add/update Discord bot tokens
ansible-vault edit inventory/group_vars/all/all.yml --vault-password-file ~/.vault_pass.txt

# Each agent has a dedicated token:
# vault_discord_bot_token_zeus, vault_discord_bot_token_athena, etc.
```

### Step 3.3: Configure GitHub Accounts

Create GitHub accounts for each agent:

1. Go to https://github.com/signup
2. For each agent:
   - Email: `<agent>@infiquetra.com`
   - Username: `<agent>-infiquetra` (e.g., athena-infiquetra)
   - Password: Generate strong password
   - Check jeff@infiquetra.com for verification
   - Verify email
3. Create organization: `infiquetra-agents`
4. Invite all agent accounts to organization
5. Create shared repositories for collaboration

**Setup SSH Keys on VMs**:

```bash
# For each agent VM
ssh agent@10.220.1.50  # Athena

# Generate SSH key
ssh-keygen -t ed25519 -C "athena@infiquetra.com"

# Display public key
cat ~/.ssh/id_ed25519.pub

# Add to GitHub account:
# GitHub → Settings → SSH and GPG keys → New SSH key
```

### Step 3.4: Authenticate AI Tools

Each agent VM needs authentication for Claude Code, OpenAI, and Google.

**Claude Code Authentication**:

```bash
# SSH into each VM
ssh agent@10.220.1.50

# Authenticate Claude Code
claude-code auth

# Follow browser OAuth flow
# Login with shared Anthropic account (jefcox's subscription)
```

**OpenAI API Key**:

```bash
# SSH into VM
ssh agent@10.220.1.50

# Edit Hermes environment file
nano ~/.hermes/.env

# Add/update:
OPENAI_API_KEY=sk-...
```

**Google API Key**:

```bash
# SSH into VM
ssh agent@10.220.1.50

# Edit Hermes environment file
nano ~/.hermes/.env

# Add/update:
GOOGLE_API_KEY=...
```

**AWS Credentials** (optional for now):

```bash
ssh agent@10.220.1.50
aws configure

# Enter credentials for agent-specific IAM user
```

### Step 3.5: Deploy Hermes

Deploy Hermes agent runtime on all agent VMs.

```bash
# Execute Hermes deployment
ansible-playbook hermes_cluster.yml \
  --vault-password-file ~/.vault_pass.txt
```

**Expected duration**: 10-15 minutes

**Verification**:
```bash
# Check Hermes service on a VM
ssh agent@10.220.1.50
sudo systemctl status hermes-zeus

# View configuration
cat ~/.hermes/config.yml
```

### Step 3.6: Start Hermes Services

Hermes services are started automatically by the playbook. To manually manage:

```bash
# Check service status across all agents
ansible agent_vms -i inventory/hosts.yml \
  -m shell \
  -a "systemctl status hermes-{{ inventory_hostname_short }}" \
  -u agent \
  --become \
  --vault-password-file ~/.vault_pass.txt
```

---

## Phase 4: Integration & Testing

### Step 4.1: Test Discord Integration

1. Open Discord server
2. Send a message in #general mentioning an agent
3. Verify agents respond via their Discord bot connections
4. Check Hermes logs:

```bash
ssh agent@10.220.1.50
sudo journalctl -u hermes-zeus -f
```

### Step 4.2: Test GitHub Integration

```bash
# SSH into an agent VM
ssh agent@10.220.1.50

# Configure git
git config --global user.name "Athena"
git config --global user.email "athena@infiquetra.com"

# Clone a test repository
git clone git@github.com:infiquetra-agents/test-repo.git

# Create a branch and commit
cd test-repo
git checkout -b athena-test
echo "Test from Athena" > athena.txt
git add athena.txt
git commit -m "feat(test): add athena test file"
git push -u origin athena-test

# Create a PR using gh CLI
gh pr create --title "Test PR from Athena" --body "Testing agent collaboration"
```

Verify in GitHub web UI that PR was created.

### Step 4.3: Test Agent Collaboration

Create a test workflow:

1. **Human (Jeff)** posts in Discord #pm channel:
   ```
   @athena Please create a GitHub issue for building a simple TODO app
   ```

2. **Athena** (orchestrator) should:
   - Acknowledge request
   - Create GitHub issue with requirements
   - Assign to a developer (e.g., @apollo)

3. **Apollo** (developer) should:
   - See assignment notification
   - Clone repo
   - Create feature branch
   - Implement TODO app
   - Create PR

4. **Human approval gate**:
   - Jeff reviews PR
   - Approves and merges

### Step 4.4: Monitor Agent Activity

**Discord**:
- Watch channels for agent messages
- Check agent status and activity

**GitHub**:
- Monitor issues and PRs
- Review commit history

**Monitoring VM** (10.220.1.63):
- Grafana dashboards for cluster health
- VM resource usage and Hermes service status

**System Monitoring**:
```bash
# Check Hermes service status
ansible agent_vms -i inventory/hosts.yml \
  -m shell \
  -a "systemctl status hermes-{{ inventory_hostname_short }}" \
  -u agent \
  --become \
  --vault-password-file ~/.vault_pass.txt
```

---

## Troubleshooting

### VM Won't Start

```bash
# Check VM status on Proxmox host
ssh root@<hypervisor-host>
qm list

# Start VM
qm start <vmid>

# Check console via Proxmox web UI or:
qm terminal <vmid>

# Check Proxmox logs
journalctl -u pvedaemon -n 100
```

### SSH Access Fails

```bash
# Check network connectivity
ping 10.220.1.50

# Verify cloud-init completed via Proxmox console
ssh root@<hypervisor-host>
qm terminal <vmid>
# Check /var/log/cloud-init-output.log

# Verify SSH key is authorized
ssh agent@10.220.1.50 -v
# Look for key authentication attempts
```

### Hermes Service Fails

```bash
# SSH into agent VM
ssh agent@10.220.1.50

# Check service status
sudo systemctl status hermes-zeus

# View logs
sudo journalctl -u hermes-zeus -n 100

# Check configuration
cat ~/.hermes/config.yml

# Check environment variables
cat ~/.hermes/.env
```

### API Authentication Issues

**Claude Code**:
```bash
# Re-authenticate
claude-code auth logout
claude-code auth

# Check authentication status
claude-code auth status
```

**OpenAI/Google**:
```bash
# Verify API keys are set
cat ~/.hermes/.env | grep API_KEY

# Test API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Agent Not Responding in Discord

1. Check Hermes service is running: `sudo systemctl status hermes-<agent>`
2. Check Discord bot token is correct in `~/.hermes/.env`
3. Check Hermes logs for connection errors: `sudo journalctl -u hermes-<agent> -f`
4. Restart Hermes service:
   ```bash
   sudo systemctl restart hermes-<agent>
   ```

---

## Rollback Procedures

### Complete Infrastructure Teardown

```bash
cd ~/workspace/infiquetra/home-lab/ansible

# Stop all services and remove VMs
ansible-playbook proxmox_cluster_reset.yml \
  -e reset=true \
  --vault-password-file ~/.vault_pass.txt
```

### Rollback Single Agent

```bash
# Stop agent service
ssh agent@10.220.1.50
sudo systemctl stop hermes-zeus
sudo systemctl disable hermes-zeus

# Remove configuration
rm -rf ~/.hermes

# Destroy VM from Proxmox host
ssh root@10.220.1.11  # r820 (Zeus's host)
qm stop 100
qm destroy 100
```

### Recreate Single Agent

After fixing issues, recreate a single agent:

```bash
# Re-run VM provisioning for just that host
ansible-playbook proxmox_cluster.yml \
  --tags proxmox_vm \
  --limit r820.infiquetra.com \
  --vault-password-file ~/.vault_pass.txt

# Re-run Hermes deployment for that agent
ansible-playbook hermes_cluster.yml \
  --limit zeus.infiquetra.com \
  --vault-password-file ~/.vault_pass.txt
```

---

## Next Steps

After successful deployment:

1. **Create project repositories** in GitHub organization
2. **Define first project** for agents to work on
3. **Establish workflows**:
   - How humans communicate with Athena (PM)
   - How work gets assigned to developers
   - PR review and approval process
   - Deployment gates
4. **Monitor and optimize**:
   - Agent performance and resource usage (Monitoring VM at 10.220.1.63)
   - Discord interaction patterns
   - Code quality and collaboration effectiveness
5. **Scale up** (optional):
   - Add more developer agents as needed
   - Add specialized agents (QA, DevOps, etc.)
   - Integrate additional tools (CI/CD, monitoring)

---

**Last Updated**: 2026-03-28
**Maintainer**: jeff@infiquetra.com
