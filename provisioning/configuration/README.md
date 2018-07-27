# Results collection system configuration

This subdirectory defines the procedure used to provision and deploy systems
for running the test results collection mechanism for WPT Dashboard (elsewhere
referred to simply as "run"). The process is facilitated by [the Ansible
configuration management tool](https://www.ansible.com/).

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

       vagrant up

This will initiate the creation of a virtual machine. Further documentation on
using Vagrant can be found in [the "Getting Started" guide by the maintainers
of that project](https://www.vagrantup.com/intro/getting-started/index.html).

This does not rely on any private infrastructure, so any contributor may follow
these instructions. This will require some manual modification of the
configuration files. Those unfamiliar with Ansible may contact the project
maintainers for more detailed instructions. Note that the resulting virtual
machine will not have all the capabilities of the production system.

## macOS configuration

This project supports collecting results from macOS systems. However, due to
constraints of that operating system, provisioning must occur via a GUI session
on the target machine.

To prepare the system for configuration, execute the following commands from a
terminal:

    xcode-select --install
    sudo easy_install pip
    sudo pip install ansible

To configure the system, execute the following command:

    make deploy-macos

This command also requires human interaction.
