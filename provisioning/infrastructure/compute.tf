resource "aws_eip" "production" {
  instance = "${aws_instance.build_master.id}"
  vpc      = true
}

resource "aws_security_group" "web" {
  name = "WPT Dashboard web server"
  vpc_id = "${module.vpc.id}"
  ingress {
    from_port = 80
    to_port = 80
    protocol = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    from_port = 443
    to_port = 443
    protocol = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port = 0
    to_port = 0
    protocol = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "ssh" {
  name = "WPT Dashboard SSH server"
  vpc_id = "${module.vpc.id}"
  ingress {
    from_port = 22
    to_port = 22
    protocol = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port = 0
    to_port = 0
    protocol = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "buildbot" {
  name = "WPT Dashboard Buildbot communication"
  vpc_id = "${module.vpc.id}"
  ingress {
    from_port = 9989
    to_port = 9989
    protocol = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port = 0
    to_port = 0
    protocol = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# > The first four IP addresses and the last IP address in each subnet CIDR
# > block are not available for you to use, and cannot be assigned to an
# > instance. For example, in a subnet with CIDR block 10.0.0.0/24, the following
# > five IP addresses are reserved: 
#
# https://docs.aws.amazon.com/AmazonVPC/latest/UserGuide/VPC_Subnets.html#VPCSubnet
resource "aws_instance" "build_master" {
  ami = "${data.aws_ami.ubuntu_16_04.id}"
  instance_type = "t2.small"
  key_name = "${var.key_name}"
  subnet_id = "${element(module.subnet.ids, 0)}"
  private_ip = "10.101.23.10"
  vpc_security_group_ids = [
    "${aws_security_group.web.id}",
    "${aws_security_group.ssh.id}",
    "${aws_security_group.buildbot.id}",
  ]
  tags {
    "Name" = "${var.name}-build-master"
  }
}

resource "aws_volume_attachment" "database_attachment" {
  device_name = "/dev/sdf"
  volume_id   = "${aws_ebs_volume.build_master_database.id}"
  instance_id = "${aws_instance.build_master.id}"
}

resource "aws_instance" "build_master_staging" {
  ami = "${data.aws_ami.ubuntu_16_04.id}"
  instance_type = "t2.small"
  key_name = "${var.key_name}"
  subnet_id = "${element(module.subnet.ids, 0)}"
  private_ip = "10.101.23.11"
  vpc_security_group_ids = [
    "${aws_security_group.web.id}",
    "${aws_security_group.ssh.id}",
    "${aws_security_group.buildbot.id}",
  ]
  tags {
    "Name" = "${var.name}-build-master"
  }
}

resource "aws_volume_attachment" "staging_database_attachment" {
  device_name = "/dev/sdf"
  volume_id   = "${aws_ebs_volume.build_master_database_staging.id}"
  instance_id = "${aws_instance.build_master_staging.id}"
}

variable "instance_ips" {
  default = {
    "0" = "10.101.23.100"
    "1" = "10.101.23.101"
    "2" = "10.101.23.102"
    "3" = "10.101.23.103"
    "4" = "10.101.23.104"
    "5" = "10.101.23.105"
    "6" = "10.101.23.106"
    "7" = "10.101.23.107"
    "8" = "10.101.23.108"
    "9" = "10.101.23.109"
    "10" = "10.101.23.110"
    "11" = "10.101.23.111"
    "12" = "10.101.23.112"
    "13" = "10.101.23.113"
    "14" = "10.101.23.114"
    "15" = "10.101.23.115"
    "16" = "10.101.23.116"
    "17" = "10.101.23.117"
    "18" = "10.101.23.118"
    "19" = "10.101.23.119"
    "20" = "10.101.23.120"
    "21" = "10.101.23.121"
    "22" = "10.101.23.122"
    "23" = "10.101.23.123"
    "24" = "10.101.23.124"
    "25" = "10.101.23.125"
    "26" = "10.101.23.126"
    "27" = "10.101.23.127"
    "28" = "10.101.23.128"
    "29" = "10.101.23.129"
  }
}

resource "aws_instance" "build_worker" {
  count = "30"

  ami = "${data.aws_ami.ubuntu_18_04.id}"
  instance_type = "t2.small"
  key_name = "${var.key_name}"
  subnet_id = "${element(module.subnet.ids, 0)}"
  private_ip = "${lookup(var.instance_ips, count.index)}"
  vpc_security_group_ids = [
    "${aws_security_group.ssh.id}",
    "${aws_security_group.buildbot.id}",
  ]
  tags {
    "Name" = "${var.name}-build-worker-${count.index}"
  }
}
