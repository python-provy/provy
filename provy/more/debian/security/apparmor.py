from provy.core import Role
from provy.more.debian.package.aptitude import AptitudeRole


class AppArmorRole(Role):
    def provision(self):
        with self.using(AptitudeRole) as aptitude:
            aptitude.ensure_package_installed('apparmor-profiles')
            aptitude.ensure_package_installed('apparmor-utils')

    def __execute_batch(self, command, executables):
        for executable in executables:
            command += ' %s' % executable
        self.execute(command, stdout=False, sudo=True)

    def disable(self, *executables):
        self.__execute_batch('aa-disable', executables)

    def complain(self, *executables):
        self.__execute_batch('aa-complain', executables)

    def enforce(self, *executables):
        self.__execute_batch('aa-enforce', executables)
