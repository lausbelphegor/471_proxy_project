provider "aws" {
  region = var.region
}

# Create a VPC
resource "aws_vpc" "proxy_project_vpc" {
  cidr_block = var.vpc_cidr
  # enable_dns_support   = true
  # enable_dns_hostnames = true

  tags = {
    Name = "proxy-project-vpc"
  }
}

# Create a public subnet
resource "aws_subnet" "proxy_project_public_subnet" {
  vpc_id            = aws_vpc.proxy_project_vpc.id
  cidr_block        = var.public_subnet_cidr
  availability_zone = "eu-central-1a"

  tags = {
    Name = "proxy-project-public-subnet"
  }
}

# Create an internet gateway
resource "aws_internet_gateway" "proxy_project_igw" {
  vpc_id = aws_vpc.proxy_project_vpc.id


  tags = {
    Name = "proxy-project-igw"
  }
}

# Create a route table
resource "aws_route_table" "proxy_project_public_rt" {
  vpc_id = aws_vpc.proxy_project_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.proxy_project_igw.id
  }

  tags = {
    Name = "proxy-project-public-route-table"
  }
}

# Associate the route table with the public subnet
resource "aws_route_table_association" "public_rt_assoc" {
  subnet_id      = aws_subnet.proxy_project_public_subnet.id
  route_table_id = aws_route_table.proxy_project_public_rt.id
}

# Create a security group
resource "aws_security_group" "proxy_project_public_sg" {
  vpc_id      = aws_vpc.proxy_project_vpc.id
  name        = "proxy-project-public-sg"
  description = "proxy-project security group for public subnet"

  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "proxy-project-public-sg"
  }
}

resource "aws_key_pair" "proxy_auth" {
  key_name   = "proxy_key"
  public_key = file("./.ssh/proxy_key.pub") # ssh-keygen -t ed25519 -f ./.ssh/proxy_key
}

