from provy.core import Role
from provy.more.debian.package.aptitude import AptitudeRole


class UFWRole(Role):

    def provision(self):
        '''
        Installs ufw and its dependencies, if they're not already installed.
        Also, it allows ssh (TCP+UDP/22), so that provy can continue to provision the server, and the user doesn't get locked out of it.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import UFWRole

        class MySampleRole(Role):
            def provision(self):
                self.provision_role(UFWRole) # no need to call this if using with block.

        </pre>
        '''
        with self.using(AptitudeRole) as aptitude:
            aptitude.ensure_package_installed('ufw')

        self.execute('ufw allow ssh', stdout=False, sudo=True)

    def schedule_cleanup(self):
        '''
        Apart from the core cleanup, this one also enables the firewall.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import UFWRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(UFWRole) as iptables:
                    self.schedule_cleanup() # no need to call this explicitly

        </pre>
        '''
        super(UFWRole, self).schedule_cleanup()
        self.execute("ufw enable", stdout=False, sudo=True)

    def __change(self, action_name, direction, port, protocol):
        command = 'ufw %s ' % action_name
        if direction is not None:
            command += '%s ' % direction
        command += str(port)
        if protocol is not None:
            command += '/%s' % protocol
        self.execute(command, stdout=False, sudo=True)

    def allow(self, port, protocol=None, direction=None):
        self.__change('allow', direction, port, protocol)

    def deny(self, port, protocol=None, direction=None):
        self.__change('deny', direction, port, protocol)

    def reject(self, port, protocol=None, direction=None):
        self.__change('reject', direction, port, protocol)
