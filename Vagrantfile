# -*- mode: ruby -*-
# vi: set ft=ruby :

VAGRANTFILE_API_VERSION = '2'

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = 'ubuntu/xenial64'

  config.vm.synced_folder '.', '/vagrant'

  config.vm.network 'forwarded_port', guest: 80, host: 8090

  config.vm.provision 'ansible_local' do |ansible|
    ansible.provisioning_path = '/vagrant/provisioning'
    ansible.playbook = 'provision.yml'
    ansible.inventory_path = 'inventory/vagrant'
    ansible.limit = 'all'
  end
end
