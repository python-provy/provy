#!/usr/bin/python
# -*- coding: utf-8 -*-

from provy.core import Role
from provy.more.debian import UserRole
from provy.more.debian import GitRole
from provy.more.debian import RailsRole


class RailsSite(Role):
    def provision(self):
        with self.using(UserRole) as role:
            role.ensure_user('rails', identified_by='pass', is_admin=True)

        self.change_dir_mode('/home/rails', mode=644, recursive=False)

        with self.using(GitRole) as role:
            role.ensure_repository(repo='git://github.com/heynemann/hello-rails.git',
                                   path='/home/rails/hello-rails',
                                   branch="master",
                                   owner='rails')

        self.ensure_dir('/home/rails/logs', sudo=True, owner='rails')

        with self.using(RailsRole) as role:
            pass
            #role.ensure_site_disabled('default')
            #role.create_site('hello-rails', '/home/rails/hello-rails')
            #role.ensure_site_enabled('hello-rails')


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

