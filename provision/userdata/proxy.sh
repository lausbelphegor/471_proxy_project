#!/bin/bash


sudo hostnamectl set-hostname proxy-server

cat << EOT >> /etc/cloud/cloud.cfg.d/99-disable-network-config.cfg
network: {config: disabled}
EOT

sudo apt update
sudo apt install software-properties-common -y
sudo git clone https://github.com/lausbelphegor/471_proxy_project.git /opt/471_proxy_project

sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update

sudo apt install python3.10 python3.10-venv python3.10-dev -y
sudo ln -sf /usr/bin/python3.10 /usr/bin/python3
curl -sS https://bootstrap.pypa.io/get-pip.py | sudo python3.10
python3 -m pip install --upgrade pip
python3 -m venv /opt/471_proxy_project/venv
source /opt/471_proxy_project/venv/bin/activate
pip install -r /opt/471_proxy_project/requirements.txt


# Create a systemd service for the proxy server
cat <<EOT >> /etc/systemd/system/proxy_server.service
[Unit]
Description=Proxy Server
After=network.target

[Service]
ExecStart=/usr/bin/python3 /opt/main.py
Restart=always
User=nobody

[Install]
WantedBy=multi-user.target
EOT

# Start and enable the proxy server service
systemctl start proxy_server
systemctl enable proxy_server
