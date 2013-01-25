from provy.core import Role
from provy.more.debian.package.aptitude import AptitudeRole

'''
Roles in this namespace are meant to provide `AppArmor <http://wiki.apparmor.net/>`_ management utilities for Debian distributions.
'''


class AppArmorRole(Role):
    '''
    This role provides `AppArmor <http://wiki.apparmor.net/>`_ utilities for Debian distributions.

    .. warning::

        If you're provisioning a Debian Wheezy server or older, it's highly recommended you use :class:`SELinuxRole <provy.more.debian.security.selinux.SELinuxRole>` instead of this one.

    Example:
    ::

        from provy.core import Role
        from provy.more.debian import AppArmorRole

        class MySampleRole(Role):
            def provision(self):

                with self.using(AppArmorRole) as apparmor:
                    apparmor.disable("/bin/ping", "/sbin/dhclient")

                with self.using(AppArmorRole) as apparmor:
                    apparmor.create("/usr/sbin/nginx", policy_groups=['networking', 'user-application'],
                                    read=["/srv/my-site"], read_and_write=["/srv/my-site/uploads"])
    '''

    def provision(self):
        '''
        Installs AppArmor profiles and utilities.

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import AppArmorRole

            class MySampleRole(Role):
                def provision(self):
                    self.provision_role(AppArmorRole) # no need to call this if using with block.
        '''
        with self.using(AptitudeRole) as aptitude:
            aptitude.ensure_package_installed('apparmor-profiles')
            aptitude.ensure_package_installed('apparmor-utils')

    def __execute_batch(self, command, executables):
        arguments = ' '.join(executables)
        command += ' %s' % arguments
        self.execute(command, stdout=False, sudo=True)

    def disable(self, *executables):
        '''
        Disables executables in AppArmor, removing them from confinement - that is, they will not be under vigilance anymore -.

        :param executables: The executables to change.
        :type executables: positional arguments of :class:`str`

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import AppArmorRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(AppArmorRole) as apparmor:
                        apparmor.disable("/bin/ping", "/sbin/dhclient")
        '''
        self.__execute_batch('aa-disable', executables)

    def complain(self, *executables):
        '''
        Puts the executables to complain mode - the policies are not enforced, but when they're broken, the action gets logged -.

        :param executables: The executables to change.
        :type executables: positional arguments of :class:`str`

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import AppArmorRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(AppArmorRole) as apparmor:
                        apparmor.complain("/bin/ping", "/sbin/dhclient")
        '''
        self.__execute_batch('aa-complain', executables)

    def enforce(self, *executables):
        '''
        Puts the executables to enforce mode - the policies are enforced, but only break attempts will be logged -.

        :param executables: The executables to change.
        :type executables: positional arguments of :class:`str`

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import AppArmorRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(AppArmorRole) as apparmor:
                        apparmor.enforce("/bin/ping", "/sbin/dhclient")
        '''
        self.__execute_batch('aa-enforce', executables)

    def audit(self, *executables):
        '''
        Puts the executables to audit mode - the policies are enforced, and all actions (legal and ilegal ones) will be logged -.

        :param executables: The executables to change.
        :type executables: positional arguments of :class:`str`

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import AppArmorRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(AppArmorRole) as apparmor:
                        apparmor.audit("/bin/ping", "/sbin/dhclient")
        '''
        self.__execute_batch('aa-audit', executables)

    def create(self, executable, template=None, policy_groups=None, abstractions=None, read=[], read_and_write=[]):
        '''
        Creates a profile for an executable. Please refer to the `aa-easyprof manual pages <http://manpages.ubuntu.com/manpages/precise/man8/aa-easyprof.8.html>`_ for more documentation.

        :param executable: The executable to be referenced by the profile being created.
        :type executable: :class:`str`
        :param template: If provided, will be used instead of the "default" one. Defaults to :data:`None`.
        :type template: :class:`str`
        :param policy_groups: If provided, use its items as the policy groups. Defaults to :data:`None`.
        :type policy_groups: :data:`iterable`
        :param abstractions: If provided, use its items as the abstractions. Defaults to :data:`None`.
        :type abstractions: :data:`iterable`
        :param read: If provided, paths to be readable by the executable. Defaults to :data:`[]` (empty list).
        :type read: :data:`iterable`
        :param read_and_write: If provided, paths to be readable and writable by the executable (there's no need to provide the "read" argument in this case). Defaults to :data:`[]` (empty list).
        :type read_and_write: :data:`iterable`

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import AppArmorRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(AppArmorRole) as apparmor:
                        apparmor.create("/usr/sbin/nginx", policy_groups=['networking', 'user-application'],
                                        read=["/srv/my-site"], read_and_write=["/srv/my-site/uploads"])
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
