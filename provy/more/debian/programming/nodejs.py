#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to provide `Node.js <http://nodejs.org/>`_ utility methods for Debian and Ubuntu distributions.
'''

import re

from fabric.api import cd, settings

from provy.core import Role
from provy.more.debian import AptitudeRole


class NodeJsRole(Role):
    '''
    This role provides `Node.js <http://nodejs.org/>`_ utilities for Debian and Ubuntu distributions.

    Example:
    ::

        from provy.core import Role
        from provy.more.debian import NodeJsRole

        class MySampleRole(Role):
            def provision(self):
                self.provision_role(NodeJsRole)
    '''

    def provision(self):
        '''
        Installs `Node.js <http://nodejs.org/>`_, `NPM <https://npmjs.org/>`_ and their dependencies.
        This method should be called upon if overriden in base classes, or Node won't work properly in the remote server.

        If the server is a Debian, will install via source packages, if it's Ubuntu, will install via
        `Chris Lea's official PPA repository <https://launchpad.net/~chris-lea/+archive/node.js/>`_.

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import NodeJsRole

            class MySampleRole(Role):
                def provision(self):
                    self.provision_role(NodeJsRole) # no need to call this if using with block.
        '''
        if self.is_already_installed():
            return

        distro_info = self.get_distro_info()

        if distro_info.distributor_id == 'Ubuntu':
            self.log('Installing Node.JS and NPM via PPA packages')
            self.provision_to_ubuntu()
        else:
            self.log('Installing Node.JS and NPM via source packages')
            self.provision_to_debian()

        self.log('Node.JS and NPM installed')

    def provision_to_debian(self):
        '''
        Installs `Node.js <http://nodejs.org/>`_, `NPM <https://npmjs.org/>`_ and their dependencies via source packages.

        It's not recommended that you use this method directly; Instead, provision this role directly and it will find out the best way to provision.

        Also, this method doesn't check if Node.js is already installed before provisioning it.

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import NodeJsRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(NodeJsRole) as nodejs:
                        nodejs.provision_to_debian()
        '''
        with self.using(AptitudeRole) as aptitude:
            aptitude.ensure_package_installed('g++')

        installer_directory = '/tmp/nodejs'

        self.ensure_dir(installer_directory, sudo=True)

        with cd(installer_directory):
            self.execute('wget -N http://nodejs.org/dist/node-latest.tar.gz', sudo=True)
            self.execute('tar xzvf node-latest.tar.gz && cd `ls -rd node-v*` && ./configure && make install', sudo=True)

    def provision_to_ubuntu(self):
        '''
        Installs `Node.js <http://nodejs.org/>`_, `NPM <https://npmjs.org/>`_ and their dependencies via
        `Chris Lea's official PPA repository <https://launchpad.net/~chris-lea/+archive/node.js/>`_.

        It's not recommended that you use this method directly; Instead, provision this role directly and it will find out the best way to provision.

        Also, this method doesn't check if Node.js is already installed before provisioning it.

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import NodeJsRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(NodeJsRole) as nodejs:
                        nodejs.provision_to_ubuntu()
        '''
        with self.using(AptitudeRole) as aptitude:
            aptitude.ensure_package_installed('python-software-properties')

        self.execute('add-apt-repository ppa:chris-lea/node.js', sudo=True)

        aptitude.force_update()
        aptitude.ensure_package_installed('nodejs')
        aptitude.ensure_package_installed('npm')
        aptitude.ensure_package_installed('nodejs-dev')

    def is_already_installed(self):
        '''
        Checks if Node.js is already installed on the server.

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import NodeJsRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(NodeJsRole) as nodejs:
                        nodejs.is_already_installed() # True or False
        '''
        with settings(warn_only=True):
            result = self.execute('node --version')

        if not result:
            return False

        return bool(re.match(r'v[\d]', result))
