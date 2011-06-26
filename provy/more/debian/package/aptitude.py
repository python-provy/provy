#!/usr/bin/python
# -*- coding: utf-8 -*-

from os.path import join
from datetime import datetime, timedelta

from provy.core import Role

class AptitudeRole(Role):
    time_format = "%d-%m-%y %H:%M:%S"
    key = 'aptitude-up-to-date'

    @property
    def update_date_file(self):
        return join(self.remote_temp_dir(), 'last_aptitude_update')

    def store_update_date(self):
        self.execute('echo "%s" > %s' % (datetime.now().strftime(self.time_format), self.update_date_file), stdout=False)

    def get_last_update_date(self):
        if not self.remote_exists(self.update_date_file):
            return None

        date = datetime.strptime(self.read_remote_file(self.update_date_file), self.time_format)
        return date

    def ensure_up_to_date(self):
        last_updated = self.get_last_update_date()
        if not self.key in self.context and (not last_updated or (datetime.now() - last_updated > timedelta(minutes=30))):
            self.log('Updating aptitude sources...')
            self.execute('aptitude update', stdout=False, sudo=True)
            self.store_update_date()
            self.log('Aptitude sources up-to-date')
            self.context[self.key] = True

    def is_package_installed(self, package_name):
        return package_name in self.execute("dpkg -l | grep %s" % package_name, stdout=False, sudo=True)

    def ensure_package_installed(self, package_name):
        if not self.is_package_installed:
            self.log('%s is not installed (via aptitude)! Installing...' % package_name)
            self.execute('aptitude install -y %s' % package_name, stdout=False, sudo=True)
            self.log('%s is installed (via aptitude).' % package_name)
