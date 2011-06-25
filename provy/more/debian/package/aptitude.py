#!/usr/bin/python
# -*- coding: utf-8 -*-

from provy.core import Role

class AptitudeRole(Role):
    key = 'aptitude-up-to-date'

    def ensure_up_to_date(self, context):
        if not self.key in context:
            self.sudo_execute('aptitude update')
            context[self.key] = True

    def ensure_package_installed(self, package_name):
        self.sudo_execute('aptitude install -y %s' % package_name)
