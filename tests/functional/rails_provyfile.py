#!/usr/bin/python
# -*- coding: utf-8 -*-

from provy.core import Role
from provy.more.debian import UserRole
from provy.more.debian import GitRole
from provy.more.debian import RailsRole


class RailsSite(Role):
    def provision(self):
        with self.using(UserRole) as role:
            role.ensure_user('rails', identified_by='pass')

        with self.using(GitRole) as role:
            role.ensure_repository(repo='git://github.com/heynemann/hello-rails.git',
                                   path='/home/rails/hello-rails',
                                   branch="master",
                                   owner='rails')

        with self.using(RailsRole) as role:
            role.ensure_site_disabled('default')
            role.create_site(site='hello-rails', host='localhost', path='/home/rails/hello-rails')
            role.ensure_site_enabled('hello-rails')


servers = {
    'test': {
        'frontend': {
            'address': '33.33.33.33',
            'user': 'vagrant',
            'roles': [
                RailsSite
            ],
            'options': {
            }
        }
    }
}

