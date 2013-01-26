#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to provide hosts management operations.
'''

from provy.core import Role


class HostsRole(Role):
    '''
    This role provides hosts file management utilities.

    Example:
    ::

        from provy.core import Role
        from provy.more.linux import HostsRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(HostsRole) as role:
                    role.ensure_host('localhost', '127.0.0.1')
    '''

    def ensure_host(self, host_name, ip):
        '''
        Makes sure that a certain host is configured in the hosts file.

        :param host_name: The hostname.
        :type host_name: :class:`str`
        :param ip: The IP to which the :data:`host_name` will point to.
        :type ip: :class:`str`
        '''
        self.ensure_line('%s        %s' % (ip, host_name), '/etc/hosts', sudo=True)
