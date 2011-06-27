#!/usr/bin/python
# -*- coding: utf-8 -*-

from provy.core import Role
from provy.more.debian.web.nginx import NginxRole
from provy.more.debian.web.tornado import TornadoRole
from provy.more.debian.users import UserRole, SSHRole
from provy.more.debian.package.pip import PipRole
from provy.more.debian.vcs.git import GitRole

class WebServer(Role):
    def provision(self):
        with self.using(UserRole) as role:
            role.ensure_user('test', identified_by='test-pass', is_admin=True)

        with self.using(SSHRole) as role:
            role.ensure_ssh_key(user='test', private_key_file="private-key")

        with self.using(GitRole) as role:
            role.ensure_repository(repo='git://github.com/heynemann/provy.git',
                                   path='/home/test/provy',
                                   owner='test')

        with self.using(NginxRole) as role:
            role.ensure_conf(conf_template='test-conf.conf', options={'user': 'test'})
            role.ensure_site_disabled('default')
            role.create_site(site='test', template='test-site', options = {
                'root_path': '/var/www/nginx-default',
                'media_path': '/var/www/nginx-default'
            })
            role.ensure_site_enabled('test')

        with self.using(PipRole) as role:
            role.ensure_package_installed("django", "1.2.1")
            role.ensure_package_up_to_date("virtualenv")
            role.ensure_package_installed("pygeoip")

        self.provision_role(TornadoRole)

servers = {
    'test': {
        'host1': {
            'address': '33.33.33.33',
            'user': 'vagrant',
            'roles': [
                WebServer
            ]
        },
        #'host2': {
            #'address': '33.33.33.34',
            #'user': 'vagrant',
            #'roles': [
                #WebServer
            #]
        #}
    }
}

