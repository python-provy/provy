from provy.core import Role
from provy.more.debian.package.aptitude import AptitudeRole


class AppArmorRole(Role):
    def provision(self):
        '''
        Installs AppArmor profiles and utilities.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import AppArmorRole

        class MySampleRole(Role):
            def provision(self):
                self.provision_role(AppArmorRole) # no need to call this if using with block.

        </pre>
        '''
        with self.using(AptitudeRole) as aptitude:
            aptitude.ensure_package_installed('apparmor-profiles')
            aptitude.ensure_package_installed('apparmor-utils')

    def __execute_batch(self, command, executables):
        for executable in executables:
            command += ' %s' % executable
        self.execute(command, stdout=False, sudo=True)

    def disable(self, *executables):
        '''
        Disables executables in AppArmor, removing them from confinement - that is, they will not be under vigilance anymore -.
        <em>Parameters</em>
        *executables - the executables to change.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import AppArmorRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(AppArmorRole) as apparmor:
                    apparmor.disable("/bin/ping", "/sbin/dhclient")

        </pre>
        '''
        self.__execute_batch('aa-disable', executables)

    def complain(self, *executables):
        '''
        Puts the executables to complain mode - the policies are not enforced, but when they're broken, the action gets logged -.
        <em>Parameters</em>
        *executables - the executables to change.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import AppArmorRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(AppArmorRole) as apparmor:
                    apparmor.complain("/bin/ping", "/sbin/dhclient")

        </pre>
        '''
        self.__execute_batch('aa-complain', executables)

    def enforce(self, *executables):
        '''
        Puts the executables to enforce mode - the policies are enforced, but only break attempts will be logged -.
        <em>Parameters</em>
        *executables - the executables to change.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import AppArmorRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(AppArmorRole) as apparmor:
                    apparmor.enforce("/bin/ping", "/sbin/dhclient")

        </pre>
        '''
        self.__execute_batch('aa-enforce', executables)

    def audit(self, *executables):
        '''
        Puts the executables to audit mode - the policies are enforced, and all actions (legal and ilegal ones) will be logged -.
        <em>Parameters</em>
        *executables - the executables to change.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import AppArmorRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(AppArmorRole) as apparmor:
                    apparmor.audit("/bin/ping", "/sbin/dhclient")

        </pre>
        '''
        self.__execute_batch('aa-audit', executables)

    def create(self, executable, template=None, policy_groups=None, abstractions=None, read=[], read_and_write=[]):
        '''
        Creates a profile for an executable. Please refer to the "aa-easyprof" manual pages for more documentation.
        <em>Parameters</em>
        executable - the executable to be referenced by the profile being created.
        template - if provided, will be used instead of the "default" one. Defaults to None.
        policy_groups - if an iterable is provided, use its items as the policy groups. Defaults to None.
        abstractions - if an iterable is provided, use its items as the abstractions. Defaults to None.
        read - if provided, paths to be readable by the executable. Defaults to [] (empty list).
        read_and_write - if provided, paths to be readable and writable by the executable (there's no need to provide the "read" argument in this case). Defaults to [] (empty list).
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import AppArmorRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(AppArmorRole) as apparmor:
                    apparmor.create("/usr/sbin/nginx", policy_groups=['networking', 'user-application'], read=["/srv/my-site"], read_and_write=["/srv/my-site/uploads"])

        </pre>
        '''
        command = 'aa-easyprof'
        if template is not None:
            command += ' -t %s' % template
        if policy_groups is not None:
            groups = ','.join(policy_groups)
            command += ' -p %s' % groups
        if abstractions is not None:
            abstr = ','.join(abstractions)
            command += ' -a %s' % abstr
        for path in read:
            command += ' -r %s' % path
        for path in read_and_write:
            command += ' -w %s' % path
        command += ' %s' % executable
        self.execute(command, stdout=False, sudo=True)