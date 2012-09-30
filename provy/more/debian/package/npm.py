#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to provision packages installed via the NPM package manager for Debian distributions.
'''

from fabric.api import settings
from provy.core import Role

from provy.more.debian.programming.nodejs import NodeJsRole

class NPMRole(Role):
    '''
    This role provides package management operations with NPM within Debian distributions.
    <em>Sample usage</em>
    <pre class="sh_python">
    from provy.core import Role
    from provy.more.debian import NPMRole

    class MySampleRole(Role):
        def provision(self):
            with self.using(NPMRole) as role:
                role.ensure_package_installed('socket.io', '0.6.17')
    </pre>
    '''

    time_format = "%d-%m-%y %H:%M:%S"
    key = 'npm-up-to-date'

    def provision(self):
        '''
        Installs NPM. This method should be called upon if overriden in base classes, or NPM won't work properly in the remote server.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import NPMRole

        class MySampleRole(Role):
            def provision(self):
                self.provision_role(NPMRole) # no need to call this if using with block.
        </pre>
        '''

        self.provision_role(NodeJsRole)

    def is_package_installed(self, package_name, version=None):
        '''
        Returns True if the given package is installed via NPM, False otherwise.
        <em>Sample usage</em>
        <em>Parameters</em>
        package_name - Name of the package to verify
        version - Version to verify
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import NPMRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(NPMRole) as role:
                    if role.is_package_installed('socket.io', '0.6.17'):
                        # do something
        </pre>
        '''

        with settings(warn_only=True):
            if version:
                package_name = "%s@%s" % (package_name, version)
            return package_name in self.execute("npm --global list | egrep '%s'" % package_name, stdout=False, sudo=True)

    def ensure_package_installed(self, package_name, version=None, stdout=False, sudo=True):
        '''
        Ensures that the given package in the given version is installed via NPM.
        <em>Parameters</em>
        package_name - Name of the package to install
        version - version to install (or upgrade/downgrade to)
        stdout - Indicates whether install progress should be shown to stdout. Defaults to False.
        sudo - Indicates whether the package should be installed with the super user. Defaults to True.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import NPMRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(NPMRole) as role:
                    role.ensure_package_installed('socket.io', '0.6.17')
        </pre>
        '''

        if not self.is_package_installed(package_name, version):
            if version:
                package_name = "%s@%s" % (package_name, version)

            self.log('%s is not installed (via NPM)! Installing...' % package_name)
            self.execute('npm install --global %s' % package_name, stdout=stdout, sudo=sudo)
            self.log('%s is installed (via NPM).' % package_name)
            return True
        return False
