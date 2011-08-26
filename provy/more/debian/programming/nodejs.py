#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to provide Node.JS utility methods for Debian distributions.
'''

from fabric.api import settings

from provy.core import Role
from provy.more.debian import AptitudeRole

class NodeJsRole(Role):
    '''
    This role provides Node.JS utilities for Debian distributions.

    <em>Sample usage</em>
    <pre class="sh_python">
    from provy.core import Role
    from provy.more.debian import NodeJsRole

    class MySampleRole(Role):
        def provision(self):
            NodeJsRole.version = '0.4.11' # change to whatever version you need
            self.provision_role(NodeJsRole)
    </pre>
    '''
 
    version = '0.4.11'

    def provision(self):
        '''
        Installs Node.JS and its dependencies. This method should be called upon if overriden in base classes, or Node won't work properly in the remote server.
        If you set a class property called version, that version of Node.JS will be installed instead of 0.4.11.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import NodeJsRole

        class MySampleRole(Role):
            def provision(self):
                self.provision_role(NodeJsRole) # no need to call this if using with block.

        # or
        class MySampleRole(Role):
            def provision(self):
                NodeJsRole.version = '0.4.11'
                self.provision_role(NodeJsRole) # no need to call this if using with block.
                # now node js 0.4.11 is installed.
        </pre>
        '''
        with self.using(AptitudeRole) as role:
            role.ensure_package_installed('g++')
            role.ensure_package_installed('make')
            role.ensure_package_installed('git-core')
            role.ensure_package_installed('libssl-dev')

        result = None
        with settings(warn_only=True):
            result = self.execute('node --version', stdout=False)

        if not result or 'command not found' in result or not ('v%s' % self.version) in result:
            self.log('node.js not installed... installing...')
            self.ensure_dir('/tmp/downloads', sudo=True)
            self.execute('cd /tmp/downloads && wget http://nodejs.org/dist/node-v%s.tar.gz' % self.version, stdout=True, sudo=True)
            self.execute('cd /tmp/downloads && tar -xzvf node-v%s.tar.gz' % self.version, stdout=False, sudo=True)
            self.execute('cd /tmp/downloads/node-v%s && ./configure' % self.version, stdout=False, sudo=True)
            self.log('Compiling node.js...')
            self.execute('cd /tmp/downloads/node-v%s && make' % self.version, stdout=False, sudo=True)
            self.log('Installing node.js...')
            self.execute('cd /tmp/downloads/node-v%s && sudo make install' % self.version, stdout=False, sudo=True)
            self.log('node.js installed')
            return True
        return False


