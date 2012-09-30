# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to provide Apache HTTP server utility methods for Debian distributions.
'''

from provy.core.roles import Role
from provy.more.debian import AptitudeRole


class ApacheRole(Role):
    def provision(self):
        with self.using(AptitudeRole) as aptitude:
            aptitude.ensure_package_installed('apache2')

    def ensure_mod(self, mod):
        with self.using(AptitudeRole) as aptitude:
            aptitude.ensure_package_installed('libapache2-mod-%s' % mod)

        self.execute('a2enmod %s' % mod, sudo=True)

    def create_site(self, name, template, options={}):
        available = '/etc/apache2/sites-available/%s' % name
        enabled = '/etc/apache2/sites-enabled/%s' % name

        self.update_file(template, available, options=options, sudo=True)
        self.remote_symlink(from_file=available, to_file=enabled, sudo=True)
        self.execute('service apache2 restart', sudo=True)
