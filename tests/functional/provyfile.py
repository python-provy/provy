#!/usr/bin/python
# -*- coding: utf-8 -*-

from provy.core import Role
from provy.more.debian import NginxRole, TornadoRole, UserRole, SSHRole
from provy.more.debian import PipRole, VarnishRole, AptitudeRole, GitRole
from provy.more.debian import SupervisorRole


class FrontEnd(Role):
    def provision(self):
        with self.using(UserRole) as role:
            role.ensure_user('frontend', identified_by='pass', is_admin=True)

        with self.using(VarnishRole) as role:
            role.ensure_vcl('default.vcl', owner='frontend')
            role.ensure_conf('default_varnish', owner='frontend')

        with self.using(NginxRole) as role:
            role.ensure_conf(conf_template='test-conf.conf',
                             options={'user': 'frontend'})
            role.ensure_site_disabled('default')
            role.create_site(site='frontend', template='test-site',
                             options={
                                'root_path': '/var/www/nginx-default',
                                'media_path': '/var/www/nginx-default'
                             })
            role.ensure_site_enabled('frontend')


class BackEnd(Role):
    def provision(self):
        with self.using(UserRole) as role:
            role.ensure_user('backend', identified_by='pass', is_admin=True)

        with self.using(SSHRole) as role:
            role.ensure_ssh_key(user='backend', private_key_file="private-key")

        with self.using(GitRole) as role:
            role.ensure_repository(repo='git://github.com/heynemann/provy.git',
                                   path='/home/backend/provy',
                                   branch="master",
                                   owner='backend')

        with self.using(AptitudeRole) as role:
            role.ensure_package_installed('libjpeg8')
            role.ensure_package_installed('libjpeg8-dev')

        with self.using(PipRole) as role:
            role.ensure_package_installed("pil")

        self.provision_role(TornadoRole)

        self.ensure_dir('/home/backend/logs', sudo=True, owner='backend')

        with self.using(SupervisorRole) as role:
            role.config(
                config_file_directory='/home/backend',
                log_file='/home/backend/logs/supervisord.log',
                user='backend'
            )

            with role.with_program('website') as program:
                program.directory = '/home/backend/provy/tests/functional'
                program.command = 'python website.py 800%(process_num)s'
                program.number_of_processes = 4

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
            ]
        }
    }
}

