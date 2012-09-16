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
    from provy.more.debian import RubyRole

    class MySampleRole(Role):
        def provision(self):
            self.provision_role(RubyRole)
    </pre>
    '''

    version = "1.9.2"
    patch = 290
    url = "http://ftp.ruby-lang.org/pub/ruby/1.9/ruby-%s-p%d.tar.gz"

    def __symlink_from_local(self):
        commands = "erb gem irb rake rdoc ri ruby testrb"

        for command in commands.split():
            self.remove_file('/usr/bin/%s' % command, sudo=True)
            self.remote_symlink('/usr/local/bin/%s' % command, '/usr/bin/%s' % command, sudo=True)

    def provision(self):
        '''
        Installs Ruby and its dependencies. This method should be called upon if overriden in base classes, or Ruby won't work properly in the remote server.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import RubyRole

        class MySampleRole(Role):
            def provision(self):
                self.provision_role(RubyRole) # no need to call this if using with block.

        </pre>
        '''
        with self.using(AptitudeRole) as role:
            for package in 'build-essential zlib1g zlib1g-dev libreadline5 libreadline5-dev libssl-dev libyaml-dev'.split():
                role.ensure_package_installed(package)

            with settings(warn_only=True):
                result = self.execute('ruby --version | egrep %sp%d' % (self.version, self.patch), stdout=False)

            if not result or 'command not found' in result.lower():
                self.log('ruby %sp%d not found! Installing...' % (self.version, self.patch))
                ruby_url = self.url % (self.version, self.patch)
                ruby_file = 'ruby-%s-p%d' % (self.version, self.patch)

                self.remove_file('/tmp/%s.tar.gz' % ruby_file, sudo=True)
                self.remove_dir('/tmp/%s' % ruby_file, sudo=True)

                self.execute('cd /tmp && wget %s && tar xzf %s.tar.gz && cd %s && ./configure && make && make install' %
                        (ruby_url, ruby_file, ruby_file), sudo=True, stdout=False)

                self.__symlink_from_local()

                self.log('ruby %sp%d installed!' % (self.version, self.patch))

