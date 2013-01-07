from provy.core import Role
from provy.more.debian.package.aptitude import AptitudeRole


class SELinuxRole(Role):
    LOAD_SCRIPT = 'some script'

    def provision(self):
        distro_info = self.get_distro_info()
        with self.using(AptitudeRole) as aptitude:
            if distro_info.distributor_id.lower() == 'ubuntu':
                aptitude.ensure_package_installed('selinux')
            else:
                aptitude.ensure_package_installed('selinux-basics')
                aptitude.ensure_package_installed('selinux-policy-default')
            aptitude.ensure_package_installed('selinux-utils')

        if distro_info.distributor_id.lower() != 'ubuntu':
            self.execute('selinux-activate', stdout=False, sudo=True)

        self.log('''SELinux provisioned. Don't forget to reboot the server twice after provisioning (see http://wiki.debian.org/SELinux/Setup ).''')
