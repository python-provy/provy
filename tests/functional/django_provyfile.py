#!/usr/bin/python
# -*- coding: utf-8 -*-

from provy.core import Role, AskFor
from provy.more.debian import NginxRole, UserRole
from provy.more.debian import GitRole, MySQLRole
from provy.more.debian import SupervisorRole, DjangoRole


class FrontEnd(Role):
    def provision(self):
        user = self.context['front-end-user']
        with self.using(UserRole) as role:
            role.ensure_user(user, identified_by='pass', is_admin=True)

        with self.using(NginxRole) as role:
            role.ensure_conf(conf_template='test-conf.conf', options={
                'user': user
            })
            role.ensure_site_disabled('default')
            role.create_site(site='frontend', template='test-site')
            role.ensure_site_enabled('frontend')

        self.ensure_line('version: 0.1.0', '/home/frontend/version.txt', sudo=True, owner='frontend')
        self.change_dir_mode('/home/frontend', mode=644, recursive=False)


class BackEnd(Role):
    def provision(self):
        with self.using(UserRole) as role:
            role.ensure_user('backend', identified_by='pass', is_admin=True)

        with self.using(GitRole) as role:
            role.ensure_repository(repo='git://github.com/heynemann/provy.git',
                                   path='/home/backend/provy',
                                   branch="master",
                                   owner='backend')

        self.ensure_dir('/home/backend/logs', sudo=True, owner='backend')

        with self.using(MySQLRole) as role:
            role.ensure_user(username=self.context['mysql_user'],
                             login_from="%",
                             identified_by=self.context['mysql_password'])
            role.ensure_database(self.context['mysql_database'])
            role.ensure_grant('ALL PRIVILEGES', on=self.context['mysql_database'], username=self.context['mysql_user'], login_from='%')

        with self.using(SupervisorRole) as role:
            role.config(
                config_file_directory='/home/backend',
                log_folder='/home/backend/logs',
                user='backend'
            )

            with self.using(DjangoRole) as role:
                with role.create_site('website') as site:
                    site.settings_path = '/home/backend/provy/tests/functional/djangosite/settings.py'
                    site.threads = 2
                    site.processes = 2
                    site.user = 'backend'
                    site.pid_file_path = '/home/backend'
                    site.log_file_path = '/home/backend/logs'
                    site.settings = {
                        'CREATED_BY': 'provy'
                    }

            self.change_dir_mode('/home/backend/provy/tests/functional/djangosite', mode=777, recursive=True)

servers = {
    'test': {
        'frontend': {
            'address': '33.33.33.33',
            'user': 'vagrant',
            'roles': [
                FrontEnd
            ],
            'options': {
                'front-end-user': AskFor('front-end-user', 'Please enter the name of the nginx user')
            }
        },
        'backend': {
            'address': '33.33.33.34',
            'user': 'vagrant',
            'roles': [
                BackEnd
            ],
            'options': {
                'mysql_root_pass': 'pass',
                'mysql_user': 'backend',
                'mysql_password': 'pass',
                'mysql_database': 'djangosite'
            }
        }
    }
}

