#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to provide MongoDB database management utilities for Debian distributions.
'''

from provy.core import Role
from provy.more.debian.package.aptitude import AptitudeRole


class MongoDBRole(Role):

    def provision(self):
        distro_info = self.get_distro_info()

        self.log('Installing MongoDB via packages')

        if distro_info.distributor_id == 'Ubuntu':
            self.provision_to_ubuntu()
        else:
            self.provision_to_debian()

        self.log('MongoDB installed')

    def provision_to_debian(self):
        initialization_type = 'debian-sysvinit'
        self.__provision_with_init_type(initialization_type)

    def provision_to_ubuntu(self):
        initialization_type = 'ubuntu-upstart'
        self.__provision_with_init_type(initialization_type)

    def __provision_with_init_type(self, initialization_type):
        with self.using(AptitudeRole) as aptitude:
            aptitude.ensure_gpg_key('http://docs.mongodb.org/10gen-gpg-key.asc')
            aptitude.ensure_aptitude_source('deb http://downloads-distro.mongodb.org/repo/%s dist 10gen' % initialization_type)
            aptitude.force_update()
            aptitude.ensure_package_installed('mongodb-10gen')
