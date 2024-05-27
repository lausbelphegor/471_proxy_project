#!/bin/bash

sudo hostnamectl set-hostname dnsmasq-server

sudo apt-get update
sudo apt-get install dnsmasq



sudo systemctl restart dnsmasq