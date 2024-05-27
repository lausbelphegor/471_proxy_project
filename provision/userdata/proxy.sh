#!/bin/bash

sudo hostnamectl set-hostname proxy-server

cat << EOT >> /etc/cloud/cloud.cfg.d/99-disable-network-config.cfg
network: {config: disabled}
EOT

# Update and install necessary packages
sudo apt-get update
sudo apt-get install -y python3 python3-pip

# Install proxy server dependencies (example using a simple Python HTTP proxy)
pip3 install aiohttp

# Create a basic proxy server script (adjust according to your proxy implementation)
cat <<EOT >> /opt/proxy_server.py
import asyncio
from aiohttp import web

async def handle_request(request):
    return web.Response(text="Proxy server running")

app = web.Application()
app.router.add_route('*', '/{tail:.*}', handle_request)

web.run_app(app, port=8080)
EOT

# Create a systemd service for the proxy server
cat <<EOT >> /etc/systemd/system/proxy_server.service
[Unit]
Description=Proxy Server
After=network.target

[Service]
ExecStart=/usr/bin/python3 /opt/proxy_server.py
Restart=always
User=nobody

[Install]
WantedBy=multi-user.target
EOT

# Start and enable the proxy server service
systemctl start proxy_server
systemctl enable proxy_server
