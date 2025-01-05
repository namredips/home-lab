#!/bin/bash


kubectl apply -f test-hostpath-pvc.yml
kubectl apply -f test-zfs-pvc.yml
kubectl apply -f test-single-pvc.yml
kubectl apply -f test-double-pvc.yml
kubectl apply -f test-triple-pvc.yml
