import fabric.api

from provy.core import Role
from provy.more.debian.package.aptitude import AptitudeRole


class SELinuxRole(Role):
    def __init__(self, prov, context):
        super(SELinuxRole, self).__init__(prov, context)
        self.__is_ubuntu = None

    def __distro_is_ubuntu(self):
        if self.__is_ubuntu is None:
            distro_info = self.get_distro_info()
            self.__is_ubuntu = distro_info.distributor_id.lower() == 'ubuntu'
        return self.__is_ubuntu

    def provision(self):
        self.install_packages()
        self.activate()

        self.log('''SELinux provisioned. Don't forget to reboot the server if it didn't have SELinux already installed and activated.''')

    def install_packages(self):
        with self.using(AptitudeRole) as aptitude:
            if self.__distro_is_ubuntu():
                aptitude.ensure_package_installed('selinux')
            else:
                aptitude.ensure_package_installed('selinux-basics')
                aptitude.ensure_package_installed('selinux-policy-default')
            aptitude.ensure_package_installed('selinux-utils')
            aptitude.ensure_package_installed('auditd')
            aptitude.ensure_package_installed('audispd-plugins')

    def activate(self):
        if not self.__distro_is_ubuntu():
            self.execute('selinux-activate', stdout=False, sudo=True)
        self.enforce()

    def enforce(self):
        with fabric.api.settings(warn_only=True):
            self.execute('setenforce 1', stdout=False, sudo=True)
            self.ensure_line('SELINUX=enforcing', '/etc/selinux/config', sudo=True)
