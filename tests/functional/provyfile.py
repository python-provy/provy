#!/usr/bin/python
# -*- coding: utf-8 -*-

#from provy.core import Role
from provy.more.debian.web.nginx import NginxRole

#class User(Role):
    #def provision(self, context):
        #self.ensure_user('test', identified_by='test-pass')

class Nginx(NginxRole):
    def provision(self):
        super(Nginx, self).provision()
        self.ensure_conf('test-conf.conf', {
            'user': 'vagrant'
        })
        self.ensure_site_disabled('default')
        self.create_site('test', 'test-site', {
            'root_path': '/var/www/nginx-default',
            'media_path': '/var/www/nginx-default'
        })
        self.ensure_site_enabled('test')

roles = {
    'test': [
        Nginx
    ]
}

servers = {
    'test': {
        'host1': {
            'address': '33.33.33.33',
            'user': 'vagrant'
        },
        #'host2': {
            #'address': '33.33.33.34',
            #'user': 'root'
        #}
    }
}

