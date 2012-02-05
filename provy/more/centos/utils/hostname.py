#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to provide hostname utilities
methods within CentOS distributions.
'''
from fabric.contrib.files import sed
from fabric.api import settings, hide

from provy.core import Role


class HostNameRole(Role):
    def ensure_hostname(self, hostname):

        '''
        Ensure a fixed hostname
        <em>Parameters</em>
        hostname - Hostname to be created
        <em>Sample usage</em>
        class MySampleRole(Role):
            def provision(self):
                with self.using(HostNameRole) as role:
                    role.ensure_hostname('rabbit')
        '''
        path = '/etc/sysconfig/network'

        file = self.read_remote_file(path)
        hostname_line = 'HOSTNAME={0}'.format(hostname)

        if hostname == self.execute('hostname'):
            return False

        self.log('Setting up hostname')

        if 'HOSTNAME' not in file:
            self.ensure_line(hostname_line, stdout=False, sudo=True)
        else:
            with settings(hide('warnings', 'running', 'stdout')):
                sed(path, 'HOSTNAME=.*', hostname_line, use_sudo=True)

        self.execute(
            'hostname "{0}"'.format(hostname), stdout=False, sudo=True,
        )
        self.log('Hostname %s added' % hostname)
        return True
