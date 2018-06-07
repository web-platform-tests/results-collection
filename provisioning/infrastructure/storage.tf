resource "aws_ebs_volume" "build_master_database" {
  availability_zone = "us-east-1a"
  type = "gp2"
  size = 100
  tags {
    "Name" = "${var.name}-build-master-database"
  }
}

# The results collector uploads JSON-formatted WPT results to this bucket. The
# https://wpt.fyi website currently retrieves files from this bucket directly,
# necessitating CORS support.
resource "google_storage_bucket" "results_store" {
  name = "wptd"
  location = "US"
  storage_class = "MULTI_REGIONAL"

  cors {
    max_age_seconds = 86400
    origin = ["*"]
    method = ["GET", "HEAD"]
  }
}

# The results collector installs experimental browser builds prior to
# collecting results. In order to ensure failed collection attempts can be
# re-tried at a later date (even after new browser builds have been published),
# it uses the following bucket as a mirror for the installation artifacts.
resource "google_storage_bucket" "browser_store" {
  name = "browsers"
  location = "US"
  storage_class = "MULTI_REGIONAL"
}
