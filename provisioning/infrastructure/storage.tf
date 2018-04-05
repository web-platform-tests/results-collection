resource "aws_ebs_volume" "build_master_database" {
  availability_zone = "us-east-1a"
  type = "gp2"
  size = 50
  tags {
    "Name" = "${var.name}-build-master-database"
  }
}
