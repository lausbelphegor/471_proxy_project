
# Create DNS server instance
resource "aws_instance" "dns_server" {
  ami                         = var.ami
  instance_type               = var.instance_type
  key_name                    = aws_key_pair.proxy_auth.key_name
  subnet_id                   = aws_subnet.proxy_project_public_subnet.id
  vpc_security_group_ids      = [aws_security_group.proxy_project_public_sg.id]
  associate_public_ip_address = true


  user_data = file("userdata/dns.tpl")

  tags = {
    Name = "proxy-project-dns-server"
  }
}

resource "aws_ec2_instance_state" "dns_server" {
  instance_id = aws_instance.dns_server.id
  state       = "stopped"
}

# Create Proxy server instance
resource "aws_instance" "proxy_server" {
  ami                         = var.ami
  instance_type               = var.instance_type
  key_name                    = aws_key_pair.proxy_auth.key_name
  subnet_id                   = aws_subnet.proxy_project_public_subnet.id
  vpc_security_group_ids      = [aws_security_group.proxy_project_public_sg.id]
  associate_public_ip_address = true

  user_data = file("userdata/proxy.sh")

  # connection {
  #   type        = "ssh"
  #   host        = aws_instance.proxy_server.public_ip
  #   user        = "ubuntu"
  #   private_key = file("./.ssh/proxy_key")
  # }

  # provisioner "remote-exec" {
  #   inline = [
  #     "sudo hostnamectl set-hostname proxy-server",
  #     "sudo apt update",
  #     "sudo apt install software-properties-common -y",
  #     "sudo git clone https://github.com/lausbelphegor/471_proxy_project.git /opt/471_proxy_project",
  #     "sudo add-apt-repository ppa:deadsnakes/ppa -y",
  #     "sudo apt update",
  #     "sudo apt install python3.10 python3.10-venv python3.10-dev -y",
  #     "sudo ln -sf /usr/bin/python3.10 /usr/bin/python3",
  #     "curl -sS https://bootstrap.pypa.io/get-pip.py | sudo python3.10",
  #     "python3 -m pip install --upgrade pip",
  #     "python3 -m venv /opt/471_proxy_project/venv",
  #     "source /opt/471_proxy_project/venv/bin/activate",
  #     "pip install -r /opt/471_proxy_project/requirements.txt",
  #     "",
  #   ]
  # }

  tags = {
    Name = "proxy-project-proxy-server"
  }
}
