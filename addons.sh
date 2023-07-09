#!/bin/bash

update_token () {
  TOKEN=$(kubectl -n kubernetes-dashboard get secret $(kubectl -n kubernetes-dashboard get sa/admin-user -o jsonpath="{.secrets[0].name}") -o go-template="{{.data.token | base64decode}}")
  kubectl config set-credentials kubernetes-admin --token="${TOKEN}"
}

deploy_loadbalancer () {
  kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.11.0/manifests/namespace.yaml
  kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.11.0/manifests/metallb.yaml
  kubectl apply -f loadbalancer_config.yaml

}

deploy_dashboard () {
  helm repo add kubernetes-dashboard https://kubernetes.github.io/dashboard/
  kubectl create namespace kubernetes-dashboard
  helm install --namespace kubernetes-dashboard kubernetes-dashboard kubernetes-dashboard/kubernetes-dashboard --values dashboard-values.yaml
  kubectl apply -f dashboard-adminuser-roles.yaml
}

remove_dashboard () {
  helm delete --namespace kubernetes-dashboard kubernetes-dashboard
  kubectl delete -f dashboard-adminuser-roles.yaml
  kubectl delete namespace kubernetes-dashboard
}

deploy_rook () {
  kubectl create -f rook_crds.yaml
  kubectl create -f rook_common.yaml
  kubectl create -f rook_operator.yaml
  sleep 30
  kubectl create -f rook_cluster.yaml
  sleep 30
  kubectl create -f rook_dashboard.yaml
}

deploy_ingress () {
  kubectl create -f https://bit.ly/k4k8s
}


$1
