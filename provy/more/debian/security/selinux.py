from provy.core import Role
from provy.more.debian.package.aptitude import AptitudeRole


class SELinuxRole(Role):
    def provision(self):
        distro_info = self.get_distro_info()
        is_ubuntu = distro_info.distributor_id.lower() == 'ubuntu'

        with self.using(AptitudeRole) as aptitude:
            self.__install_packages(is_ubuntu, aptitude)

        if not is_ubuntu:
            self.execute('selinux-activate', stdout=False, sudo=True)

        self.log('''SELinux provisioned. Don't forget to reboot the server twice after provisioning (see http://wiki.debian.org/SELinux/Setup ).''')

    def __install_packages(self, is_ubuntu, aptitude):
        if is_ubuntu:
            aptitude.ensure_package_installed('selinux')
        else:
            aptitude.ensure_package_installed('selinux-basics')
            aptitude.ensure_package_installed('selinux-policy-default')
        aptitude.ensure_package_installed('selinux-utils')
        aptitude.ensure_package_installed('auditd')
        aptitude.ensure_package_installed('audispd-plugins')
