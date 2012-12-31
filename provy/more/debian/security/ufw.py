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
