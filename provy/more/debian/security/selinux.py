import fabric.api

from provy.core import Role
from provy.more.debian.package.aptitude import AptitudeRole

'''
Roles in this namespace are meant to provide `SELinux <http://selinuxproject.org/>`_ management utilities for Debian distributions.
'''


class SELinuxRole(Role):
    '''
    This role provides `SELinux <http://selinuxproject.org/>`_ utilities for Debian distributions.

    .. warning::

        If you're provisioning a Ubuntu server, it's highly recommended you use :class:`AppArmorRole <provy.more.debian.security.apparmor.AppArmorRole>` instead of this one.

        Please note that, for SELinux to be installed from scratch, you have to reboot the server so that it relabels all the files in the system for SELinux.
        So it's also highly recommended that you provision a server that has SELinux installed and activated already.

    Example:
    ::

        from provy.core import Role
        from provy.more.debian import SELinuxRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(SELinuxRole) as selinux:
                    selinux.ensure_login_mapping("foo")
                    selinux.map_login("foo", "staff_u")
                    selinux.map_role("foo", ["staff_r", "sysadm_r"])
    '''

    def __init__(self, prov, context):
        super(SELinuxRole, self).__init__(prov, context)

    def __distro_is_ubuntu(self):
        distro_info = self.get_distro_info()
        return distro_info.distributor_id.lower() == 'ubuntu'

    def provision(self):
        '''
        Installs SELinux, its dependencies, its utilities and the `Audit framework <https://www.wzdftpd.net/docs/selinux/audit.html>`_.

        Also, it activates SELinux after installing the packages, puts the system in enforce mode and puts the generic users into confinement for enhanced security.

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import SELinuxRole

            class MySampleRole(Role):
                def provision(self):
                    self.provision_role(SELinuxRole) # no need to call this if using with block.
        '''
        self.install_packages()
        self.activate()

        self.log('''SELinux provisioned. Don't forget to reboot the server if it didn't have SELinux already installed and activated.''')

    def install_packages(self):
        '''
        Installs the necessary packages to provision SELinux.

        This is executed during provisioning, so you can ignore this method.

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import SELinuxRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(SELinuxRole) as selinux:
                        selinux.install_packages() # no need to call this directly.
        '''
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
        '''
        Activates SELinux, confines generic users and puts the system into enforce mode.

        This is executed during provisioning, so you can ignore this method.

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import SELinuxRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(SELinuxRole) as selinux:
                        selinux.activate() # no need to call this directly.
        '''
        if not self.__distro_is_ubuntu():
            self.execute('selinux-activate', stdout=False, sudo=True)
        self.__confine_generic_users()
        self.enforce()

    def __confine_generic_users(self):
        self.execute("semanage login -m -s 'user_u' -r s0 __default__", stdout=False, sudo=True)

    def enforce(self):
        '''
        Puts the system into enforce mode.

        This is executed during provisioning, so you can ignore this method.

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import SELinuxRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(SELinuxRole) as selinux:
                        selinux.enforce() # no need to call this directly.
        '''
        with fabric.api.settings(warn_only=True):
            self.execute('setenforce 1', stdout=False, sudo=True)
            self.ensure_line('SELINUX=enforcing', '/etc/selinux/config', sudo=True)

    def ensure_login_mapping(self, user_or_group):
        '''
        Makes sure that a mapping exists for a login user to an SELinux user (if creating one now, sets it to the "user_u" SELinux user).

        :param user_or_group: The user or group to be changed. If providing a group, pass it with an "@" before the group name (like "@my-group").
        :type user_or_group: :class:`str`

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import SELinuxRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(SELinuxRole) as selinux:
                        selinux.ensure_login_mapping("foo")
                        selinux.ensure_login_mapping("@bar")
        '''
        with fabric.api.settings(warn_only=True):
            self.execute('semanage login -a %s' % user_or_group, stdout=False, sudo=True)

    def map_login(self, user_or_group, selinux_user):
        '''
        Maps a login user to an SELinux user.

        If the login user has no mapping yet, the role creates one.

        :param user_or_group: The user or group to be changed. If providing a group, pass it with an "@" before the group name (like "@my-group").
        :type user_or_group: :class:`str`
        :param selinux_user: The SELinux user to be referenced.
        :type selinux_user: :class:`str`

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import SELinuxRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(SELinuxRole) as selinux:
                        selinux.map_login("foo", "staff_u")
        '''
        self.ensure_login_mapping(user_or_group)
        self.execute('semanage login -m -s %s %s' % (selinux_user, user_or_group), stdout=False, sudo=True)

    def map_role(self, user_or_group, selinux_roles):
        '''
        Maps a login user to one or more SELinux roles.

        If the login user has no mapping yet, the role creates one.

        :param user_or_group: The user or group to be changed. If providing a group, pass it with an "@" before the group name (like "@my-group").
        :type user_or_group: :class:`str`
        :param selinux_roles: The roles to be referenced.
        :type selinux_roles: :class:`iterable`

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import SELinuxRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(SELinuxRole) as selinux:
                        selinux.map_role("foo", ["staff_r", "sysadm_r"])
        '''
        self.ensure_login_mapping(user_or_group)
        roles_as_string = ' '.join(selinux_roles)
        self.execute("semanage user -m -R '%s' %s" % (roles_as_string, user_or_group), stdout=False, sudo=True)
