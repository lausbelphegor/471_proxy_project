#!/bin/bash


sudo hostnamectl set-hostname proxy-server

sudo apt update
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa -y

sudo apt install python3.10 python3.10-venv python3.10-dev -y
sudo ln -sf /usr/bin/python3.10 /usr/bin/python3
curl -sS https://bootstrap.pypa.io/get-pip.py | sudo python3.10
python3 -m pip install --upgrade pip
python3 -m venv /opt/471_proxy_project/venv

sudo git clone https://github.com/lausbelphegor/471_proxy_project.git /opt/471_proxy_project
sudo python3 -m venv /opt/471_proxy_project/venv
source /opt/471_proxy_project/venv/bin/activate
sudo python3 -m pip install -r /opt/471_proxy_project/requirements.txt
python3 /opt/471_proxy_project/main.py