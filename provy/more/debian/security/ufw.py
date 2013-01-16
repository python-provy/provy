from provy.core import Role
from provy.more.debian.package.aptitude import AptitudeRole

'''
Roles in this namespace are meant to provide UncomplicatedFireWall management utilities for Debian distributions.
'''


class UFWRole(Role):
    '''
    This role provides ufw utilities for Debian distributions.
    There are two important behaviors to notice:
    Right after ufw is installed, this role allows TCP and UDP (in and out) connections to port 22, so that provy can still continue to provision the server through SSH.
    Right before exiting the "with using(UFWRole)" block, it enables ufw, which blocks all other ports and protocols, so that the server is secure by default.
    So, when using this role, remember to allow all the ports with protocols that you need, otherwise you might not be able to connect to the services you provision later on.
    <em>Properties</em>
    block_on_finish - If False, doesn't block other ports and protocols when finishing the usage of this role. Defaults to True.
    <em>Sample usage</em>
    <pre class="sh_python">
    from provy.core import Role
    from provy.more.debian import UFWRole

    class MySampleRole(Role):
        def provision(self):

            # this example allows only incoming HTTP connections
            with self.using(UFWRole) as ufw:
                ufw.allow('http')

            # this example blocks SSH outgoing connections
            with self.using(UFWRole) as ufw:
                ufw.reject(22, direction="out") # here we used a number, but could be "ssh" as well
    </pre>
    '''

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
                with self.using(UFWRole) as ufw:
                    self.schedule_cleanup() # no need to call this explicitly

        </pre>
        '''
        super(UFWRole, self).schedule_cleanup()
        self.execute("ufw --force enable", stdout=False, sudo=True)

    def __change(self, action_name, direction, port_or_query, protocol):
        command = 'ufw %s ' % action_name
        if direction is not None:
            command += '%s ' % direction
        command += str(port_or_query)
        if protocol is not None:
            command += '/%s' % protocol
        self.execute(command, stdout=False, sudo=True)

    def allow(self, port_or_query, protocol=None, direction=None):
        '''
        Allows connections to be made to or from the server.
        <em>Parameters</em>
        port_or_query - Port to be used, or a full query specification. If you use a full query, there's no sense in providing the other arguments.
        direction - Direction of the connection related to the server. Can be either "in" (connections coming into the server) or "out" (connections coming from the server to the outside).
        protocol - Protocol to be used - choose one that is understandable by ufw (like "udp", "icmp" etc). By default, it changes for "tcp" and "udp".
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import UFWRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(UFWRole) as ufw:
                    ufw.allow(11211, protocol="udp", direction="out") # allow UDP connections to an external Memcached server.

        </pre>
        '''
        self.__change('allow', direction, port_or_query, protocol)

    def drop(self, port_or_query, protocol=None, direction=None):
        '''
        Drop connections to be made to or from the server, without responding anything to the client (drop packets on the ground).
        <em>Parameters</em>
        port_or_query - Port to be used, or a full query specification. If you use a full query, there's no sense in providing the other arguments.
        direction - Direction of the connection related to the server. Can be either "in" (connections coming into the server) or "out" (connections coming from the server to the outside).
        protocol - Protocol to be used - choose one that is understandable by ufw (like "udp", "icmp" etc). By default, it changes for "tcp" and "udp".
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import UFWRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(UFWRole) as ufw:
                    ufw.drop(port=11211, direction="out", protocol="udp") # drop UDP connections to an external Memcached server.

        </pre>
        '''
        self.__change('deny', direction, port_or_query, protocol)

    def reject(self, port_or_query, protocol=None, direction=None):
        '''
        Rejects connections to be made to or from the server, responding with a "connection refused" packet.
        <em>Parameters</em>
        port_or_query - Port to be used, or a full query specification. If you use a full query, there's no sense in providing the other arguments.
        direction - Direction of the connection related to the server. Can be either "in" (connections coming into the server) or "out" (connections coming from the server to the outside).
        protocol - Protocol to be used - choose one that is understandable by ufw (like "udp", "icmp" etc). By default, it changes for "tcp" and "udp".
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import UFWRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(UFWRole) as ufw:
                    ufw.reject(port=11211, direction="out", protocol="udp") # reject UDP connections to an external Memcached server.

        </pre>
        '''
        self.__change('reject', direction, port_or_query, protocol)
