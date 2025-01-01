#!/bin/bash

ansible-playbook -i inventory/hosts.yml k8_cluster.yml -u jefcox --vault-password-file ~/.vault_pass.txt --tags ${1:-all}

