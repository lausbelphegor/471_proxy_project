#!/bin/bash

# Set hostname
sudo hostnamectl set-hostname proxy-server

# Update package list and install prerequisites
sudo apt update
sudo apt install -y software-properties-common

# Add deadsnakes PPA for Python 3.10
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update

# Install Python 3.10 and required packages
sudo apt install -y python3.10 python3.10-venv python3.10-dev

# Ensure python3 points to python3.10
sudo ln -sf /usr/bin/python3.10 /usr/bin/python3

# Install pip for Python 3.10
curl -sS https://bootstrap.pypa.io/get-pip.py | sudo python3.10

# Clone the project repository
sudo git clone https://github.com/lausbelphegor/471_proxy_project.git /opt/471_proxy_project

# Set up a virtual environment
sudo python3 -m venv /opt/471_proxy_project/venv

# Activate the virtual environment and install dependencies
source /opt/471_proxy_project/venv/bin/activate
pip3 install flask

# Deactivate virtual environment
deactivate

# Create a dedicated user for running the proxy service
sudo useradd -r -s /bin/false proxyuser
sudo chown -R proxyuser:proxyuser /opt/471_proxy_project

# Create systemd service file for the proxy server
sudo tee /etc/systemd/system/proxy.service > /dev/null <<EOF
[Unit]
Description=Proxy Server
After=network.target

[Service]
User=proxyuser
WorkingDirectory=/opt/471_proxy_project
Environment="FLASK_APP=main.py"
ExecStart=/opt/471_proxy_project/venv/bin/flask run --host=0.0.0.0 --port=8081
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd to recognize the new service
sudo systemctl daemon-reload

# Enable the proxy service to start on boot
sudo systemctl enable proxy

# Start the proxy service
sudo systemctl start proxy

# Check the status of the proxy service
sudo systemctl status proxy
