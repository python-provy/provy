#!/usr/bin/python
# -*- coding: utf-8 -*-

from os.path import join
from datetime import datetime, timedelta

from fabric.api import settings

from provy.core import Role

class YumRole(Role):
    time_format = "%d-%m-%y %H:%M:%S"
    key = 'yum-up-to-date'

    def provision(self):
        self.ensure_up_to_date()
        self.ensure_package_installed('curl')

    def ensure_gpg_key(self, url):
        command = "curl %s | rpm --import -" % url
        self.execute(command, stdout=False, sudo=True)

    def has_source(self, source_string):
        return source_string in self.execute('cat /etc/yum.repos.d/CentOS-Base.repo', stdout=False, sudo=True)

    def ensure_yum_source(self, source_string):
        if self.has_source(source_string):
            return False

        self.log("Yum source %s not found! Adding it..." % source_string)
        command = 'echo "%s" >> /etc/yum.repos.d/CentOS-Base.repo' % source_string
        self.execute(command, stdout=False, sudo=True)
        return True

    @property
    def update_date_file(self):
        return join(self.remote_temp_dir(), 'last_yum_update')

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
            self.force_update()

    def force_update(self):
        self.log('Updating yum sources...')
        self.execute('yum update -y', stdout=False, sudo=True)
        self.store_update_date()
        self.log('Yum sources up-to-date')
        self.context[self.key] = True

    def is_package_installed(self, package_name):
        with settings(warn_only=True):
            return package_name in self.execute("rpm -qa" % package_name, stdout=False, sudo=True)

    def ensure_package_installed(self, package_name):
        if not self.is_package_installed(package_name):
            self.log('%s is not installed (via yum)! Installing...' % package_name)
            self.execute('yum install -y %s' % package_name, stdout=False, sudo=True)
            self.log('%s is installed (via yum).' % package_name)
