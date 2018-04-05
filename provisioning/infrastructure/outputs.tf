output "master_public_ip" {
  value = "${aws_instance.build_master.public_ip}"
}
