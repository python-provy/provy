#!/usr/bin/python
# -*- coding: utf-8 -*-

from provy.core import Role
from provy.more.centos import UserRole
from provy.more.centos import PipRole, YumRole, GitRole


class FrontEnd(Role):
    def provision(self):
        with self.using(UserRole) as role:
            role.ensure_user('frontend', identified_by='pass', is_admin=True)

class BackEnd(Role):
    def provision(self):
        with self.using(UserRole) as role:
            role.ensure_user('backend', identified_by='pass', is_admin=True)

        with self.using(GitRole) as role:
            role.ensure_repository(repo='git://github.com/heynemann/provy.git',
                                   path='/home/backend/provy',
                                   branch="master",
                                   owner='backend')

        with self.using(YumRole) as role:
            role.ensure_package_installed('libjpeg8')
            role.ensure_package_installed('libjpeg8-dev')

        with self.using(PipRole) as role:
            role.ensure_package_installed("pil")


servers = {
    'test': {
        'frontend': {
            'address': '10.0.0.10',
            'user': 'vagrant',
            'roles': [
                FrontEnd
            ],
            'options': {
                'user': 'frontend'
            }
        },
        'backend': {
            'address': '10.0.0.11',
            'user': 'vagrant',
            'roles': [
                BackEnd
            ],
            'options': {
                'supervisor-user': 'backend'
            }

        }
    }
}

