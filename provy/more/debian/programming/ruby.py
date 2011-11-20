#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to provide Ruby utility methods for Debian distributions.
'''

from fabric.api import settings

from provy.core import Role
from provy.more.debian import AptitudeRole

class RubyRole(Role):
    '''
    This role provides Ruby utilities for Debian distributions.

    <em>Sample usage</em>
    <pre class="sh_python">
    from provy.core import Role
    from provy.more.debian import NodeJsRole

    class MySampleRole(Role):
        def provision(self):
            RubyRole.version = '1.9.3' # change to whatever version you need. This is optional.
            self.provision_role(RubyRole)
    </pre>
    '''

    version = "1.9.3"

    def provision(self):
        '''
        Installs Ruby and its dependencies. This method should be called upon if overriden in base classes, or Ruby won't work properly in the remote server.
        If you set a class property called version, that version of Ruby will be installed instead of 1.9.3.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import RubyRole

        class MySampleRole(Role):
            def provision(self):
                self.provision_role(RubyRole) # no need to call this if using with block.

        # or
        class MySampleRole(Role):
            def provision(self):
                RubyRole.version = "1.9.3"
                self.provision_role(RubyRole) # no need to call this if using with block.
                # now ruby 1.9.3 is installed.
        </pre>
        '''

        with self.using(AptitudeRole) as role:
            role.ensure_package_installed('g++')
            role.ensure_package_installed('make')
            role.ensure_package_installed('git-core')
            role.ensure_package_installed('libssl-dev')

        with settings(warn_only=True):
            result = self.execute('rvm --version', stdout=False)

        if not result or 'command not found' in result:
            self.execute('bash < <(curl -s https://rvm.beginrescueend.com/install/rvm)', sudo=True, stdout=False)

        with settings(warn_only=True):
            result = self.execute('rvm list | egrep %s' % self.version, stdout=False)

        if not result or 'command not found' in result :
            self.execute('rvm install %s' % self.version, sudo=True, stdout=True)
            return True

        return False


