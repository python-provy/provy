#!/usr/bin/python
# -*- coding: utf-8 -*-

from provy.core import Role
#from provy.more.nginx import NginxRole

class HelloWorld(Role):
    def provision(self, context):
        self.execute('echo done')

#class User(Role):
    #def provision(self, context):
        #self.ensure_user('test', identified_by='test-pass')

#class Nginx(NginxRole):
    #def provision(self, context):
        #self.ensure_conf('test-conf.conf')
        #self.ensure_site_disabled('default')
        #self.ensure_site_enabled('test', 'test-site', {})

roles = {
    'test': [
        HelloWorld
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

