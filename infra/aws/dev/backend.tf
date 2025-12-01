terraform {
  backend "s3" {
    bucket         = "chsn-runner-tf-state"
    key            = "dev/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "chsn-runner-tf-locks"
    encrypt        = true
  }
}