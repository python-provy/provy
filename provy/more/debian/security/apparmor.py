from provy.core import Role
from provy.more.debian.package.aptitude import AptitudeRole


class AppArmorRole(Role):
    def provision(self):
        with self.using(AptitudeRole) as aptitude:
            aptitude.ensure_package_installed('apparmor-profiles')
            aptitude.ensure_package_installed('apparmor-utils')

    def enable_profile(self, profile):
        self.execute('rm -f /etc/apparmor.d/disable/some.profile', stdout=False, sudo=True)
        self.execute('apparmor_parser -r /etc/apparmor.d/some.profile', stdout=False, sudo=True)
