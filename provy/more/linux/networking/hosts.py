#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to provide hosts management operations.
'''

from provy.core import Role

class HostsRole(Role):
    '''
    This role provides hosts file management utilities.
    <em>Sample usage</em>
    <pre class="sh_python">
    from provy.core import Role
    from provy.more.linux import HostsRole

    class MySampleRole(Role):
        def provision(self):
            with self.using(HostsRole) as role:
                role.ensure_host('localhost', '127.0.0.1')
    </pre>
    '''

    def ensure_host(self, host_name, ip):
        self.ensure_line('%s        %s' % (ip, host_name), '/etc/hosts', sudo=True)

