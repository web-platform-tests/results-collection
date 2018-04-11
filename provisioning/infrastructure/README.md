# Web Platform Tests Infrastructure

## Bootstrapping

1. Install [AWSCLI] & [Terraform]
2. Ensure `~/.aws/credentials` has an entry with administrative access keys
   matching the `profile` for the project. The profile name can be found in
   `terraform/{project}/variables.tf` under the `provider "aws" {}` block.
3. Retrieve a Google Cloud Platform credentials file and save it with the file
   name `google-cloud-platform.json` in the current directory. [Instructions
   are available
   here.](https://www.terraform.io/docs/providers/google/index.html)

### Commands Available

- `terraform init` - Prepare Terraform to manage the project you've specified.
  This must be run once before the other commands are accessible.
- `terraform plan -out project.plan` - Compare your local configuration to the
  actual deployed infrastructure and prepare a plan to reconcile any
  differences.
- `terraform apply project.plan` - After verifying plan, execute the changes.

[AWSCLI]: http://docs.aws.amazon.com/cli/latest/userguide/installing.html
[Terraform]: https://www.terraform.io/downloads.html
