#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to provide `Tornado <http://www.tornadoweb.org/>`_ app server utility methods for Debian distributions.
'''

from provy.core import Role
from provy.more.debian.package.aptitude import AptitudeRole
from provy.more.debian.package.pip import PipRole


class TornadoRole(Role):
    '''
    This role provides `Tornado <http://www.tornadoweb.org/>`_ app server management utilities for Debian distributions.

    Example:
    ::

        from provy.core import Role
        from provy.more.debian import TornadoRole

        class MySampleRole(Role):
            def provision(self):
                self.provision_role(TornadoRole)
    '''

    def provision(self):
        '''
        Installs `Tornado <http://www.tornadoweb.org/>`_ and its dependencies.
        This method should be called upon if overriden in base classes, or `Tornado <http://www.tornadoweb.org/>`_ won't work properly in the remote server.

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import TornadoRole

            class MySampleRole(Role):
                def provision(self):
                    self.provision_role(TornadoRole)
        '''

        with self.using(AptitudeRole) as role:
            role.ensure_up_to_date()
            role.ensure_package_installed('python-pycurl')

        with self.using(PipRole) as role:
            role.ensure_package_installed('tornado')
