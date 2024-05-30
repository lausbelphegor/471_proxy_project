#!/bin/bash


sudo hostnamectl set-hostname proxy-server

sudo apt update
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa -y

sudo apt install python3.10 python3.10-venv python3.10-dev -y
sudo ln -sf /usr/bin/python3.10 /usr/bin/python3
curl -sS https://bootstrap.pypa.io/get-pip.py | sudo python3.10

sudo git clone https://github.com/lausbelphegor/471_proxy_project.git /opt/471_proxy_project
sudo python3 -m venv /opt/471_proxy_project/venv
source /opt/471_proxy_project/venv/bin/activate
pip3 install flask
# python3 /opt/471_proxy_project/main.py

# systemd service for the proxy server
sudo tee /etc/systemd/system/proxy.service <<EOF
[Unit]
Description=Proxy Server
After=network.target

[Service]
User=root
WorkingDirectory=/opt/471_proxy_project
Environment="FLASK_APP=main.py"
ExecStart=/opt/471_proxy_project/venv/bin/python3 -m flask run --host=
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable proxy
sudo systemctl start proxy
