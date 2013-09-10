# User creation vars
export PROVY_USERNAME=provy
PROVY_GROUP=provy
export PROVY_PASSWORD=provy
PROVY_HOME=/home/provy
PROVY_SHELL=/bin/bash
PROVY_ADMIN_GROUP=sudo
PROVY_PUBLIC_KEY=provy-e2e-key.pub
export PROVY_LOCAL_PRIVATE_KEY=$(PWD)/provy-e2e-key
PROVY_SSH_DIR=$(PROVY_HOME)/.ssh
PROVY_AUTHORIZED_KEYS=$(PROVY_SSH_DIR)/authorized_keys
VAGRANT_KEYS=$(shell dirname $(shell gem which vagrant))/../keys
VAGRANT_PRIVATE_KEY=$(VAGRANT_KEYS)/vagrant

# Network vars
export PROVY_HOST=33.33.33.33
export PROVY_PORT=8888
KNOWN_HOSTS=$(HOME)/.ssh/known_hosts

# Commands
VAGRANT_SSH=vagrant ssh end_to_end -c
PROJECT_ROOT=$(shell dirname $(shell dirname $(PWD)))
export PYTHONPATH=$(PROJECT_ROOT)
PROVY=python ../../provy/console.py


end-to-end:
	@echo Starting end-to-end tests
	@make destroy-vm start-vm prepare-vm run-tests

destroy-vm:
	@echo Destroying previous VM
	@vagrant destroy -f end_to_end

start-vm:
	@echo Starting a new VM
	@vagrant up end_to_end

prepare-vm:
	@echo Preparing VM for the tests
	@make prepare-user
	@make provision

prepare-user:
	@echo Preparing user
	@$(VAGRANT_SSH) "sudo groupadd $(PROVY_GROUP); sudo useradd -g $(PROVY_GROUP) -s $(PROVY_SHELL) -m $(PROVY_USERNAME) -G $(PROVY_ADMIN_GROUP)"
	@$(VAGRANT_SSH) "echo $(PROVY_USERNAME):$(PROVY_PASSWORD) | sudo chpasswd"
	@$(VAGRANT_SSH) "sudo mkdir -p $(PROVY_SSH_DIR)"
	@$(VAGRANT_SSH) "sudo chmod 0700 $(PROVY_SSH_DIR)"
	@scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i $(VAGRANT_PRIVATE_KEY) $(PROVY_PUBLIC_KEY) vagrant@$(PROVY_HOST):
	@$(VAGRANT_SSH) "sudo mv $(PROVY_PUBLIC_KEY) $(PROVY_AUTHORIZED_KEYS)"
	@$(VAGRANT_SSH) "sudo chmod 0640 $(PROVY_AUTHORIZED_KEYS)"
	@$(VAGRANT_SSH) "sudo chown -R $(PROVY_USERNAME):$(PROVY_GROUP) $(PROVY_HOME)"
	-@ssh-keygen -f "$(KNOWN_HOSTS)" -R $(PROVY_HOST)
	-@ssh-keyscan -t rsa,dsa $(PROVY_HOST) >> $(KNOWN_HOSTS)

provision:
	@$(PROVY) -s end-to-end -p $(PROVY_PASSWORD)
	@echo Sleeping for a while to let supervisor start...
	@sleep 5

run-tests:
	@echo Running the tests
	@nosetests test.py
