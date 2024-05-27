variable "region" {
  description = "The AWS region to deploy in"
  default     = "eu-central-1"
}

variable "vpc_cidr" {
  description = "The CIDR block for the VPC"
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  description = "The CIDR block for the public subnet"
  default     = "10.0.1.0/24"
}

variable "instance_type" {
  description = "The instance type for the EC2 instances"
  default     = "t2.micro"
}

variable "ami" {
    description = "The AMI to use for the EC2 instances"
    default     = "ami-026c3177c9bd54288"
  
}