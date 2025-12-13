terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
  }

  backend "s3" {
    bucket         = "chsn-runner-tf-state"
    key            = "eks/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "chsn-runner-tf-locks"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region
}

# We'll configure the kubernetes provider AFTER the cluster exists.
# For now, just declare it; config will be set later with data sources.
provider "kubernetes" {
  host                   = ""
  cluster_ca_certificate = ""
  token                  = ""
}