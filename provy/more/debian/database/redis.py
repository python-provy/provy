#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to provide `Redis <http://redis.io/>`_ key-value store management utilities for Debian distributions.
'''

from provy.core import Role
from provy.more.debian import AptitudeRole


class RedisRole(Role):
    '''
    This role provides `Redis <http://redis.io/>`_ key-value store management utilities for Debian distributions.

    Example:
    ::

        from provy.core import Role
        from provy.more.debian import RedisRole

        class MySampleRole(Role):
            def provision(self):
                self.provision_role(RedisRole)
    '''

    def provision(self):
        '''
        Installs `Redis <http://redis.io/>`_ and its dependencies.
        This method should be called upon if overriden in base classes, or Redis won't work properly in the remote server.

        Example:
        ::

            class MySampleRole(Role):
                def provision(self):
                    self.provision_role(RedisRole) # no need to call this if using with block.
        '''
        with self.using(AptitudeRole) as aptitude:
            aptitude.ensure_package_installed('redis-server')
            aptitude.ensure_package_installed('python-redis')
