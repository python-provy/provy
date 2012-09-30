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

    def ensure_site(self, name, file, options={}):
        available = '/etc/apache2/sites-available/%s' % name
        enabled = '/etc/apache2/sites-enabled/%s' % name

        self.update_file(file, available, options=options, sudo=True)
        self.remote_symlink(from_file=available, to_file=enabled, sudo=True)
        self.execute('service apache2 reload', sudo=True)
