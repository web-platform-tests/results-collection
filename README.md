# WPT Results Collector [![Build Status](https://travis-ci.org/web-platform-tests/results-collection.svg?branch=master)](https://travis-ci.org/web-platform-tests/results-collection)

This project defines a procedure to provision and deploy systems for running
[the web-platform-tests](https://github.com/web-platform-tests/wpt) in a number
of configurations. It currently provides data to power
[wpt.fyi](https://wpt.fyi), a dashboard for reviewing current and historic test
results.

The deployment process is facilitated by [the Ansible configuration management
tool](https://www.ansible.com/). The running system is implemented with
[Buildbot](http://buildbot.net/).

Because the system must access private infrastructure (e.g. [Google Cloud
Storage](https://cloud.google.com/storage/) and the [Sauce
Labs](https://saucelabs.com/) testing environment), some aspects of the process
cannot be shared publicly. The private information is included in this
repository in encrypted form.

## Local development (for project contributors)

To support local development and functional testing, a
[Vagrant](https://www.vagrantup.com/)-mediated
[VirtualBox](https://www.virtualbox.org/) virtual machine is also available.

1. Install [Vagrant](https://www.vagrantup.com/) (version 2) and
   [VirtualBox](https://www.virtualbox.org/) (version 5.2)
2. Open a terminal and navigate to the directory containing this text file
3. Run the following command:

   ```
   vagrant up
   ```

This will initiate the creation of a virtual machine. Further documentation on
using Vagrant can be found in [the "Getting Started" guide by the maintainers
of that project](https://www.vagrantup.com/intro/getting-started/index.html).

This does not rely on any private infrastructure, so any contributor may follow
these instructions. This will require some manual modification of the
configuration files. Those unfamiliar with Ansible may contact the project
maintainers for more detailed instructions. Note that the resulting virtual
machine will not have all the capabilities of the production system.

## Deploying to production (for project maintainers)

1. Install [Ansible] (version 2.5.0 or later), [AWSCLI] & [Terraform]
2. Request the Ansible Vault password from another maintainer and save it to
   the following location:
   `provisioning/configuration/ansible-vault-password.txt`
2. Ensure `~/.aws/credentials` has an entry with administrative access keys
   matching the `profile` for the project. The profile name can be found in
   `terraform/{project}/variables.tf` under the `provider "aws" {}` block.
3. Retrieve a Google Cloud Platform credentials file and save it with the file
   name `google-cloud-platform.json` in the current directory. [Instructions
   are available
   here.](https://www.terraform.io/docs/providers/google/index.html)
4. Open a terminal and navigate to the directory containing this text file
5. Run the following command:

       make deploy

## Related repositories

- [web-platform-tests](https://github.com/w3c/web-platform-tests): The tests
  themselves
- [wpt.fyi](https://github.com/web-platform-tests/wpt.fyi): A dashboard
  displaying test results
- [Results Analysis](https://github.com/web-platform-tests/results-analysis):
  Automated analysis of results from web-platform-tests

## License

Copyright (c) 2017 The WPT Dashboard Project. All rights reserved.

The code in this project is governed by the BSD license that can be found in
the LICENSE file

[Ansible]: https://www.ansible.com/
[AWSCLI]: http://docs.aws.amazon.com/cli/latest/userguide/installing.html
[Terraform]: https://www.terraform.io/downloads.html
