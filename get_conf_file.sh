CONFIG_FILE=/users/jefcox/.kube/kube_config_lab
scp r420:.kube/config $CONFIG_FILE

if [[ ":$KUBECONFIG:" == *":$CONFIG_FILE:"* ]]; then
  echo "KUBECONFIG already contains $CONFIG_FILE"
else
  echo "KUBECONFIG does not contain $CONFIG_FILE"
  if [ -z "$KUBECONFIG" ]; then
    export KUBECONFIG=$CONFIG_FILE
  else
    export KUBECONFIG=$KUBECONFIG:$CONFIG_FILE
  fi
  echo "KUBECONFIG now contains $KUBECONFIG"
fi

kubectl config --kubeconfig=$CONFIG_FILE set-cluster microk8s-cluster --server https://r420.infiquetra.com:30443
kubectl config --kubeconfig=$CONFIG_FILE rename-context microk8s lab

