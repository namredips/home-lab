# Ansible Patterns for Olympus

## Role Structure Convention

Every role follows this layout:

```
ansible/roles/<role_name>/
  tasks/
    main.yml      # import_tasks: setup.yml (when: not reset) and reset.yml (when: reset)
    setup.yml     # Installation and configuration tasks
    reset.yml     # Teardown / cleanup tasks
  defaults/
    main.yml      # All role variables with defaults
  templates/
    *.j2          # Jinja2 templates
  files/
    *             # Static files to copy
  handlers/
    main.yml      # Service restart handlers (if needed)
```

## Variable Naming

- **Vault secrets**: `vault_<service>_<purpose>` (e.g., `vault_discord_bot_token_zeus`)
- **Role defaults**: `<role_name>_<variable>` (e.g., `hermes_primary_model`)
- **Boolean flags**: `install_<thing>: true/false`, `deploy_<thing>: true/false`
- **Paths**: `<role_name>_install_dir`, `<role_name>_config_dir`

## Inventory Groups

```yaml
proxmox_hosts:    # All 6 Proxmox hypervisor nodes
proxmox_master:   # r420 only (cluster master)
proxmox_nodes:    # Non-master Proxmox nodes
agent_vms:        # 8 Hermes agent VMs (zeus through ares)
control_nodes:    # Mac mini conductor
service_vms:      # RustDesk, OME, PBS, Monitoring, olympus-bus
```

## Secrets Strategy

All secrets stored in `ansible/inventory/group_vars/all/all.yml` as `!vault` inline encrypted blocks.

To add a new secret:
```bash
cd ansible
ansible-vault encrypt_string 'the-secret-value' \
  --name 'vault_new_secret_name' \
  --vault-password-file ~/.vault_pass.txt
```
Then paste the output block into `group_vars/all/all.yml`.

To edit existing vault content:
```bash
ansible-vault edit inventory/group_vars/all/all.yml \
  --vault-password-file ~/.vault_pass.txt
```

## Become Strategy

- Proxmox host tasks: `become: yes` (root via sudo)
- Agent VM tasks: mix — some `become: yes`, most run as `ansible_user` (the `agent` user)
- Templates writing to home dir: no `become`, runs as the connection user

## Common Patterns

### Idempotent file creation
```yaml
- name: Create config file
  template:
    src: config.j2
    dest: /etc/service/config.yaml
    mode: '0644'
  notify: Restart service
```

### Conditional installation
```yaml
- name: Install X
  apt:
    name: x-package
    state: present
  become: yes
  when: install_x | default(true)
```

### Secret deployment (mode 0600)
```yaml
- name: Deploy credentials
  template:
    src: credentials.j2
    dest: ~/.config/service/credentials.json
    mode: '0600'
  when: vault_service_credential is defined
  no_log: true
```

### Service management
```yaml
- name: Enable and start service
  systemd:
    name: my-service
    enabled: yes
    state: started
    daemon_reload: yes
  become: yes
```

## Running Playbooks

```bash
# Full agent stack deployment
cd ansible
ansible-playbook -i inventory/hosts.yml hermes_cluster.yml \
  --vault-password-file ~/.vault_pass.txt

# Single role via tags
ansible-playbook -i inventory/hosts.yml hermes_cluster.yml \
  --tags agent_provision --vault-password-file ~/.vault_pass.txt

# Limit to specific host
ansible-playbook -i inventory/hosts.yml hermes_cluster.yml \
  --limit hephaestus.infiquetra.com --vault-password-file ~/.vault_pass.txt

# Dry run (check mode)
ansible-playbook -i inventory/hosts.yml hermes_cluster.yml \
  --check --vault-password-file ~/.vault_pass.txt
```
