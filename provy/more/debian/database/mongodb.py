#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to provide MongoDB database management utilities for Debian distributions.
'''

from provy.core import Role
from provy.more.debian.package.aptitude import AptitudeRole


class MongoDBRole(Role):
    '''
    This role provides MongoDB database management utilities for Debian distributions.
    <em>Sample usage</em>
    <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import MongoDBRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(MongoDBRole) as role:
                    role.restart()

    </pre>
    '''
    def provision(self):
        '''
        Installs MongoDB and its dependencies. This method should be called upon if overriden in base classes, or MongoDB won't work properly in the remote server.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import MongoDBRole

        class MySampleRole(Role):
            def provision(self):
                self.provision_role(MongoDBRole) # no need to call this if using with block.
        </pre>
        '''
        distro_info = self.get_distro_info()

        self.log('Installing MongoDB via packages')

        if distro_info.distributor_id == 'Ubuntu':
            self.provision_to_ubuntu()
        else:
            self.provision_to_debian()

        self.log('MongoDB installed')

    def provision_to_debian(self):
        '''
        Installs MongoDB and its dependencies via Debian-specific repository.
        It's not recommended that you use this method directly; Instead, provision this role directly and it will find out the best way to provision.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import MongoDBRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(MongoDBRole) as mongo:
                    mongo.provision_to_debian()
        </pre>
        '''
        initialization_type = 'debian-sysvinit'
        self.__provision_with_init_type(initialization_type)

    def provision_to_ubuntu(self):
        '''
        Installs MongoDB and its dependencies via Ubuntu-specific repository.
        It's not recommended that you use this method directly; Instead, provision this role directly and it will find out the best way to provision.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import MongoDBRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(MongoDBRole) as mongo:
                    mongo.provision_to_ubuntu()
        </pre>
        '''
        initialization_type = 'ubuntu-upstart'
        self.__provision_with_init_type(initialization_type)

    def __provision_with_init_type(self, initialization_type):
        with self.using(AptitudeRole) as aptitude:
            aptitude.ensure_gpg_key('http://docs.mongodb.org/10gen-gpg-key.asc')
            aptitude.ensure_aptitude_source('deb http://downloads-distro.mongodb.org/repo/%s dist 10gen' % initialization_type)
            aptitude.force_update()
            aptitude.ensure_package_installed('mongodb-10gen')

    def restart(self):
        '''
        Restarts the MongoDB database.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import MongoDBRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(MongoDBRole) as mongo:
                    mongo.restart()
        </pre>
        '''
        self.execute('service mongodb restart', sudo=True)
