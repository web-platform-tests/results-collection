##
# This module manages a VPC for all of our infrastructure to exist in.
#
variable "name" { default = "vpc" }
variable "cidr" { }

output "id" { value = "${aws_vpc.main.id}" }
output "cidr" { value = "${aws_vpc.main.cidr_block}" }

resource "aws_vpc" "main" {
  cidr_block = "${var.cidr}"
  enable_dns_hostnames = true
  enable_dns_support = true
  tags {
    Name = "${var.name}"
  }
}
