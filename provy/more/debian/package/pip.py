#!/usr/bin/python
# -*- coding: utf-8 -*-

import xmlrpclib

from fabric.api import settings

from provy.more.debian.package.aptitude import AptitudeRole

class PipRole(AptitudeRole):

    use_sudo = True

    def provision(self):
        super(PipRole, self).ensure_up_to_date()
        super(PipRole, self).ensure_package_installed('python-setuptools')
        super(PipRole, self).execute("easy_install pip", sudo=True, stdout=False)

    def is_pip_package_installed(self, package_name, version=None):
        with settings(warn_only=True):
            package_string = version and "%s==%s" % (package_name.lower(), version) or package_name
            return package_name in self.execute("pip freeze | tr '[A-Z]' '[a-z]' | grep %s" % package_string, stdout=False, sudo=self.use_sudo)

    def get_pip_package_remote_version(self, package_name):
        with settings(warn_only=True):
            result = self.execute("pip freeze | tr '[A-Z]' '[a-z]' | grep %s" % package_name.lower(), stdout=False, sudo=self.use_sudo)
            if result:
                package, version = result.split('==')
                return version

            return None

    def get_pip_package_latest_version(self, package_name):
        pypi = xmlrpclib.ServerProxy('http://pypi.python.org/pypi')
        available = pypi.package_releases(package_name)
        if not available:
            # Try to capitalize pkg name
            available = pypi.package_releases(package_name.capitalize())
                
        if not available:
            return False

        return available[0]

    def does_pip_package_has_update(self, package_name):
        remote_version = self.get_pip_package_remote_version(package_name)
        latest_version = self.get_pip_package_latest_version(package_name)

        return remote_version != latest_version

    def ensure_pip_package_installed(self, package_name, version=None):
        if not self.is_pip_package_installed(package_name):
            self.log('%s is not installed (via pip)! Installing...' % package_name)
            self.execute('pip install %s' % package_name, stdout=False, sudo=self.use_sudo)
            self.log('%s installed!' % package_name)
            return True

        if not self.is_pip_package_installed(package_name, version):
            self.log('%s version %s should be installed (via pip)! Rectifying that...' % (package_name, version))
            self.execute('pip install %s==%s' % (package_name, version), stdout=False, sudo=self.use_sudo)
            self.log('%s version %s installed!' % (package_name, version))
            return True

        return False

    def ensure_pip_package_up_to_date(self, package_name):
        if self.is_pip_package_installed(package_name) and self.does_pip_package_has_update(package_name):
            self.log('%s is installed (via pip)! Updating...' % package_name)
            self.execute('pip install -U --no-dependencies %s' % package_name, stdout=False, sudo=self.use_sudo)
            self.log('%s updated!' % package_name)
            return True
        else:
            self.ensure_pip_package_installed(package_name)
            return True

        self.log('%s is up to date (via pip).' % package_name)
        return False

