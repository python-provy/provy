from provy.core import Role
from provy.more.debian.package.aptitude import AptitudeRole


class IPTablesRole(Role):
    '''
    This role provides iptables utilities for Debian distributions.

    <em>Sample usage</em>
    <pre class="sh_python">
    from provy.core import Role
    from provy.more.debian import IPTablesRole

    class MySampleRole(Role):
        def provision(self):
            self.provision_role(IPTablesRole)
    </pre>
    '''

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
            self.execute('iptables -A INPUT -p tcp -m tcp --dport 22 -j ACCEPT', stdout=False, sudo=True)

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
        Apart from the core cleanup, this one saves the iptables rules to the iptables config file, so that it's not lost upon restart.
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
        self.execute("iptables-save > /etc/iptables.rules", sudo=True)
