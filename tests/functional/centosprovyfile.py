#!/usr/bin/python
# -*- coding: utf-8 -*-

from provy.core import Role, AskFor
from provy.more.centos import UserRole
from provy.more.centos import PipRole, YumRole, GitRole, RabbitMqRole
from provy.more.centos import HostNameRole


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
            role.ensure_package_installed('libjpeg')
            role.ensure_package_installed('libjpeg-devel')

        with self.using(PipRole) as role:
            role.ensure_package_installed("pil")

        with self.using(HostNameRole) as role:
            role.ensure_hostname('rabbit')

        with self.using(RabbitMqRole) as role:
            role.delete_user('guest')
            role.ensure_user(
                self.context['rabbit_user'], self.context['rabbit_password'],
            )
            role.ensure_vhost(self.context['rabbit_vhost'])
            role.ensure_permission(
                self.context['rabbit_vhost'],
                self.context['rabbit_user'],
                '".*" ".*" ".*"',
            )


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
                'supervisor-user': 'backend',

                'rabbit_user': 'celery',
                'rabbit_password': AskFor('rabbit_password', 'Rabbit password'),
                'rabbit_vhost': '/celery',
            }

        }
    }
}
