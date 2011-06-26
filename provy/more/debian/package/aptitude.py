#!/usr/bin/python
# -*- coding: utf-8 -*-

from provy.core import Role

class AptitudeRole(Role):
    key = 'aptitude-up-to-date'

    def ensure_up_to_date(self):
        if not self.key in self.context:
            self.log('Updating aptitude sources...')
            self.execute('aptitude update', stdout=False, sudo=True)
            self.log('Aptitude sources up-to-date')
            self.context[self.key] = True

    def ensure_package_installed(self, package_name):
        self.log('Making sure %s is installed (via aptitude).' % package_name)
        self.execute('aptitude install -y %s' % package_name, stdout=False, sudo=True)
        self.log('%s is installed (via aptitude).' % package_name)
