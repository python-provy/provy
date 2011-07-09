#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to provide Tornado app server utility methods for Debian distributions.
'''

from provy.core import Role
from provy.more.debian.package.aptitude import AptitudeRole
from provy.more.debian.package.pip import PipRole


class TornadoRole(Role):
    '''
    This role provides Tornado app server management utilities for Debian distributions.
    <em>Sample usage</em>
    <pre class="sh_python">
    from provy.core import Role
    from provy.more.debian import TornadoRole

    class MySampleRole(Role):
        def provision(self):
            self.provision_role(TornadoRole)
    </pre>
    '''

    def provision(self):
        '''
        Installs Tornado and its dependencies. This method should be called upon if overriden in base classes, or Tornado won't work properly in the remote server.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import TornadoRole

        class MySampleRole(Role):
            def provision(self):
                self.provision_role(TornadoRole)
        </pre>
        '''

        with self.using(AptitudeRole) as role:
            role.ensure_up_to_date()
            role.ensure_package_installed('python-pycurl')

        with self.using(PipRole) as role:
            role.ensure_package_installed('tornado')
