#!/usr/bin/python
# -*- coding: utf-8 -*-

from provy.core import Role, AskFor
from provy.more.debian import UserRole, VarnishRole, AptitudeRole


class Server(Role):
    def provision(self):
        user = self.context['logio-user']
        with self.using(UserRole) as role:
            role.ensure_user(user, identified_by='pass', is_admin=True)

servers = {
    'test': {
        'server': {
            'address': '33.33.33.33',
            'user': 'vagrant',
            'roles': [
                Server
            ],
            'options': {
                'logio-user': AskFor('front-end-user', 'Please enter the name of the nginx user')
            }
        }
    }
}
