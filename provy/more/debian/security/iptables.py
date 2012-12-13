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
