#!/usr/bin/env bash

sudo ln -s /usr/bin/python3 /usr/bin/python
sudo swapoff -a
sudo sed -i '/ swap /d' /etc/fstab

#sudo lvm lvextend -l +100%FREE /dev/ubuntu-vg/ubuntu-lv
#sudo resize2fs -p /dev/mapper/ubuntu--vg-ubuntu--lv
