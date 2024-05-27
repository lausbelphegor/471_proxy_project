output "dns_server_public_ip" {
  value = aws_instance.dns_server.public_ip
}

output "proxy_server_public_ip" {
  value = aws_instance.proxy_server.public_ip
}

# output "client_public_ip" {
#   value = aws_instance.client.public_ip
# }
