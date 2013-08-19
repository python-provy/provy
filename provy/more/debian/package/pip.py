#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to provision packages installed via the `PIP <http://www.pip-installer.org/>`_ package manager for Debian distributions.
'''

from fabric.api import settings

from provy.core import Role
from provy.more.debian.package.aptitude import AptitudeRole

import xmlrpclib


class PipRole(Role):
    '''
    This role provides package management operations with `PIP <http://www.pip-installer.org/>`_ within Debian distributions.

    By default, all commands executed with this role will be executed with sudo, unless you set a different user (refer to the :meth:`set_user` method below).

    You can also change the class parameters below in the class directly to have a global effect (use carefully!).

    :var use_sudo: If :data:`False`, the packages will be installed as normal user. Defaults to :data:`True`.
    :type use_sudo: :class:`bool`
    :var user: User through which the packages will be installed. Defaults to :data:`None`, which means that, using together with the default use_sudo, will install packages globally.
    :type user: :class:`str`

    Example:
    ::

        from provy.core import Role
        from provy.more.debian import PipRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(PipRole) as role:
                    role.ensure_package_installed('django', version='1.1.1')
    '''

    use_sudo = True
    user = None

    def provision(self):
        '''
        Installs pip dependencies. This method should be called upon if overriden in base classes, or PIP won't work properly in the remote server.

        Example:
        ::

            class MySampleRole(Role):
                def provision(self):
                    self.provision_role(PipRole) # does not need to be called if using with block.
        '''
        with self.using(AptitudeRole) as role:
            role.ensure_up_to_date()
            role.ensure_package_installed('python-setuptools')
            role.ensure_package_installed('python-dev')
        self.execute("easy_install pip", sudo=True, stdout=False, user=None)

    def extract_package_data_from_input(self, input_line):
        package_constraint = None
        input_line = input_line.strip()
        package_info = {
            "name": input_line
        }

        if input_line.startswith("-e") and "#egg=" in input_line:
            data = input_line.split("#egg=")
            if len(data) > 0:
                package_info["name"] = data[1]
        elif "==" in input_line:
            package_constraint = "=="
        elif '>=' in input_line:
            package_constraint = ">="

        if package_constraint:
            package_info['version_constraint'] = package_constraint
            data = input_line.split(package_constraint)
            if len(data) > 1:
                package_info["name"] = data[0]
                package_info["version"] = data[1]

        return package_info

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
            package_info = self.extract_package_data_from_input(package_name)
            if not version:
                package_name = package_info['name']
            package_string = self.execute("pip freeze | tr '[A-Z]' '[a-z]' | grep %s" % package_name, stdout=False, sudo=self.use_sudo, user=self.user)
            if package_name in package_string:
                installed_version = package_string.split('==')[-1]
                if 'version' in package_info:
                    if '>=' == package_info['version_constraint']:
                        if installed_version < package_info['version']:
                            return False
                elif version and installed_version != version:
                    return False
                return True

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
            result = self.execute("pip freeze | tr '[A-Z]' '[a-z]' | grep %s" % package_name.lower(), stdout=False, sudo=self.use_sudo, user=self.user)
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
            return None

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
        if version:
            package_info = self.extract_package_data_from_input(version)
            version_constraint = package_info.get('version_constraint', '==')
            version = package_info.get('version', version)
            if not self.is_package_installed(package_name, version):
                self.log('%s version %s should be installed (via pip)! Rectifying that...' % (package_name, version))
                self.execute('pip install %s%s%s' % (package_name, version_constraint, version), stdout=False, sudo=self.use_sudo, user=self.user)
                self.log('%s version %s installed!' % (package_name, version))
                return True
        elif not self.is_package_installed(package_name):
            self.log('%s is not installed (via pip)! Installing...' % package_name)
            self.execute('pip install %s' % package_name, stdout=False, sudo=self.use_sudo, user=self.user)
            self.log('%s installed!' % package_name)
            return True

        return False

    def ensure_requeriments_installed(self, requeriments_file_name):
        '''
        .. warning:: Deprecated. Please use :meth:`ensure_requirements_installed` instead. (Will be removed in 0.7.0)

        Makes sure the requirements file provided is installed.

        :param requeriments_file_name: Path to the requirements file (can be provided as absolute path or relative to the directory where provy is run from).
        :type requeriments_file_name: :class:`str`

        Example:
        ::

            class MySampleRole(Role):
                def provision(self):
                    with self.using(PipRole) as role:
                        role.ensure_requeriments_installed('/path/to/requirements.txt')
        '''
        self.log('"ensure_requeriments_installed" is deprecated, please use "ensure_requirements_installed" instead.')
        self.ensure_requirements_installed(requeriments_file_name)

    def ensure_requirements_installed(self, requirements_file_name):
        '''
        Makes sure the requirements file provided is installed.

        :param requirements_file_name: Path to the requirements file (can be provided as absolute path or relative to the directory where provy is run from).
        :type requirements_file_name: :class:`str`

        Example:
        ::

            class MySampleRole(Role):
                def provision(self):
                    with self.using(PipRole) as role:
                        role.ensure_requirements_installed('/path/to/requirements.txt')
        '''

        with open(requirements_file_name, 'r') as requirements_file:
            for requirement in requirements_file.readlines():
                self.ensure_package_installed(requirement.strip())

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
        is_installed = self.is_package_installed(package_name)

        if is_installed and self.package_can_be_updated(package_name):
            self.log('%s is installed (via pip)! Updating...' % package_name)
            self.execute('pip install -U --no-dependencies %s' % package_name, stdout=False, sudo=self.use_sudo, user=self.user)
            self.log('%s updated!' % package_name)
            return True
        elif not is_installed:
            self.ensure_package_installed(package_name)
            return True

        self.log('%s is up to date (via pip).' % package_name)
        return False

    def set_user(self, user):
        '''
        Prepares the pip role instance to run its commands as a specific user.

        :param user: The username with which the role should run its commands.
        :type user: :class:`str`

        Example:
        ::

            class MySampleRole(Role):
                def provision(self):
                    with self.using(PipRole) as role:
                        role.ensure_package_installed('django') # runs as sudo
                        role.set_user('johndoe')
                        role.ensure_package_installed('django') # runs as "johndoe" user
        '''

        self.user = user
        self.use_sudo = False

    def set_sudo(self):
        '''
        Prepares the pip role instance to run its commands with sudo; This is useful when you had previously set a user, and want it to run back as sudo.

        Example:
        ::

            class MySampleRole(Role):
                def provision(self):
                    with self.using(PipRole) as role:
                        role.ensure_package_installed('django') # runs as sudo
                        role.set_user('johndoe')
                        role.ensure_package_installed('django') # runs as "johndoe" user
                        role.set_sudo()
                        role.ensure_package_installed('django') # runs as sudo
        '''

        self.user = None
        self.use_sudo = True
