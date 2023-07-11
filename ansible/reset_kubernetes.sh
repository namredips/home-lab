#!/bin/bash

ansible-playbook -i inventory/hosts.yml reset_kubernetes.yml -u jefcox --vault-password-file ~/.vault_pass.txt --tags ${1:-all}

