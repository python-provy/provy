from provy.core import Role
from provy.more.debian.package.aptitude import AptitudeRole

'''
Roles in this namespace are meant to provide `iptables <http://www.netfilter.org/>`_ management utilities for Debian distributions.
'''


class IPTablesRole(Role):
    '''
    This role provides `iptables <http://www.netfilter.org/>`_ utilities for Debian distributions.

    .. note::

        There are two important behaviors to notice:

        1. Right after iptables is installed, this role allows TCP incoming connections to port 22, so that provy can still continue to provision the server through SSH.

        2. Right before exiting the `with using(IPTablesRole)` block, it blocks all other ports and protocols, so that the server is secure by default.

        So, when using this role, remember to allow all the ports with protocols that you need, otherwise you might not be able to connect to the services you provision later on.

    :param block_on_finish: If :data:`False`, doesn't block other ports and protocols when finishing the usage of this role. Defaults to :data:`True`.
    :type block_on_finish: :class:`bool`

    Example:
    ::

        from provy.core import Role
        from provy.more.debian import IPTablesRole

        class MySampleRole(Role):
            def provision(self):

                # this example allows only incoming HTTP connections
                with self.using(IPTablesRole) as iptables:
                    iptables.allow('http')

                # this example allows any incoming connections, but block SSH outgoing connections
                with self.using(IPTablesRole) as iptables:
                    iptables.block_on_finish = False
                    iptables.reject(22, direction="out") # here we used a number, but could be "ssh" as well

                # this example allows established sessions in interface eth0
                with self.using(IPTablesRole) as iptables:
                    iptables.allow(interface='eth0', match='state', state='ESTABLISHED,RELATED')
    '''

    DIRECTION_TO_CHAIN_MAP = {
        "in": "INPUT",
        "out": "OUTPUT",
        "forward": "FORWARD",
    }

    def __init__(self, prov, context):
        super(IPTablesRole, self).__init__(prov, context)
        self.block_on_finish = True

    def provision(self):
        '''
        Installs iptables and its dependencies, if they're not already installed (though this is usually the case).

        Also, it adds an `ACCEPT` rule for SSH (TCP/22), so that provy can continue to provision the server, and the user doesn't get locked out of it.

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import IPTablesRole

            class MySampleRole(Role):
                def provision(self):
                    self.provision_role(IPTablesRole) # no need to call this if using with block.
        '''
        with self.using(AptitudeRole) as aptitude:
            aptitude.ensure_package_installed('iptables')
            self.allow('ssh')

    def list_rules(self):
        '''
        Lists the currently configured rules and returns them as a multiline string. Equivalent to running:

        .. code-block:: sh

            $ sudo iptables -L

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import IPTablesRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(IPTablesRole) as iptables:
                        iptables.list_rules()
        '''
        return self.execute('iptables -L', stdout=True, sudo=True)

    def list_rules_with_commands(self):
        '''
        Like :meth:`list_rules`, but showing the rules as executable commands. Equivalent to running:

        .. code-block:: sh

            $ sudo iptables-save

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import IPTablesRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(IPTablesRole) as iptables:
                        iptables.list_rules_with_commands()
        '''
        return self.execute('iptables-save', stdout=True, sudo=True)

    def schedule_cleanup(self):
        '''
        Apart from the core cleanup, this one also blocks other ports and protocols not allowed earlier ("catch-all" as the last rule)
        and saves the iptables rules to the iptables config file, so that it's not lost upon restart.

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import IPTablesRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(IPTablesRole) as iptables:
                        self.schedule_cleanup() # no need to call this explicitly
        '''
        super(IPTablesRole, self).schedule_cleanup()
        if self.block_on_finish:
            self.reject()
        self.execute("iptables-save > /etc/iptables.rules", stdout=False, sudo=True)

    def __change_rule(self, policy, port, direction, protocol, interface, match=None, **options):
        chain = self.DIRECTION_TO_CHAIN_MAP[direction]
        command = "iptables -A %s -j %s -p %s" % (chain, policy, protocol)
        if interface is not None:
            command += " -i %s" % interface
        if port is not None:
            command += " --dport %s" % port
        if match is not None:
            command += " -m %s" % match
        for option_name in options:
            command += " --%s %s" % (option_name, options[option_name])
        self.execute(command, stdout=False, sudo=True)

    def allow(self, port=None, direction="in", protocol="tcp", interface=None, match=None, **options):
        '''
        Allows connections to be made to or from the server.

        :param port: Port to be used. Defaults to None, which means all ports will be allowed. Defaults to :data:`None`.
        :type port: :class:`int` or :class:`str`
        :param direction: Direction of the connection related to the server. Can be either "in" (connections coming into the server), "out" (connections coming from the server to the outside) or "forward" (packet routing). Defaults to "in".
        :type direction: :class:`str`
        :param protocol: Protocol to be used - choose one that is understandable by iptables (like "udp", "icmp" etc). Defaults to "tcp".
        :type protocol: :class:`str`
        :param interface: The network interface to which the rule is bound to. Defaults to :data:`None` (bound to all).
        :type interface: :class:`str`
        :param match: Match filter. Defaults to :data:`None`.
        :type match: :class:`str`
        :param options: Arbitrary of arbitrary options that will be used in conjunction to the match filters.
        :type options: Keyword arguments of :class:`str`

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import IPTablesRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(IPTablesRole) as iptables:
                        iptables.allow(port=11211, direction="out", protocol="udp") # allow UDP connections to an external Memcached server.
        '''
        self.__change_rule("ACCEPT", port, direction, protocol, interface, match, **options)

    def reject(self, port=None, direction="in", protocol="all", interface=None, match=None, **options):
        '''
        Rejects connections to be made to or from the server, responding with a "connection refused" packet.

        :param port: Port to be used. Defaults to None, which means all ports will be allowed.
        :type port: :class:`int` or :class:`str`
        :param direction: Direction of the connection related to the server. Can be either "in" (connections coming into the server), "out" (connections coming from the server to the outside) or "forward" (packet routing). Defaults to "in".
        :type direction: :class:`str`
        :param protocol: Protocol to be used - choose one that is understandable by iptables (like "udp", "icmp" etc). Defaults to "all".
        :type protocol: :class:`str`
        :param interface: The network interface to which the rule is bound to. Defaults to :data:`None` (bound to all).
        :type interface: :class:`str`
        :param match: Match filter. Defaults to :data:`None`.
        :type match: :class:`str`
        :param options: Arbitrary of arbitrary options that will be used in conjunction to the match filters.
        :type options: Keyword arguments of :class:`str`

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import IPTablesRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(IPTablesRole) as iptables:
                        iptables.reject(port=11211, direction="out", protocol="udp") # reject UDP connections to an external Memcached server.
        '''
        self.__change_rule("REJECT", port, direction, protocol, interface, match, **options)

    def drop(self, port=None, direction="in", protocol="all", interface=None, match=None, **options):
        '''
        Drop connections to be made to or from the server, without responding anything to the client (drop packets on the ground).

        :param port: Port to be used. Defaults to None, which means all ports will be allowed.
        :type port: :class:`int` or :class:`str`
        :param direction: Direction of the connection related to the server. Can be either "in" (connections coming into the server), "out" (connections coming from the server to the outside) or "forward" (packet routing). Defaults to "in".
        :type direction: :class:`str`
        :param protocol: Protocol to be used - choose one that is understandable by iptables (like "udp", "icmp" etc). Defaults to "all".
        :type protocol: :class:`str`
        :param interface: The network interface to which the rule is bound to. Defaults to :data:`None` (bound to all).
        :type interface: :class:`str`
        :param match: Match filter. Defaults to :data:`None`.
        :type match: :class:`str`
        :param options: Arbitrary of arbitrary options that will be used in conjunction to the match filters.
        :type options: Keyword arguments of :class:`str`

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import IPTablesRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(IPTablesRole) as iptables:
                        iptables.drop(port=11211, direction="out", protocol="udp") # drop UDP connections to an external Memcached server.
        '''
        self.__change_rule("DROP", port, direction, protocol, interface, match, **options)
