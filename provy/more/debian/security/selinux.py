from provy.core import Role
from provy.more.debian.package.aptitude import AptitudeRole


class SELinuxRole(Role):
    LOAD_SCRIPT = 'some script'

    def provision(self):
        with self.using(AptitudeRole) as aptitude:
            aptitude.ensure_package_installed('selinux-basics')
            aptitude.ensure_package_installed('selinux-policy-default')
            aptitude.ensure_package_installed('selinux-utils')

        self.__complete_for_distro()

        self.execute('selinux-activate', stdout=False, sudo=True)

        self.log('''SELinux provisioned. Don't forget to reboot the server twice after provisioning (see http://wiki.debian.org/SELinux/Setup ).''')

    def __complete_for_distro(self):
        distro_info = self.get_distro_info()
        if distro_info.distributor_id.lower() == 'ubuntu':
            self.put_file(self.LOAD_SCRIPT, '/usr/share/initramfs-tools/scripts/init-bottom/_load_selinux_policy', sudo=True)
            self.execute('update-initramfs -u', stdout=False, sudo=True)
