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

    def audit(self, *executables):
        self.__execute_batch('aa-audit', executables)

    def create(self, executable, template=None, policy_groups=None, abstractions=None):
        command = 'aa-easyprof'
        if template is not None:
            command += ' -t %s' % template
        if policy_groups is not None:
            groups = ','.join(policy_groups)
            command += ' -p %s' % groups
        if abstractions is not None:
            abstr = ','.join(abstractions)
            command += ' -a %s' % abstr
        command += ' %s' % executable
        self.execute(command, stdout=False, sudo=True)
