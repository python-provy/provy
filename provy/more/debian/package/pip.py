#!/usr/bin/python
# -*- coding: utf-8 -*-

from fabric.api import settings

from provy.more.debian.package.aptitude import AptitudeRole

class PipRole(AptitudeRole):

    use_sudo = True

    def provision(self):
        super(PipRole, self).ensure_up_to_date()
        super(PipRole, self).ensure_package_installed('python-setuptools')
        super(PipRole, self).execute("easy_install pip", sudo=True)

    def is_package_installed(self, package_name, version=None):
        with settings(warn_only=True):
            return package_name in self.execute("pip freeze | grep %s..%s" % (package_name, version or ""), stdout=False, sudo=self.use_sudo)

    def ensure_package_installed(self, package_name, version=None):
        if not self.is_package_installed(package_name):
            self.log('%s is not installed (via pip)! Installing...' % package_name)
            self.execute('pip install %s' % package_name, stdout=True, sudo=self.use_sudo)
        
        if not self.is_package_installed(package_name, version):
            self.log('%s is not the version %s (via pip)! Installing specific version...' % (package_name, version))
            self.execute('pip install %s==%s' % (package_name, version), stdout=True, sudo=self.use_sudo)

        with settings(warn_only=True):
            self.log('%s is installed (via pip).' % self.execute("pip freeze | grep %s" % package_name, stdout=True, sudo=self.use_sudo))

    def ensure_up_to_date(self, package_name):
        if self.is_package_installed(package_name):
            self.log('%s is installed (via pip)! Updating...' % package_name)
            self.execute('pip install -U %s' % package_name, stdout=True, sudo=self.use_sudo)
        else:
            self.ensure_package_installed(package_name)
        self.log('%s is up to date (via pip).' % package_name)



