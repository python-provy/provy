from provy.core import Role
from provy.more.debian.package.aptitude import AptitudeRole


class IPTablesRole(Role):
    '''
    This role provides iptables utilities for Debian distributions.
    There are two important behaviors to notice:
    Right after iptables is installed, this role allows TCP incoming connections to port 22, so that provy can still continue to provision the server through SSH.
    Right before exiting the "with using(IPTablesRole)" block, it blocks all other ports and protocols, so that the server is secure by default.
    So, when using this role, remember to allow all the ports with protocols that you need, otherwise you might not be able to connect to the services you provision later on.
    <em>Properties</em>
    block_on_finish - if False, doesn't block other ports and protocols when finishing the usage of this role. Defaults to True.
    <em>Sample usage</em>
    <pre class="sh_python">
    from provy.core import Role
    from provy.more.debian import IPTablesRole

    class MySampleRole(Role):
        def provision(self):

            # this example uses the defaults provided
            with self.using(IPTablesRole) as iptables:
                iptables.list_rules()

            # this is when you want to avoid blocking other ports and protocols that don't match any previous one
            with self.using(IPTablesRole) as iptables:
                iptables.block_on_finish = False
                iptables.list_rules()
    </pre>
    '''

    def __init__(self, prov, context):
        super(IPTablesRole, self).__init__(prov, context)
        self.block_on_finish = True

    def provision(self):
        '''
        Installs iptables and its dependencies, if they're not already installed (though this is usually the case).
        Also, it adds an ACCEPT rule for SSH (TCP/22), so that provy can continue to provision the server, and the user doesn't get locked out of it.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import IPTablesRole

        class MySampleRole(Role):
            def provision(self):
                self.provision_role(IPTablesRole) # no need to call this if using with block.

        </pre>
        '''
        with self.using(AptitudeRole) as aptitude:
            aptitude.ensure_package_installed('iptables')
            self.execute('iptables -A INPUT -j ACCEPT -p tcp -m tcp --dport 22', stdout=False, sudo=True)

    def list_rules(self):
        '''
        Lists the currently configured rules and returns them as a multiline string. Equivalent to running "iptables -L".
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import IPTablesRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(IPTablesRole) as iptables:
                    iptables.list_rules()

        </pre>
        '''
        return self.execute('iptables -L', stdout=True, sudo=True)

    def list_rules_with_commands(self):
        '''
        Like IPTablesRole.list_rules(), but showing the rules as executable commands. Equivalent to running "iptables-save".
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import IPTablesRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(IPTablesRole) as iptables:
                    iptables.list_rules_with_commands()

        </pre>
        '''
        return self.execute('iptables-save', stdout=True, sudo=True)

    def schedule_cleanup(self):
        '''
        Apart from the core cleanup, this one also blocks other ports and protocols not allowed earlier ("catch-all" as the last rule) and saves the iptables rules to the iptables config file, so that it's not lost upon restart.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import IPTablesRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(IPTablesRole) as iptables:
                    self.schedule_cleanup() # no need to call this explicitly

        </pre>
        '''
        super(IPTablesRole, self).schedule_cleanup()
        if self.block_on_finish:
            self.execute('iptables -A INPUT -j DROP', stdout=False, sudo=True)
        self.execute("iptables-save > /etc/iptables.rules", stdout=False, sudo=True)

    def allow(self, port=None):
        command = "iptables -A INPUT -j ACCEPT -p tcp"
        if port is not None:
            command += " --dport %s" % port
        self.execute(command, stdout=False, sudo=True)
