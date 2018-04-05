##
# This is the network all of our services are hosted in. Each VPC is an isolated
# network for a project to live in.
#
variable "vpc_cidr" {
  default = "10.101.0.0/16"
}

##
# This is all the networks we'll create subnets for. If we want to provide
# high availability for the services we host in this project, we would ideally
# put an instance in each one and load balance between them.
#
variable "subnet_cidr_blocks" {
  type = "list"
  default = [
    "10.101.23.0/24"
  ]
}

##
# Get all availability zones from AWS for the region we are in
#
data "aws_availability_zones" "available" {}

module "vpc" {
  source = "./modules/aws_vpc"
  name = "${var.name}"
  cidr = "${var.vpc_cidr}"
}

module "subnet" {
  source = "./modules/aws_subnet"
  name = "${var.name}"
  azs = "${data.aws_availability_zones.available.names}"
  vpc_id = "${module.vpc.id}"
  cidr_blocks = "${var.subnet_cidr_blocks}"
}
