#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to provide hosts management operations for debian distributions.
'''

from provy.more.linux.networking.hosts import HostsRole as Hosts

class HostsRole(Hosts):
    '''
    This role provides hosts file management utilities for debian distributions.
    <em>Sample usage</em>
    <pre class="sh_python">
    from provy.core import Role
    from provy.more.debian import HostsRole

    class MySampleRole(Role):
        def provision(self):
            with self.using(HostsRole) as role:
                role.ensure_host('localhost', '127.0.0.1')
    </pre>
    '''

    def ensure_host(self, host_name, ip):
        super(HostsRole, self).ensure_host(host_name, ip)

