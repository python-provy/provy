#!/usr/bin/python
# -*- coding: utf-8 -*-

from provy.core import Role, AskFor
from provy.more.debian import UserRole, NPMRole

class LogIOServerRole(Role):
    def provision(self):
        with self.using(NPMRole) as role:
            role.ensure_package_installed('socket.io', '0.6.17')
            role.ensure_package_installed('connect')
            role.ensure_package_installed('underscore')

    def ensure_config(self, port, authenticated=False, auth_user=None, auth_pass=None):
        pass

class Server(Role):
    def provision(self):
        with self.using(UserRole) as role:
            role.ensure_user('timehome', identified_by=self.context['logio-pass'], is_admin=True)

        with self.using(LogIOServerRole) as role:
            role.ensure_config(port=8989, authenticated=True, auth_user='timehome', auth_pass=self.context['logio-pass'])

servers = {
    'test': {
        'server': {
            'address': '33.33.33.33',
            'user': 'vagrant',
            'roles': [
                Server
            ],
            'options': {
                'logio-pass': AskFor('logio-pass', 'Please enter the password for the log.io user')
            }
        }
    }
}
