#!/usr/bin/python
# -*- coding: utf-8 -*-

#from provy.core import Role
from provy.more.debian.web.nginx import NginxRole
from provy.more.debian.users import UserRole, SSHRole

class User(UserRole, SSHRole):
    def provision(self):
        self.ensure_user('test', identified_by='test-pass', is_admin=True)
        #self.ensure_ssh_key(user='test', key='AAAAB3NzaC1yc2EAAAADAQABAAABAQDn4fj6FZtSS7l2sNehakYgNpZyp39uekSgrM5pT0kYSxDq7+7gpbJI9qXkNcXrF+zhsPt5I9JtHZ86QSjPhlCCYkZJ71jq87R8Zd1LpMnk/AuTJRRDShL1S2NPA5r3fpaECLKNsqamGmaVJaxhvqqNHH7g9XtrbZFF8TlB99u/gR6OJ4CqPOUp1MXiawC0SUXgc54dHj5+k3ErOuH6Q2Q397MRsCsur5B6/d1bdN5QjJRa9Te9D3V1IB6Mz6fTx/74pmXns8rjbNSZsVbldPeqm7Ilct/nb1yP1oQ6X6n3+s8qzQhSW3oFM0QJdFBkBndZMzPmkyFFYHtLALXlKuKJ', type=SSHRole.rsa)

class Nginx(NginxRole):
    def provision(self):
        super(Nginx, self).provision()
        self.ensure_conf('test-conf.conf', {
            'user': 'test'
        })
        self.ensure_site_disabled('default')
        self.create_site('test', 'test-site', {
            'root_path': '/var/www/nginx-default',
            'media_path': '/var/www/nginx-default'
        })
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
        #'host2': {
            #'address': '33.33.33.34',
            #'user': 'root'
        #}
    }
}

