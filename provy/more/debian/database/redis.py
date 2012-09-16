from provy.core import Role
from provy.more.debian import AptitudeRole


class RedisRole(Role):
    '''
    This role provides Redis key-value store management utilities for Debian distributions.
    <em>Sample usage</em>
    <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import RedisRole

        class MySampleRole(Role):
            def provision(self):
                self.provision_role(RedisRole)

    </pre>
    '''

    def provision(self):
        '''
        Installs Redis and its dependencies. This method should be called upon if overriden in base classes, or Redis won't work properly in the remote server.
        <em>Sample usage</em>
        <pre class="sh_python">
            class MySampleRole(Role):
                def provision(self):
                    self.provision_role(RedisRole) # no need to call this if using with block.
        </pre>
        '''
        with self.using(AptitudeRole) as aptitude:
            aptitude.ensure_package_installed('redis-server')
            aptitude.ensure_package_installed('python-redis')