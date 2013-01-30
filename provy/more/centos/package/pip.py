#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to provision packages installed via the `PIP <http://www.pip-installer.org/>`_ package manager for CentOS distributions.
'''

import xmlrpclib

from fabric.api import settings

from provy.core import Role
from provy.more.centos.package.yum import YumRole


class PipRole(Role):
    '''
    This role provides package management operations with `PIP <http://www.pip-installer.org/>`_ within CentOS distributions.

    Example:
    ::

        from provy.core import Role
        from provy.more.centos import PipRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(PipRole) as role:
                    role.ensure_package_installed('django', version='1.1.1')
    '''

    use_sudo = True

    def provision(self):
        '''
        Installs pip dependencies. This method should be called upon if overriden in base classes, or PIP won't work properly in the remote server.

        Example:
        ::

            class MySampleRole(Role):
                def provision(self):
                    self.provision_role(PipRole) # does not need to be called if using with block.
        '''

        with self.using(YumRole) as role:
            role.ensure_up_to_date()
            role.ensure_package_installed('python-setuptools')
            role.ensure_package_installed('python-devel')
            role.ensure_package_installed('gcc')
        self.execute("easy_install pip", sudo=True, stdout=False)

    def is_package_installed(self, package_name, version=None):
        '''
        Returns :data:`True` if the given package is installed via pip in the remote server, :data:`False` otherwise.

        :param package_name: Name of the package to verify
        :type package_name: :class:`str`
        :param version: Version to check for. Defaults to :data:`None`, which makes it check for any version.
        :type version: :class:`str`
        :return: Whether the package is installed or not.
        :rtype: :class:`bool`

        Example:
        ::

            class MySampleRole(Role):
                def provision(self):
                    with self.using(PipRole) as role:
                        if role.is_package_installed('django', version='1.1.1'):
                            pass
        '''

        with settings(warn_only=True):
            package_string = version and "%s==%s" % (package_name.lower(), version) or package_name
            return package_name in self.execute("pip freeze | tr '[A-Z]' '[a-z]' | grep %s" % package_string, stdout=False, sudo=self.use_sudo)

    def get_package_remote_version(self, package_name):
        '''
        Returns the version of the package currently installed via PIP in the remote server. If package is not installed, returns :data:`None`.

        :param package_name: Name of the package to verify
        :type package_name: :class:`str`
        :return: The package version.
        :rtype: :class:`str`

        Example:
        ::

            class MySampleRole(Role):
                def provision(self):
                    with self.using(PipRole) as role:
                        version = role.get_package_remote_version('django')
                        if version and version == '1.1.1':
                            pass
        '''
        with settings(warn_only=True):
            result = self.execute("pip freeze | tr '[A-Z]' '[a-z]' | grep %s" % package_name.lower(), stdout=False, sudo=self.use_sudo)
            if result:
                package, version = result.split('==')
                return version

            return None

    def get_package_latest_version(self, package_name):
        '''
        Returns the latest available version of the package at the Python Package Index. If package is not available, returns :data:`None`.

        :param package_name: Name of the package to verify
        :type package_name: :class:`str`
        :return: The package version.
        :rtype: :class:`str`

        Example:
        ::

            class MySampleRole(Role):
                def provision(self):
                    with self.using(PipRole) as role:
                        version = role.get_package_remote_version('django')
                        latest = role.get_package_latest_version('django')
                        if version != latest:
                            pass
                            # this check is not needed if you use ensure_package_up_to_date.
        '''
        pypi = xmlrpclib.ServerProxy('http://pypi.python.org/pypi')
        available = pypi.package_releases(package_name)
        if not available:
            # Try to capitalize pkg name
            available = pypi.package_releases(package_name.capitalize())

        if not available:
            return False

        return available[0]

    def package_can_be_updated(self, package_name):
        '''
        Returns :data:`True` if there is an update for the given package in the Python Package Index, False otherwise.

        :param package_name: Name of the package to verify
        :type package_name: :class:`str`
        :return: Whether the package can be updated.
        :rtype: :class:`bool`

        Example:
        ::

            class MySampleRole(Role):
                def provision(self):
                    with self.using(PipRole) as role:
                        if role.package_can_be_updated('django'):
                            pass
                            # this check is not needed if you use ensure_package_up_to_date.
        '''
        remote_version = self.get_package_remote_version(package_name)
        latest_version = self.get_package_latest_version(package_name)

        return remote_version != latest_version

    def ensure_package_installed(self, package_name, version=None):
        '''
        Makes sure the package is installed with the specified version (latest if :data:`None` specified).
        This method does not verify and upgrade the package on subsequent provisions, though. Use :meth:`ensure_package_up_to_date` for this purpose instead.

        :param package_name: Name of the package to install.
        :type package_name: :class:`str`
        :param version: If specified, installs this version of the package. Installs latest version otherwise. You can use >= or <= before version number to ensure package version.
        :type version: :class:`str`
        :return: Whether the package had to be installed or not.
        :rtype: :class:`bool`

        Example:
        ::

            class MySampleRole(Role):
                def provision(self):
                    with self.using(PipRole) as role:
                        role.ensure_package_installed('django', version='1.1.1')
        '''
        if version and not self.is_package_installed(package_name, version):
            self.log('%s version %s should be installed (via pip)! Rectifying that...' % (package_name, version))
            self.execute('pip install %s==%s' % (package_name, version), stdout=False, sudo=self.use_sudo)
            self.log('%s version %s installed!' % (package_name, version))
            return True
        elif not self.is_package_installed(package_name):
            self.log('%s is not installed (via pip)! Installing...' % package_name)
            self.execute('pip install %s' % package_name, stdout=False, sudo=self.use_sudo)
            self.log('%s installed!' % package_name)
            return True

        return False

    def ensure_package_up_to_date(self, package_name):
        '''
        Makes sure the package is installed and up-to-date with the latest version.
        This method verifies if there is a newer version for this package every time the server is provisioned. If a new version is found, it is installed.

        :param package_name: Name of the package to install.
        :type package_name: :class:`str`

        Example:
        ::

            class MySampleRole(Role):
                def provision(self):
                    with self.using(PipRole) as role:
                        role.ensure_package_is_up_to_date('django')
        '''
        if self.is_package_installed(package_name) and self.package_can_be_updated(package_name):
            self.log('%s is installed (via pip)! Updating...' % package_name)
            self.execute('pip install -U --no-dependencies %s' % package_name, stdout=False, sudo=self.use_sudo)
            self.log('%s updated!' % package_name)
            return True
        else:
            self.ensure_package_installed(package_name)
            return True

        self.log('%s is up to date (via pip).' % package_name)
        return False
