# -*- coding: utf-8 -*-

import os

from provy.core import Role
from provy.more.debian import UserRole, TornadoRole, SupervisorRole, NginxRole


class FrontEnd(Role):
    def provision(self):
        with self.using(UserRole) as role:
            role.ensure_user('frontend', identified_by='pass', is_admin=True)

        with self.using(NginxRole) as role:
            role.ensure_conf(conf_template='nginx.conf', options={'user': 'frontend'})
            role.ensure_site_disabled('default')
            role.create_site(site='website', template='website', options={
                'host': os.environ['PROVY_HOST'],
                'port': os.environ['PROVY_PORT'],
            })
            role.ensure_site_enabled('website')


class BackEnd(Role):
    def provision(self):
        with self.using(UserRole) as role:
            role.ensure_user('backend', identified_by='pass', is_admin=True)

        self.update_file('website.py', '/home/backend/website.py', owner='backend', sudo=True)

        self.provision_role(TornadoRole)

        # make sure we have a folder to store our logs
        self.ensure_dir('/home/backend/logs', owner='backend')

        with self.using(SupervisorRole) as role:
            role.config(
                config_file_directory='/home/backend',
                log_folder='/home/backend/logs/',
                user='backend'
            )

            with role.with_program('website') as program:
                program.directory = '/home/backend'
                program.command = 'python website.py 800%(process_num)s'
                program.number_of_processes = 4

                program.log_folder = '/home/backend/logs'


servers = {
    'end-to-end': {
        'frontend': {
            'address': os.environ['PROVY_HOST'],
            'user': os.environ['PROVY_USERNAME'],
            'roles': [
                FrontEnd
            ]
        },
        'backend': {
            'address': os.environ['PROVY_HOST'],
            'user': os.environ['PROVY_USERNAME'],
            'roles': [
                BackEnd
            ]
        }
    }
}
