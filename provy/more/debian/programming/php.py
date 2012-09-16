from provy.core import Role
from provy.more.debian.package.aptitude import AptitudeRole


class PHPRole(Role):
    '''
    This role provides PHP utilities for Debian distributions.
    Additionally, installs php5-dev (PHP source libraries), php-pear (PHP package management).

    <em>Sample usage</em>
    <pre class="sh_python">
    from provy.core import Role
    from provy.more.debian import PHPRole

    class MySampleRole(Role):
        def provision(self):
            self.provision_role(PHPRole)
    </pre>
    '''

    def provision(self):
        '''
        Installs PHP and its dependencies. This method should be called upon if overriden in base classes, or PHP won't work properly in the remote server.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import PHPRole

        class MySampleRole(Role):
            def provision(self):
                self.provision_role(PHPRole) # no need to call this if using with block.

        </pre>
        '''

        with self.using(AptitudeRole) as aptitude:
            aptitude.ensure_package_installed('php5')
            aptitude.ensure_package_installed('php5-dev')
            aptitude.ensure_package_installed('php-pear')