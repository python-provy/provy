#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to provision packages installed via the `NPM <https://npmjs.org/>`_ package manager for Debian distributions.
'''

from fabric.api import settings
from provy.core import Role

from provy.more.debian.programming.nodejs import NodeJsRole


class NPMRole(Role):
    '''
    This role provides package management operations with `NPM <https://npmjs.org/>`_ within Debian distributions.

    Example:
    ::

        from provy.core import Role
        from provy.more.debian import NPMRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(NPMRole) as role:
                    role.ensure_package_installed('socket.io', '0.6.17')
    '''

    time_format = "%d-%m-%y %H:%M:%S"
    key = 'npm-up-to-date'

    def provision(self):
        '''
        Installs NPM. This method should be called upon if overriden in base classes, or NPM won't work properly in the remote server.

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import NPMRole

            class MySampleRole(Role):
                def provision(self):
                    self.provision_role(NPMRole) # no need to call this if using with block.
        '''

        self.provision_role(NodeJsRole)

    def is_package_installed(self, package_name, version=None):
        '''
        Returns :data:`True` if the given package is installed via NPM, :data:`False` otherwise.

        :param package_name: Name of the package to verify
        :type package_name: :class:`str`
        :param version: Version to check for. Defaults to :data:`None`, which makes it check for any version.
        :type version: :class:`str`
        :return: Whether the package is installed or not.
        :rtype: :class:`bool`

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import NPMRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(NPMRole) as role:
                        if role.is_package_installed('socket.io', '0.6.17'):
                            pass
        '''

        with settings(warn_only=True):
            if version:
                package_name = "%s@%s" % (package_name, version)
            return package_name in self.execute("npm --global list | egrep '%s'" % package_name, stdout=False, sudo=True)

    def ensure_package_installed(self, package_name, version=None, stdout=False, sudo=True):
        '''
        Ensures that the given package in the given version is installed via NPM.

        :param package_name: Name of the package to install.
        :type package_name: :class:`str`
        :param version: If specified, installs this version of the package. Installs latest version otherwise.
        :type version: :class:`str`
        :param stdout: Indicates whether install progress should be shown to stdout. Defaults to :data:`False`.
        :type stdout: :class:`bool`
        :param sudo: Indicates whether the package should be installed with the super user. Defaults to :data:`True`.
        :type sudo: :class:`bool`
        :return: Whether the package had to be installed or not.
        :rtype: :class:`bool`

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import NPMRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(NPMRole) as role:
                        role.ensure_package_installed('socket.io', '0.6.17')
        '''

        if not self.is_package_installed(package_name, version):
            if version:
                package_name = "%s@%s" % (package_name, version)

            self.log('%s is not installed (via NPM)! Installing...' % package_name)
            self.execute('npm install --global %s' % package_name, stdout=stdout, sudo=sudo)
            self.log('%s is installed (via NPM).' % package_name)
            return True
        return False
