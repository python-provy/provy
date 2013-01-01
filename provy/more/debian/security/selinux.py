from provy.core import Role
from provy.more.debian.package.aptitude import AptitudeRole


class SELinuxRole(Role):
    def provision(self):
        with self.using(AptitudeRole) as aptitude:
            aptitude.ensure_package_installed('selinux-basics')
            aptitude.ensure_package_installed('selinux-policy-default')
            aptitude.ensure_package_installed('selinux-utils')
