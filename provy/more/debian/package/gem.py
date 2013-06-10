#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to provision packages installed via the `gem <http://docs.rubygems.org/>`_ package manager for Debian distributions.
'''

from fabric.api import settings

from provy.core import Role


UPDATE_ALTERNATIVES_COMMAND = """
update-alternatives --force --install /usr/bin/gem gem /usr/bin/gem{version} {priority} \
  --slave   /usr/share/man/man1/gem.1.gz gem.1.gz /usr/share/man/man1/gem{version}.1.gz
"""


class GemRole(Role):
    '''
    This role provides package management operations with `gem <http://docs.rubygems.org/>`_ within Debian distributions.

    If you wish to use a different Ruby version other than the default in provy, remember to set `version` and `priority` in the
    :class:`RubyRole <provy.more.debian.programming.ruby.RubyRole>` class.

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
        from provy.more.debian.programming.ruby import RubyRole
        self.provision_role(RubyRole)

        update_alternatives_command = UPDATE_ALTERNATIVES_COMMAND.format(
            version=RubyRole.version,
            priority=RubyRole.priority,
        )
        completion_command = 'ln - sf /etc/bash_completion.d/gem{version} /etc/alternatives/bash_completion_gem'.format(version=RubyRole.version)

        self.execute(update_alternatives_command, sudo=True)
        self.execute(completion_command, sudo=True)

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
