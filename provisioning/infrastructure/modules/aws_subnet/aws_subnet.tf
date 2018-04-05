##
# This modules manages subnets for a VPC.
#
variable "name" { }
variable "azs" { type = "list" }
variable "vpc_id" { }
variable "cidr_blocks" { type = "list" }

output "ids" { value = ["${aws_subnet.main.*.id}"] }
output "cidr_blocks" { value = ["${aws_subnet.main.*.cidr_block}"] }
output "route_table_id" { value = "${aws_route_table.main.id}" }

##
# Create one subnet for each availablity zone.
#
resource "aws_subnet" "main" {
  count = "${length(var.cidr_blocks)}"
  vpc_id = "${var.vpc_id}"
  cidr_block = "${element(var.cidr_blocks, count.index)}"
  availability_zone = "${element(var.azs, count.index)}"
  map_public_ip_on_launch = true
  tags {
    Name = "${var.name}-${count.index}"
  }
}

##
# Configure ACL to allow all inbound and outbound traffic. Further access
# control is managed by security groups.
#
resource "aws_network_acl" "main" {
  vpc_id = "${var.vpc_id}"
  subnet_ids = ["${aws_subnet.main.*.id}"]
  ingress {
    protocol = -1
    rule_no = 100
    action = "allow"
    cidr_block = "0.0.0.0/0"
    from_port = 0
    to_port = 0
  }
  egress {
    protocol = -1
    rule_no = 100
    action = "allow"
    cidr_block =  "0.0.0.0/0"
    from_port = 0
    to_port = 0
  }
  tags {
    Name = "${var.name}"
  }
}

##
# Create a gateway to the internet.
#
resource "aws_internet_gateway" "main" {
  vpc_id = "${var.vpc_id}"
  tags {
    Name = "${var.name}"
  }
}

##
# Create a route table for subnets.
#
resource "aws_route_table" "main" {
  vpc_id = "${var.vpc_id}"
  tags {
    Name = "${var.name}"
  }
}

##
# Create an entry in each of our route tables that provides internet access
# via the gateway defined above.
#
resource "aws_route" "main" {
  route_table_id = "${aws_route_table.main.id}"
  destination_cidr_block = "0.0.0.0/0"
  gateway_id = "${aws_internet_gateway.main.id}"
}

##
# Associate route tables with subnets.
#
resource "aws_route_table_association" "main" {
  count = "${length(var.cidr_blocks)}"
  subnet_id = "${element(aws_subnet.main.*.id, count.index)}"
  route_table_id = "${aws_route_table.main.id}"
}
