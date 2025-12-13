resource "aws_vpc" "runner" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = merge(var.tags, {
    Name = "${var.cluster_name}-vpc"
  })
}

resource "aws_internet_gateway" "runner" {
  vpc_id = aws_vpc.runner.id

  tags = merge(var.tags, {
    Name = "${var.cluster_name}-igw"
  })
}

resource "aws_subnet" "runner_public" {
  count                   = 2
  vpc_id                  = aws_vpc.runner.id
  cidr_block              = cidrsubnet(aws_vpc.runner.cidr_block, 4, count.index)
  map_public_ip_on_launch = true
  availability_zone       = data.aws_availability_zones.available.names[count.index]

  tags = merge(var.tags, {
    Name = "${var.cluster_name}-public-${count.index}"
  })
}

resource "aws_route_table" "runner_public" {
  vpc_id = aws_vpc.runner.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.runner.id
  }

  tags = merge(var.tags, {
    Name = "${var.cluster_name}-public-rt"
  })
}

resource "aws_route_table_association" "runner_public" {
  count          = length(aws_subnet.runner_public)
  subnet_id      = aws_subnet.runner_public[count.index].id
  route_table_id = aws_route_table.runner_public.id
}

data "aws_availability_zones" "available" {}