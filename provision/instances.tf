
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

# Create Proxy server instance
resource "aws_instance" "proxy_server" {
  ami                         = var.ami
  instance_type               = var.instance_type
  key_name                    = aws_key_pair.proxy_auth.key_name
  subnet_id                   = aws_subnet.proxy_project_public_subnet.id
  vpc_security_group_ids      = [aws_security_group.proxy_project_public_sg.id]
  associate_public_ip_address = true

  user_data = file("userdata/proxy.sh")

  tags = {
    Name = "proxy-project-proxy-server"
  }
}

# # Create Client instance
# resource "aws_instance" "client" {
#   ami                         = var.ami
#   instance_type               = var.instance_type
#   key_name                    = aws_key_pair.proxy_auth.key_name
#   subnet_id                   = aws_subnet.proxy_project_public_subnet.id
#   vpc_security_group_ids      = [aws_security_group.proxy_project_public_sg.id]
#   associate_public_ip_address = true

#   user_data = file("userdata/client.sh")

#   tags = {
#     Name = "proxy-project-client-instance"
#   }
# }
