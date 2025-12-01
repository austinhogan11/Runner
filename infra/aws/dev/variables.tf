variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Prefix for all Runner resources"
  type        = string
  default     = "chsn-runner"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "vpc_cidr" {
  description = "CIDR block for the main VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default = [
    "10.0.1.0/24",
    "10.0.2.0/24",
  ]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default = [
    "10.0.11.0/24",
    "10.0.12.0/24",
  ]
}

variable "database_url" {
  description = "Database connection URL for the backend"
  type        = string
  default     = "postgresql+psycopg2://runner:runner@db:5432/runner"
}

variable "db_username" {
  type        = string
  description = "DB username"
  default     = "runner"
}

variable "db_password" {
  type        = string
  description = "DB password"
  sensitive   = true
}