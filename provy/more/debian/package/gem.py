#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to provision packages installed via the `gem <http://docs.rubygems.org/>`_ package manager for Debian distributions.
'''

from fabric.api import settings

from provy.core import Role
from provy.more.debian.programming.ruby import RubyRole


class GemRole(Role):
    '''
    This role provides package management operations with `gem <http://docs.rubygems.org/>`_ within Debian distributions.

    Example:
    ::

        from provy.core import Role
        from provy.more.debian import GemRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(GemRole) as role:
                    role.ensure_package_installed('activerecord', version='3.1.1')
    '''

    use_sudo = True

    def provision(self):
        '''
        Installs gem dependencies. This method should be called upon if overriden in base classes, or gem won't work properly in the remote server.

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import PipRole

            class MySampleRole(Role):
                def provision(self):
                    self.provision_role(PipRole) # does not need to be called if using with block.
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
        Returns :data:`True` if the given package is installed via gem in the remote server, :data:`False` otherwise.

        :param package_name: Name of the package to verify.
        :type package_name: :class:`str`
        :param version: Version to check for. Defaults to :data:`None`, which makes it check for any version.
        :type version: :class:`str`
        :return: Wheter the package is installed or not.
        :rtype: :class:`bool`

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import GemRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(GemRole) as role:
                        if role.is_package_installed('activerecord', version='3.1.1'):
                            pass
        '''
        with settings(warn_only=True):
            package_string = self.execute("gem list --local | tr '[A-Z]' '[a-z]' | grep %s%s" %
                                          (package_name, version and '(%s)' % version or ''),
                                          stdout=False, sudo=self.use_sudo)
            return package_name in package_string

    def ensure_package_installed(self, package_name, version=None):
        '''
        Makes sure the package is installed with the specified version (latest if :data:`None` specified).
        This method does not verify and upgrade the package on subsequent provisions, though.

        :param package_name: Name of the package to install.
        :type package_name: :class:`str`
        :param version: If specified, installs this version of the package. Installs latest version otherwise.
        :type version: :class:`str`

        Example::
        ::

            from provy.core import Role
            from provy.more.debian import GemRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(GemRole) as role:
                        role.ensure_package_installed('activerecord', version='3.1.1')
        '''
        if not self.is_package_installed(package_name):
            version_str = version and '(%s)' % version or ''
            self.log('%s is not installed (via gem)! Installing...' % package_name)
            self.execute('gem install %s%s' % (package_name, version_str), stdout=False, sudo=self.use_sudo)
            self.log('%s installed!' % package_name)
            return True

        return False
