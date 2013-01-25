from provy.core import Role
from provy.more.debian.package.aptitude import AptitudeRole

'''
Roles in this namespace are meant to provide `UncomplicatedFireWall <https://help.ubuntu.com/community/UFW>`_ management utilities for Debian distributions.
'''


class UFWRole(Role):
    '''
    This role provides `UncomplicatedFireWall <https://help.ubuntu.com/community/UFW>`_ utilities for Debian distributions.

    .. note::
        There are two important behaviors to notice:

        1. Right after ufw is installed, this role allows TCP and UDP (in and out) connections to port 22, so that provy can still continue to provision the server through SSH.
        2. Right before exiting the "with using(UFWRole)" block, it enables ufw, which blocks all other ports and protocols, so that the server is secure by default.

        So, when using this role, remember to allow all the ports with protocols that you need, otherwise you might not be able to connect to the services you provision later on.

    :param block_on_finish: If :data:`False`, doesn't block other ports and protocols when finishing the usage of this role. Defaults to :data:`True`.
    :type block_on_finish: :class:`bool`

    Example:
    ::

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
    '''

    def provision(self):
        '''
        Installs ufw and its dependencies, if they're not already installed.

        Also, it allows ssh (TCP+UDP/22), so that provy can continue to provision the server, and the user doesn't get locked out of it.

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import UFWRole

            class MySampleRole(Role):
                def provision(self):
                    self.provision_role(UFWRole) # no need to call this if using with block.
        '''
        with self.using(AptitudeRole) as aptitude:
            aptitude.ensure_package_installed('ufw')

        self.execute('ufw allow ssh', stdout=False, sudo=True)

    def schedule_cleanup(self):
        '''
        Apart from the core cleanup, this one also enables the firewall.

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import UFWRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(UFWRole) as ufw:
                        self.schedule_cleanup() # no need to call this explicitly
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

        :param port_or_query: Port to be used, or a full query specification. If you use a full query, there's no sense in providing the other arguments.
        :type port_or_query: :class:`str`
        :param direction: Direction of the connection related to the server. Can be either "in" (connections coming into the server) or "out" (connections coming from the server to the outside). Defaults to :data:`None`, making ufw use the default of "in".
        :type direction: :class:`str`
        :param protocol: Protocol to be used - choose one that is understandable by ufw (like "udp", "icmp" etc). By default, it changes for "tcp" and "udp".
        :type protocol: :class:`str`

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import UFWRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(UFWRole) as ufw:
                        ufw.allow(11211, protocol="udp", direction="out") # allow UDP connections to an external Memcached server.
        '''
        self.__change('allow', direction, port_or_query, protocol)

    def drop(self, port_or_query, protocol=None, direction=None):
        '''
        Drop connections to be made to or from the server, without responding anything to the client (drop packets on the ground).

        :param port_or_query: Port to be used, or a full query specification. If you use a full query, there's no sense in providing the other arguments.
        :type port_or_query: :class:`str`
        :param direction: Direction of the connection related to the server. Can be either "in" (connections coming into the server) or "out" (connections coming from the server to the outside). Defaults to :data:`None`, making ufw use the default of "in".
        :type direction: :class:`str`
        :param protocol: Protocol to be used - choose one that is understandable by ufw (like "udp", "icmp" etc). By default, it changes for "tcp" and "udp".
        :type protocol: :class:`str`

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import UFWRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(UFWRole) as ufw:
                        ufw.drop(port=11211, direction="out", protocol="udp") # drop UDP connections to an external Memcached server.
        '''
        self.__change('deny', direction, port_or_query, protocol)

    def reject(self, port_or_query, protocol=None, direction=None):
        '''
        Rejects connections to be made to or from the server, responding with a "connection refused" packet.

        :param port_or_query: Port to be used, or a full query specification. If you use a full query, there's no sense in providing the other arguments.
        :type port_or_query: :class:`str`
        :param direction: Direction of the connection related to the server. Can be either "in" (connections coming into the server) or "out" (connections coming from the server to the outside). Defaults to :data:`None`, making ufw use the default of "in".
        :type direction: :class:`str`
        :param protocol: Protocol to be used - choose one that is understandable by ufw (like "udp", "icmp" etc). By default, it changes for "tcp" and "udp".
        :type protocol: :class:`str`

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import UFWRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(UFWRole) as ufw:
                        ufw.reject(port=11211, direction="out", protocol="udp") # reject UDP connections to an external Memcached server.
        '''
        self.__change('reject', direction, port_or_query, protocol)
