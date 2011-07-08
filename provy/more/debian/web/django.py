#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to provide Django app server utility methods for Debian distributions.
'''

from provy.core import Role
from provy.more.debian.package.pip import PipRole

SITES_KEY = 'django-sites'

class WithSite(object):
    def __init__(self, django, name):
        self.django = django 
        self.name = name
        self.path = None
        self.threads = 1
        self.user = self.django.context['owner']
        self.settings = {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if not self.path:
            raise RuntimeError('[Django] The path to the site must be specified and should correspond to the directory where the settings.py file is for site %s.' % self.name)

        if SITES_KEY not in self.django.context:
            self.django.context[SITES_KEY] = []

        self.django.context[SITES_KEY].append({
            'name': self.name,
            'path': self.path,
            'threads': self.threads,
            'user': self.user,
            'settings': self.settings
        })

class DjangoRole(Role):
    '''
    This role provides Django app server management utilities for Debian distributions.
    <em>Sample usage</em>
    <pre class="sh_python">
        class MySampleRole(Role):
            def provision(self):
                with self.using(DjangoRole) as role:
                    with role.create_site('mysite') as site:
                        site.path = '/some/folder/with/settings.py'
                        site.threads = 4
                        # settings that override the website defaults.
                        site.settings = {

                        }
    </pre>
    '''

    def provision(self):
        '''
        Installs Django and its dependencies. This method should be called upon if overriden in base classes, or Django won't work properly in the remote server.
        If you set a variable called django-version in the context, that version of django will be installed instead of latest.
        <em>Sample usage</em>
        <pre class="sh_python">
            class MySampleRole(Role):
                def provision(self):
                    self.provision_role(DjangoRole) # no need to call this if using with block.

            # or
            class MySampleRole(Role):
                def provision(self):
                    self.context['django-version'] = '1.1.1'
                    self.provision_role(DjangoRole) # no need to call this if using with block.
                    # now django 1.1.1 is installed.
        </pre>
        '''
        with self.using(PipRole) as role:
            if 'django-version' in self.context:
                role.ensure_package_installed('django', version=self.context['django-version'])
            else:
                role.ensure_package_installed('django')

            role.ensure_package_installed('gunicorn')

    def create_site(self, name):
        '''
        Enters a with block with a Site variable that allows you to configure a django website.
        <em>Parameters</em>
        name - name of the website.
        <em>Sample usage</em>
        <pre class="sh_python">
            class MySampleRole(Role):
                def provision(self):
                    with self.using(DjangoRole) as role:
                        with role.create_site('website') as program:
                            site.path = '/some/folder/with/settings.py'
                            site.threads = 4
                            # settings that override the website defaults.
                            site.settings = {

                            }
        </pre>
        '''
        return WithSite(self, name)

