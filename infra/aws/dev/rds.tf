resource "aws_db_subnet_group" "runner" {
  name       = "${var.project_name}-${var.environment}-db-subnets"
  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name        = "${var.project_name}-${var.environment}-db-subnets"
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_db_instance" "runner" {
  identifier = "${var.project_name}-${var.environment}-db"

  engine               = "postgres"
  engine_version       = "16.3"
  instance_class       = "db.t3.micro"   # free-tier-ish
  allocated_storage    = 20
  max_allocated_storage = 50

  db_name  = "runner"
  username = var.db_username
  password = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.runner.name
  vpc_security_group_ids = [aws_security_group.db.id]

  skip_final_snapshot      = true
  deletion_protection      = false
  backup_retention_period  = 7
  publicly_accessible      = false
  multi_az                 = false
  storage_encrypted        = true

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}