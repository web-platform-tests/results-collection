output "master_public_ip" {
  value = "${aws_instance.build_master.public_ip}"
}
output "master_staging_public_ip" {
  value = "${aws_instance.build_master_staging.public_ip}"
}
