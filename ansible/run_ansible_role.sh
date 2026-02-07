#!/bin/bash

# Function to print usage information
usage() {
    echo "Usage: $0 -r <role_name> -u <user> [-v <variables>] [-t <tags>] [-i <inventory_file>] [-p <playbook_file>]"
    echo "  -r   Role name to execute (required)"
    echo "  -u   User to run the playbook for (required)"
    echo "  -v   Variables in JSON or key=value format (optional)"
    echo "  -t   Additional tags to run (comma-separated, e.g., 'tag1,tag2') (optional)"
    echo "  -i   Inventory file (default: 'inventory.yml') (optional)"
    echo "  -p   Playbook file (default: 'site.yml') (optional)"
    exit 1
}

# Default inventory file, playbook file, and Vault password file
inventory="inventory/hosts.yml"
playbook="k8_cluster.yml"
vault_password_file="~/.vault_pass.txt"
user="jefcox"

# Parse command-line arguments
while getopts "r:u:v:t:i:p:" opt; do
    case "$opt" in
        r) role_name="$OPTARG" ;;
        u) user="$OPTARG" ;;
        v) variables="$OPTARG" ;;
        t) additional_tags="$OPTARG" ;;
        i) inventory="$OPTARG" ;;
        p) playbook="$OPTARG" ;;
        *) usage ;;
    esac
done

# Ensure the role name and user are provided
if [[ -z "$role_name" || -z "$user" ]]; then
    echo "Error: Role name and user are required."
    usage
fi

# Build the tags string (includes the role name as a tag)
if [[ -n "$additional_tags" ]]; then
    tags="$role_name,$additional_tags"
else
    tags="$role_name"
fi

# Build the ansible-playbook command
cmd=(
    uv
    run
    ansible-playbook
    -i "$inventory"
    "$playbook"
    -u "$user"
    --tags "$tags"
    --vault-password-file "$vault_password_file"
)

# Add variables if provided
if [[ -n "$variables" ]]; then
    cmd+=(--extra-vars "$variables")
fi

# Execute the command
echo "Running: ${cmd[*]}"
"${cmd[@]}"
