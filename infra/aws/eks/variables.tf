variable "aws_region" {
  type        = string
  description = "AWS region to deploy EKS"
  default     = "us-east-1"
}

variable "cluster_name" {
  type        = string
  description = "EKS cluster name"
  default     = "runner-eks-dev"
}

variable "tags" {
  type        = map(string)
  description = "Common tags"
  default = {
    Project = "runner"
    Env     = "dev"
  }
}

variable "db_name" {
  type        = string
  description = "Postgres DB name"
  default     = "runner"
}

variable "db_username" {
  type        = string
  description = "Postgres master username"
  default     = "runner_app"
}

variable "db_password" {
  type        = string
  description = "Postgres master password"
  sensitive   = true
}

variable "db_instance_class" {
  type        = string
  description = "RDS instance class"
  default     = "db.t3.micro"
}

variable "db_allocated_storage" {
  type        = number
  description = "RDS storage in GB"
  default     = 20
}