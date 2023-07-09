#!/bin/bash

if [ -z "$1" ]
then
  echo "no inventory defined"
else
  inventory=$1
  scp r420:/etc/kubernetes/admin.conf ~/bin/k_$inventory.conf
  kubectl config set-cluster cluster.local --server https://r420:6443
fi

