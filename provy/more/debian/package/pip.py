#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to provision packages installed via the PIP package manager for Debian distributions.
'''

from fabric.api import settings

from provy.core import Role
from provy.more.debian.package.aptitude import AptitudeRole

import re
import xmlrpclib


class PipRole(Role):
    '''
    This role provides package management operations with PIP within Debian distributions.
    <em>Sample usage</em>
    <pre class="sh_python">
    from provy.core import Role
    from provy.more.debian import PipRole

    class MySampleRole(Role):
        def provision(self):
            with self.using(PipRole) as role:
                role.ensure_package_installed('django', version='1.1.1')
    </pre>
    '''

    use_sudo = True

    def provision(self):
        '''
        Installs pip dependencies. This method should be called upon if overriden in base classes, or PIP won't work properly in the remote server.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import PipRole

        class MySampleRole(Role):
            def provision(self):
                self.provision_role(PipRole) # does not need to be called if using with block.
        </pre>
        '''
        with self.using(AptitudeRole) as role:
            role.ensure_up_to_date()
            role.ensure_package_installed('python-setuptools')
            role.ensure_package_installed('python-dev')
        self.execute("easy_install pip", sudo=True, stdout=False)

    def extract_package_data_from_input(self, input_line):
        package_constraint = None
        input_line = input_line.strip()
        package_info = {
            "name" : input_line
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
        Returns True if the given package is installed via pip in the remote server, False otherwise.
        <em>Parameters</em>
        package_name - Name of the package to verify.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import PipRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(PipRole) as role:
                    if role.is_package_installed('django', version='1.1.1'):
                        # do something
        </pre>
        '''
        with settings(warn_only=True):
            package_info = self.extract_package_data_from_input(package_name)
            if not version:
                package_name = package_info['name']
            #package_string = version and "%s==%s" % (package_name.lower(), version) or package_name
            package_string = self.execute("pip freeze | tr '[A-Z]' '[a-z]' | grep %s" % package_name, stdout=False, sudo=self.use_sudo)
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
        Returns the version of the package currently installed via PIP in the remote server. If package is not installed, returns None.
        <em>Parameters</em>
        package_name - Name of the package to verify.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import PipRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(PipRole) as role:
                    version = role.get_package_remote_version('django')
                    if version and version == '1.1.1':
                        # do something
        </pre>
        '''
        with settings(warn_only=True):
            result = self.execute("pip freeze | tr '[A-Z]' '[a-z]' | grep %s" % package_name.lower(), stdout=False, sudo=self.use_sudo)
            if result:
                package, version = result.split('==')
                return version

            return None

    def get_package_latest_version(self, package_name):
        '''
        Returns the latest available version of the package at the Python Package Index. If package is not available, returns None.
        <em>Parameters</em>
        package_name - Name of the package to verify.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import PipRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(PipRole) as role:
                    version = role.get_package_remote_version('django')
                    latest = role.get_package_latest_version('django')
                    if version != latest:
                        # do something
                        # this check is not needed if you use ensure_package_up_to_date.
        </pre>
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
        Returns True if there is an update for the given package in the Python Package Index, False otherwise.
        <em>Parameters</em>
        package_name - Name of the package to verify.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import PipRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(PipRole) as role:
                    if role.package_can_be_updated('django'):
                        # do something
                        # this check is not needed if you use ensure_package_up_to_date.
        </pre>
        '''
        remote_version = self.get_package_remote_version(package_name)
        latest_version = self.get_package_latest_version(package_name)

        return remote_version != latest_version

    def ensure_package_installed(self, package_name, version=None):
        '''
        Makes sure the package is installed with the specified version (Latest if None specified). This method does not verify and upgrade the package on subsequent provisions, though. Use <em>ensure_package_up_to_date</em> for this purpose instead.
        <em>Parameters</em>
        package_name - Name of the package to install.
        version - If specified, installs this version of the package. Installs latest version otherwise. You can use >= or <= before version number to ensure package version.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import PipRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(PipRole) as role:
                    role.ensure_package_installed('django', version='1.1.1')
        </pre>
        '''
        if version:
            package_info = self.extract_package_data_from_input(version)
            version_constraint = 'version_constraint' in package_info and package_info['version_constraint'] or '=='
            version = 'version' in package_info and package_info['version'] or version
            if not self.is_package_installed(package_name, version):
                self.log('%s version %s should be installed (via pip)! Rectifying that...' % (package_name, version))
                self.execute('pip install %s%s%s' % (package_name, version_constraint, version), stdout=False, sudo=self.use_sudo)
                self.log('%s version %s installed!' % (package_name, version))
                return True
        elif not self.is_package_installed(package_name):
            self.log('%s is not installed (via pip)! Installing...' % package_name)
            self.execute('pip install %s' % package_name, stdout=False, sudo=self.use_sudo)
            self.log('%s installed!' % package_name)
            return True

        return False

    def ensure_requeriments_installed(self, requeriments_file_name):
        with open(requeriments_file_name, 'r') as requeriments_file:
            for requeriment in requeriments_file.readlines():
                self.ensure_package_installed(requeriment.strip())

    def ensure_package_up_to_date(self, package_name):
        '''
        Makes sure the package is installed and up-to-date with the latest version. This method verifies if there is a newer version for this package every time the server is provisioned. If a new version is found, it is installed.
        <em>Parameters</em>
        package_name - Name of the package to install.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import PipRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(PipRole) as role:
                    role.ensure_package_is_up_to_date('django')
        </pre>
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
