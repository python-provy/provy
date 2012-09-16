from provy.core import Role
from provy.more.debian.package.aptitude import AptitudeRole


class PHPRole(Role):
    def provision(self):
        with self.using(AptitudeRole) as aptitude:
            aptitude.ensure_package_installed('php5')
            aptitude.ensure_package_installed('php5-dev')
            aptitude.ensure_package_installed('php-pear')