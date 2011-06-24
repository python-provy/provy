#!/usr/bin/python
# -*- coding: utf-8 -*-

from provy import Role
from provy.providers import Providers

class User(Role):
    def provision(self, context):
        self.ensure_user('test', identified_by='test-pass')

class Nginx(Role):
    def provision(self, context):
        self.ensure_package('nginx', Providers.APT)

roles = {
    'test': [
        User,
        Nginx
    ]
}

servers = {
    'test': {
        'host1': {
            'address': '33.33.33.33',
            'user': 'root'
        },
        'host2': {
            'address': '33.33.33.34',
            'user': 'root'
        }
    }
}

