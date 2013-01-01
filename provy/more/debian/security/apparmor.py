from provy.core import Role
from provy.more.debian.package.aptitude import AptitudeRole


class AppArmorRole(Role):
    def provision(self):
        with self.using(AptitudeRole) as aptitude:
            aptitude.ensure_package_installed('apparmor-profiles')
            aptitude.ensure_package_installed('apparmor-utils')

    def enable(self, profile):
        self.execute('rm -f /etc/apparmor.d/disable/%s' % profile, stdout=False, sudo=True)
        self.execute('apparmor_parser -r /etc/apparmor.d/%s' % profile, stdout=False, sudo=True)

    def disable(self, profile):
        self.execute('ln -s /etc/apparmor.d/%s /etc/apparmor.d/disable/' % profile, stdout=False, sudo=True)
        self.execute('apparmor_parser -R /etc/apparmor.d/%s' % profile, stdout=False, sudo=True)

    def complain(self, *executables):
        command = 'aa-complain'
        for executable in executables:
            command += ' %s' % executable
        self.execute(command, stdout=False, sudo=True)
