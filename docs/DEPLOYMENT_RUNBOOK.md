# OpenClaw Virtual Employee Deployment Runbook

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

- SSH access to all 5 Dell servers (r420, r710, r8202, r720xd, r820)
- Google Workspace admin access for email configuration
- GitHub organization admin access
- Anthropic, OpenAI, and Google Cloud accounts with API access

### Local Machine Setup

```bash
# Clone the repository
cd ~/workspace/temp/home-lab/ansible

# Install dependencies
uv sync

# Test connectivity to all hosts
ansible all -i inventory/hosts.yml -m ping

# Expected output: All hosts respond with pong
```

### Secrets Management

Create Ansible vault for sensitive data:

```bash
cd ~/workspace/temp/home-lab/ansible

# Create vault password file (keep secure!)
echo "your-strong-vault-password" > .vault_pass
chmod 600 .vault_pass

# Add .vault_pass to .gitignore
echo ".vault_pass" >> ../.gitignore

# Create encrypted vault
ansible-vault create passwd.yml --vault-password-file .vault_pass
```

Add the following variables to `passwd.yml`:

```yaml
---
# Mattermost
vault_mattermost_postgres_password: "strong-postgres-password"
vault_mattermost_bot_token: ""  # Will be populated later

# OpenClaw API keys
vault_openclaw_anthropic_api_key: "sk-ant-..."
vault_openclaw_openai_api_key: "sk-..."
vault_openclaw_google_api_key: "..."
```

---

## Phase 1: Infrastructure Setup

### Step 1.1: Prepare Hypervisor Hosts

This step updates all servers and provisions storage for VMs.

```bash
cd ~/workspace/temp/home-lab/ansible

# Run host preparation (dry run)
ansible-playbook openclaw_cluster.yml \
  --tags host_prepare \
  --check \
  --vault-password-file .vault_pass

# Execute host preparation
ansible-playbook openclaw_cluster.yml \
  --tags host_prepare \
  --vault-password-file .vault_pass
```

**Expected duration**: 15-30 minutes (depends on pending updates)

**Verification**:
```bash
# Check each host
ansible hypervisors -i inventory/hosts.yml -a "df -h /var/lib/libvirt/images"

# Expected: Storage directory exists with adequate space
```

### Step 1.2: Install Libvirt/KVM

Install virtualization platform on all hypervisors.

```bash
# Execute libvirt installation
ansible-playbook openclaw_cluster.yml \
  --tags libvirt \
  --vault-password-file .vault_pass
```

**Expected duration**: 10-15 minutes

**Verification**:
```bash
# Verify libvirt installation
ansible hypervisors -i inventory/hosts.yml -a "virsh version"

# Check virtualization support
ansible hypervisors -i inventory/hosts.yml -a "grep -E '(vmx|svm)' /proc/cpuinfo"

# List storage pools
ansible hypervisors -i inventory/hosts.yml -a "virsh pool-list --all" -b
```

### Step 1.3: Deploy Mattermost

Deploy team communication platform on r720xd.

```bash
# Execute Mattermost deployment
ansible-playbook openclaw_cluster.yml \
  --tags mattermost \
  --vault-password-file .vault_pass
```

**Expected duration**: 5-10 minutes

**Verification**:
```bash
# Check Mattermost is running
curl http://10.220.1.10:8065/api/v4/system/ping

# Expected: {"status":"OK"}

# View containers
ssh jefcox@10.220.1.10 "docker ps"

# Expected: mattermost-app and mattermost-postgres containers running
```

**Access Mattermost**:
1. Open browser: http://10.220.1.10:8065
2. Create admin account (first user becomes admin)
3. Create team: "Mount Olympus"
4. Note: Agent accounts will be created later

---

## Phase 2: VM Deployment

### Step 2.1: Create Agent VMs

Create 8 Ubuntu VMs distributed across hypervisors.

```bash
# Execute VM provisioning
ansible-playbook openclaw_cluster.yml \
  --tags agent_vm \
  --vault-password-file .vault_pass
```

**Expected duration**: 20-30 minutes

**VM Distribution**:
- r420: Athena (1 VM)
- r710: Apollo, Artemis (2 VMs)
- r8202: Hermes (1 VM)
- r720xd: Perseus (1 VM)
- r820: Prometheus, Ares, Poseidon (3 VMs)

**Verification**:
```bash
# Check VMs are running
ansible hypervisors -i inventory/hosts.yml -a "virsh list --all" -b

# Test SSH access to VMs
ansible agent_vms -i inventory/hosts.yml -m ping -u agent

# Expected: All 8 agents respond with pong
```

**Troubleshooting VM Access**:
```bash
# If SSH fails, check VM console
ssh jefcox@10.220.1.7  # r420
sudo virsh console athena

# Press Enter to see login prompt
# Login: agent / (no password, use SSH keys)

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

### Step 3.2: Create Mattermost Accounts

Create accounts for all 8 agents:

1. Open http://10.220.1.10:8065
2. For each agent:
   - Click "Create an account"
   - Email: `<agent>@infiquetra.com` (e.g., athena@infiquetra.com)
   - Username: `<agent>` (e.g., athena)
   - Password: Generate strong password, store in password manager
   - Check jeff@infiquetra.com for verification email
   - Verify email
3. Invite all agents to "Mount Olympus" team
4. Create channels: #general, #dev, #pm, #qa

**Create Bot Tokens**:

For each agent, create a personal access token:

1. System Console → Integrations → Bot Accounts → Create Bot Account
2. Bot name: `<agent>-bot`
3. Description: "OpenClaw agent for <agent>"
4. Copy token → Update vault:

```bash
# Edit vault
ansible-vault edit passwd.yml --vault-password-file .vault_pass

# Add token (same for all agents initially, can separate later)
vault_mattermost_bot_token: "your-bot-token-here"
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

# Edit OpenClaw environment file
nano ~/.openclaw/.env

# Add/update:
OPENAI_API_KEY=sk-...
```

**Google API Key**:

```bash
# SSH into VM
ssh agent@10.220.1.50

# Edit OpenClaw environment file
nano ~/.openclaw/.env

# Add/update:
GOOGLE_API_KEY=...
```

**AWS Credentials** (optional for now):

```bash
ssh agent@10.220.1.50
aws configure

# Enter credentials for agent-specific IAM user
```

### Step 3.5: Install OpenClaw

Deploy OpenClaw on all agent VMs.

```bash
# Execute OpenClaw installation
ansible-playbook openclaw_cluster.yml \
  --tags openclaw \
  --vault-password-file .vault_pass
```

**Expected duration**: 10-15 minutes

**Verification**:
```bash
# Check OpenClaw installation
ssh agent@10.220.1.50
openclaw --version

# Check systemd service
sudo systemctl status openclaw-athena

# View configuration
cat ~/.openclaw/config.yml
```

### Step 3.6: Start OpenClaw Services

Start OpenClaw on all agents:

```bash
# Start all OpenClaw services
ansible agent_vms -i inventory/hosts.yml \
  -m systemd \
  -a "name=openclaw-{{ inventory_hostname_short }} state=started enabled=yes" \
  -u agent \
  --become

# Check service status
ansible agent_vms -i inventory/hosts.yml \
  -m shell \
  -a "systemctl status openclaw-{{ inventory_hostname_short }}" \
  -u agent \
  --become
```

**Access Web Dashboards**:
- Athena: http://10.220.1.50:18789
- Apollo: http://10.220.1.51:18789
- (etc for all 8 agents)

---

## Phase 4: Integration & Testing

### Step 4.1: Test Mattermost Integration

1. Open Mattermost: http://10.220.1.10:8065
2. Login as one of the agent accounts
3. Send a message in #general
4. Verify other agents can see the message
5. Check OpenClaw logs to see if agents respond:

```bash
ssh agent@10.220.1.50
tail -f ~/.openclaw/logs/openclaw.log
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

1. **Human (Jeff)** posts in Mattermost #pm channel:
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

**Mattermost**:
- Watch #general channel for agent messages
- Check agent status and activity

**GitHub**:
- Monitor issues and PRs
- Review commit history

**OpenClaw Dashboards**:
- View web dashboard for each agent: http://10.220.1.XX:18789
- Check memory, task queue, and conversation history

**System Monitoring**:
```bash
# Check VM resource usage
ansible agent_vms -i inventory/hosts.yml -a "htop -C" -u agent

# Check OpenClaw service status
ansible agent_vms -i inventory/hosts.yml \
  -m shell \
  -a "systemctl status openclaw-{{ inventory_hostname_short }}" \
  -u agent \
  --become
```

---

## Troubleshooting

### VM Won't Start

```bash
# Check VM status
ssh jefcox@<hypervisor-host>
sudo virsh list --all

# If VM is shut off
sudo virsh start <agent-name>

# Check console for errors
sudo virsh console <agent-name>

# View VM XML definition
sudo virsh dumpxml <agent-name>

# Check libvirt logs
sudo journalctl -u libvirtd -n 100
```

### SSH Access Fails

```bash
# Check network connectivity
ping 10.220.1.50

# Verify cloud-init completed
ssh jefcox@<hypervisor-host>
sudo virsh console athena
# Check /var/log/cloud-init-output.log

# Verify SSH key is authorized
ssh agent@10.220.1.50 -v
# Look for key authentication attempts

# Manually add SSH key if needed
sudo virsh console athena
# Login and add key to ~/.ssh/authorized_keys
```

### Mattermost Not Accessible

```bash
# Check Docker containers
ssh jefcox@10.220.1.10
docker ps

# If containers aren't running
cd /opt/mattermost
docker-compose up -d

# View logs
docker-compose logs -f

# Check database
docker exec -it mattermost-postgres psql -U mmuser -d mattermost
```

### OpenClaw Service Fails

```bash
# SSH into agent VM
ssh agent@10.220.1.50

# Check service status
sudo systemctl status openclaw-athena

# View logs
sudo journalctl -u openclaw-athena -n 100

# Check configuration
cat ~/.openclaw/config.yml

# Manually run OpenClaw (debugging)
openclaw start --config ~/.openclaw/config.yml --verbose

# Check environment variables
cat ~/.openclaw/.env
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
cat ~/.openclaw/.env | grep API_KEY

# Test API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Agent Not Responding in Mattermost

1. Check OpenClaw service is running
2. Check Mattermost bot token is correct
3. Verify agent account is member of team/channels
4. Check OpenClaw logs for connection errors
5. Restart OpenClaw service:
   ```bash
   sudo systemctl restart openclaw-athena
   ```

---

## Rollback Procedures

### Complete Infrastructure Teardown

```bash
cd ~/workspace/temp/home-lab/ansible

# Stop all services and remove VMs
ansible-playbook openclaw_cluster_reset.yml \
  --vault-password-file .vault_pass

# Optional: Also remove libvirt
ansible-playbook openclaw_cluster_reset.yml \
  -e remove_libvirt=true \
  --vault-password-file .vault_pass
```

### Rollback Single Agent

```bash
# Stop agent service
ssh agent@10.220.1.50
sudo systemctl stop openclaw-athena
sudo systemctl disable openclaw-athena

# Remove configuration
rm -rf ~/.openclaw

# Destroy VM from hypervisor
ssh jefcox@10.220.1.7
sudo virsh destroy athena
sudo virsh undefine athena
sudo rm /var/lib/libvirt/images/athena.qcow2
```

### Recreate Single Agent

After fixing issues, recreate a single agent:

```bash
# On hypervisor, manually recreate VM
# Then re-run provisioning for just that host
ansible-playbook openclaw_cluster.yml \
  --limit athena.infiquetra.com \
  --tags agent_provision,openclaw \
  --vault-password-file .vault_pass
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
   - Agent performance and resource usage
   - Mattermost message patterns
   - Code quality and collaboration effectiveness
5. **Scale up** (optional):
   - Add more developer agents as needed
   - Add specialized agents (QA, DevOps, etc.)
   - Integrate additional tools (CI/CD, monitoring)

---

**Last Updated**: 2026-01-30
**Maintainer**: jeff@infiquetra.com
