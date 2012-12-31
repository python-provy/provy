from provy.core import Role
from provy.more.debian.package.aptitude import AptitudeRole


class AppArmorRole(Role):
    def provision(self):
        with self.using(AptitudeRole) as aptitude:
            aptitude.ensure_package_installed('apparmor-profiles')
            aptitude.ensure_package_installed('apparmor-utils')
