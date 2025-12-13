# Subnet group for RDS (use the same subnets as the EKS cluster)
resource "aws_db_subnet_group" "runner" {
  name       = "${var.cluster_name}-db-subnet-group"
  subnet_ids = aws_subnet.runner_public[*].id

  tags = merge(var.tags, {
    Name = "${var.cluster_name}-db-subnet-group"
  })
}

# Security group for RDS
resource "aws_security_group" "rds" {
  name        = "${var.cluster_name}-rds-sg"
  description = "Security group for RDS Postgres"
  vpc_id      = aws_vpc.runner.id

  # Allow Postgres from anything in this VPC (simple for dev)
  ingress {
    description = "Postgres from VPC"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [aws_vpc.runner.cidr_block]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = var.tags
}

# RDS Postgres instance
resource "aws_db_instance" "runner" {
  identifier              = "${var.cluster_name}-postgres"
  engine                  = "postgres"
  instance_class          = var.db_instance_class
  allocated_storage       = var.db_allocated_storage
  db_name                 = var.db_name
  username                = var.db_username
  password                = var.db_password
  db_subnet_group_name    = aws_db_subnet_group.runner.name
  vpc_security_group_ids  = [aws_security_group.rds.id]
  multi_az                = false
  publicly_accessible     = false
  storage_encrypted       = true
  backup_retention_period = 0
  skip_final_snapshot     = true

  tags = var.tags
}