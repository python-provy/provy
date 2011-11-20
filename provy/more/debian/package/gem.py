#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to provision packages installed via the gem package manager for Debian distributions.
'''

from fabric.api import settings

from provy.core import Role
from provy.more.debian.package.aptitude import AptitudeRole
from provy.more.debian.programming.ruby import RubyRole


class GemRole(Role):
    '''
    This role provides package management operations with gem within Debian distributions.
    <em>Sample usage</em>
    <pre class="sh_python">
    from provy.core import Role
    from provy.more.debian import GemRole

    class MySampleRole(Role):
        def provision(self):
            with self.using(GemRole) as role:
                role.ensure_package_installed('activerecord', version='3.1.1')
    </pre>
    '''

    use_sudo = True

    def provision(self):
        '''
        Installs gem dependencies. This method should be called upon if overriden in base classes, or gem won't work properly in the remote server.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import PipRole

        class MySampleRole(Role):
            def provision(self):
                self.provision_role(PipRole) # does not need to be called if using with block.
        </pre>
        '''
        self.provision_role(RubyRole)

        with settings(warn_only=True):
            result = self.execute('gem --version', stdout=False)

        if not result or 'command not found' in result.lower():
            self.execute('cd /tmp && wget http://rubyforge.org/frs/download.php/45905/rubygems-1.3.1.tgz && tar xzf rubygems-1.3.1.tgz && cd rubygems-1.3.1 && ruby setup.rb', sudo=True, stdout=False)
            self.remove_file('/usr/bin/gem', sudo=True)
            self.remote_symlink('/usr/bin/gem1.9.1', '/usr/bin/gem', sudo=True)
            self.execute('gem update --system', sudo=True, stdout=False)

    def is_package_installed(self, package_name, version=None):
        '''
        Returns True if the given package is installed via gem in the remote server, False otherwise.
        <em>Parameters</em>
        package_name - Name of the package to verify.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import GemRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(GemRole) as role:
                    if role.is_package_installed('activerecord', version='3.1.1'):
                        # do something
        </pre>
        '''
        with settings(warn_only=True):
            package_string = self.execute("gem list --local | tr '[A-Z]' '[a-z]' | grep %s%s" % 
                    (package_name, version and '(%s)' % version or ''),  stdout=False, sudo=self.use_sudo)
            return package_name in package_string

    def ensure_package_installed(self, package_name, version=None):
        '''
        Makes sure the package is installed with the specified version (Latest if None specified). This method does not verify and upgrade the package on subsequent provisions, though.
        <em>Parameters</em>
        package_name - Name of the package to install.
        version - If specified, installs this version of the package. Installs latest version otherwise.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import GemRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(GemRole) as role:
                    role.ensure_package_installed('activerecord', version='3.1.1')
        </pre>
        '''
        if not self.is_package_installed(package_name):
            version_str = version and '(%s)' % version or ''
            self.log('%s is not installed (via gem)! Installing...' % package_name)
            self.execute('gem install %s%s' % (package_name, version_str), stdout=False, sudo=self.use_sudo)
            self.log('%s installed!' % package_name)
            return True

        return False
