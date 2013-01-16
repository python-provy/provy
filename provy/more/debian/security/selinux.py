import fabric.api

from provy.core import Role
from provy.more.debian.package.aptitude import AptitudeRole

'''
Roles in this namespace are meant to provide SELinux management utilities for Debian distributions.
'''


class SELinuxRole(Role):
    '''
    This role provides SELinux utilities for Debian distributions.
    If you're provisioning a Ubuntu server, it's highly recommended you use AppArmorRole instead of this one.
    Please note that, for SELinux to be installed from scratch, you have to reboot the server so that it relabels all the files in the system for SELinux. So it's also highly recommended that you provision a server that has SELinux installed and activated already.
    <em>Sample usage</em>
    <pre class="sh_python">
    from provy.core import Role
    from provy.more.debian import SELinuxRole

    class MySampleRole(Role):
        def provision(self):
    </pre>
    '''

    def __init__(self, prov, context):
        super(SELinuxRole, self).__init__(prov, context)
        self.__is_ubuntu = None

    def __distro_is_ubuntu(self):
        if self.__is_ubuntu is None:
            distro_info = self.get_distro_info()
            self.__is_ubuntu = distro_info.distributor_id.lower() == 'ubuntu'
        return self.__is_ubuntu

    def provision(self):
        '''
        Installs SELinux, its dependencies, its utilities and the Audit framework.
        Also, it activates SELinux after installing the packages, puts the system in enforce mode and puts the generic users into confinement for enhanced security.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import SELinuxRole

        class MySampleRole(Role):
            def provision(self):
                self.provision_role(SELinuxRole) # no need to call this if using with block.

        </pre>
        '''
        self.install_packages()
        self.activate()

        self.log('''SELinux provisioned. Don't forget to reboot the server if it didn't have SELinux already installed and activated.''')

    def install_packages(self):
        '''
        Installs the necessary packages to provision SELinux.
        This is executed during provisioning, so you can ignore this method.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import SELinuxRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(SELinuxRole) as selinux:
                    selinux.install_packages() # no need to call this directly.

        </pre>
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
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import SELinuxRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(SELinuxRole) as selinux:
                    selinux.activate() # no need to call this directly.

        </pre>
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
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import SELinuxRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(SELinuxRole) as selinux:
                    selinux.enforce() # no need to call this directly.

        </pre>
        '''
        with fabric.api.settings(warn_only=True):
            self.execute('setenforce 1', stdout=False, sudo=True)
            self.ensure_line('SELINUX=enforcing', '/etc/selinux/config', sudo=True)

    def ensure_login_mapping(self, user_or_group):
        '''
        Makes sure that a mapping exists for a login user to an SELinux user (if creating one now, sets it to the "user_u" SELinux user).
        <em>Parameters</em>
        user_or_group - The user or group to be changed. If providing a group, pass it with an "@" before the group name (like "@my-group").
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import SELinuxRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(SELinuxRole) as selinux:
                    selinux.ensure_login_mapping("foo")
                    selinux.ensure_login_mapping("@bar")

        </pre>
        '''
        with fabric.api.settings(warn_only=True):
            self.execute('semanage login -a %s' % user_or_group, stdout=False, sudo=True)

    def map_login(self, user_or_group, selinux_user):
        '''
        Maps a login user to an SELinux user.
        If the login user has no mapping yet, the role creates one.
        <em>Parameters</em>
        user_or_group - The user or group to be changed. If providing a group, pass it with an "@" before the group name (like "@my-group").
        selinux_user - The SELinux user to be referenced.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import SELinuxRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(SELinuxRole) as selinux:
                    selinux.map_login("foo", "staff_u")

        </pre>
        '''
        self.ensure_login_mapping(user_or_group)
        self.execute('semanage login -m -s %s %s' % (selinux_user, user_or_group), stdout=False, sudo=True)

    def map_role(self, user_or_group, selinux_roles):
        '''
        Maps a login user to one or more SELinux roles.
        If the login user has no mapping yet, the role creates one.
        <em>Parameters</em>
        user_or_group - The user or group to be changed. If providing a group, pass it with an "@" before the group name (like "@my-group").
        selinux_roles - An iterable (tuple, list etc) with the roles to be referenced.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import SELinuxRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(SELinuxRole) as selinux:
                    selinux.map_role("foo", ["staff_r", "sysadm_r"])

        </pre>
        '''
        self.ensure_login_mapping(user_or_group)
        roles_as_string = ' '.join(selinux_roles)
        self.execute("semanage user -m -R '%s' %s" % (roles_as_string, user_or_group), stdout=False, sudo=True)
