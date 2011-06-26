#!/usr/bin/python
# -*- coding: utf-8 -*-

#from provy.core import Role
from provy.more.debian.web.nginx import NginxRole
from provy.more.debian.users import UserRole, SSHRole

class User(UserRole, SSHRole):
    def provision(self):
        self.ensure_user('test', identified_by='test-pass', is_admin=True)
        self.ensure_ssh_key(user='test', private_key_file="private-key")

class Nginx(NginxRole):
    def provision(self):
        super(Nginx, self).provision()
        self.ensure_conf(conf_template='test-conf.conf', 
                         options={
                            'user': 'test'
                         }
        )
        self.ensure_site_disabled('default')
        self.create_site(site='test', 
                         template='test-site', 
                         options = {
                            'root_path': '/var/www/nginx-default',
                            'media_path': '/var/www/nginx-default'
                         }
        )
        self.ensure_site_enabled('test')

roles = {
    'test': [
        User,
        Nginx
    ]
}

servers = {
    'test': {
        'host1': {
            'address': '33.33.33.33',
            'user': 'vagrant'
        },
        'host2': {
            'address': '33.33.33.34',
            'user': 'vagrant'
        }
    }
}

