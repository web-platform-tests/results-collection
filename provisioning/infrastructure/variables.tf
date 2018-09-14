##
# This is primarily used as a convience for tagging resources so operators who
# are looking at the web UI can easily see project delinations. It's also used
# as a prefix in places where the underlying cloud provider requires unique
# names for resources we'd otherwise like to name generically.
#
variable "name" {
  default = "wpt-dashboard"
}

##
# The name of the master private key to use for all compute resources. This is
# generated once by hand in the AWS EC2 web UI.
#
variable "key_name" {
  default = "web-platform"
}

##
# This tells Terraform how to authenticate for AWS resources. It expects
# an entry in ~/.aws/credentials with a matching profile. You can create
# this with `aws configure --profile web-platform`.
#
provider "aws" {
  profile = "web-platform"
  region = "us-east-1"
}

provider "google" {
  project = "wptdashboard"
  credentials = "${file("google-cloud-platform.json")}"
}

##
# This tells Terraform where to persist the state of the infrastructure for
# this project. We use S3 so the state doesn't have to be manually checked
# into the repository.
#
terraform {
  backend "s3" {
    bucket = "web-platform-terraform"
    key = "wpt-dashboard.tfstate"
    region = "us-east-1"
    profile = "web-platform"
  }
}

data "aws_ami" "ubuntu_16_04" {
  most_recent = true
  filter {
    name = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-xenial-16.04-amd64-server-20170221"]
  }
  filter {
    name = "virtualization-type"
    values = ["hvm"]
  }
  # Canonical
  owners = ["099720109477"]
}


data "aws_ami" "ubuntu_18_04" {
  most_recent = true
  filter {
    name = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-bionic-18.04-amd64-server-20180617"]
  }
  filter {
    name = "virtualization-type"
    values = ["hvm"]
  }
  # Canonical
  owners = ["099720109477"]
}
