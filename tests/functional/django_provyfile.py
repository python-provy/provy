#!/usr/bin/python
# -*- coding: utf-8 -*-

from provy.core import Role
from provy.more.debian import NginxRole, UserRole
from provy.more.debian import GitRole, MySQLRole
from provy.more.debian import SupervisorRole, DjangoRole

class FrontEnd(Role):
    def provision(self):
        with self.using(UserRole) as role:
            role.ensure_user('frontend', identified_by='pass', is_admin=True)

        with self.using(NginxRole) as role:
            role.ensure_conf(conf_template='test-conf.conf', options={
                'user': 'frontend'
            })
            role.ensure_site_disabled('default')
            role.create_site(site='frontend', template='test-site')
            role.ensure_site_enabled('frontend')

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

        with self.using(DjangoRole) as role:
            role.restart_supervisor_on_changes = True
            with role.create_site('website') as site:
                site.settings_path = '/home/backend/provy/tests/functional/djangosite/settings.py'
                site.auto_start = False # using with supervisor there's no need to auto-start.
                site.daemon = False # supervisor fails if the site daemonizes itself.
                site.threads = 2
                site.processes = 2
                site.user = 'backend'
                site.pid_file_path = '/home/backend'
                site.log_file_path = '/home/backend'
                site.settings = {
                    'CREATED_BY': 'provy'
                }

        with self.using(SupervisorRole) as role:
            role.config(
                config_file_directory='/home/backend',
                log_file='/home/backend/logs/supervisord.log',
                user='backend'
            )

            with role.with_program('website') as program:
                program.directory = '/home/backend'
                program.command = '/etc/init.d/website-80%(process_num)02d start'
                program.name = 'website-80%(process_num)02d'
                program.number_of_processes = 2
                program.user = 'backend'

                program.log_folder = '/home/backend/logs'

servers = {
    'test': {
        'frontend': {
            'address': '33.33.33.33',
            'user': 'vagrant',
            'roles': [
                FrontEnd
            ]
        },
        'backend': {
            'address': '33.33.33.34',
            'user': 'vagrant',
            'roles': [
                BackEnd
            ],
            'options': {
                'mysql_user': 'backend',
                'mysql_password': 'pass',
                'mysql_database': 'djangosite'
            }
        }
    }
}

