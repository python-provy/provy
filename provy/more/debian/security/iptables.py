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
