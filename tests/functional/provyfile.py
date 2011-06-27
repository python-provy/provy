#!/usr/bin/python
# -*- coding: utf-8 -*-

from provy.core import Role
from provy.more.debian import NginxRole, TornadoRole, UserRole, SSHRole, PipRole
from provy.more.debian import VarnishRole, AptitudeRole, GitRole

class FrontEnd(Role):
    def provision(self):
        with self.using(UserRole) as role:
            role.ensure_user('frontend', identified_by='pass', is_admin=True)

        with self.using(VarnishRole) as role:
            role.ensure_vcl('default.vcl', owner='frontend')
            role.ensure_conf('default_varnish', owner='frontend')

        with self.using(NginxRole) as role:
            role.ensure_conf(conf_template='test-conf.conf', options={'user': 'frontend'})
            role.ensure_site_disabled('default')
            role.create_site(site='frontend', template='test-site', options = {
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
                                   owner='backend')

        with self.using(AptitudeRole) as role:
            role.ensure_package_installed('libjpeg')

        with self.using(PipRole) as role:
            role.ensure_package_up_to_date("pil")

        self.provision_role(TornadoRole)

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

