#!/usr/bin/python
# -*- coding: utf-8 -*-

from provy.core import Role
from provy.more.debian.package.pip import PipRole

class SupervisorRole(Role):
    def provision(self):
        self.register_template_loader('provy.more.debian.monitoring')

        with self.using(PipRole) as role:
            role.ensure_package_installed('supervisor')

    def update_init_script(self, config_file_path):
        options = { 'config_file': config_file_path }
        self.update_file('supervisord.init.template', '/etc/init.d/supervisord', owner=self.context['owner'], options=options)

        self.execute('chmod +x /etc/init.d/supervisord', stdout=False, sudo=True)
        self.execute('update-rc.d supervisord defaults', stdout=False, sudo=True)

    def ensure_config_update(self):
        self.context['must-update-supervisor-config'] = True

    def config(self,
               config_file_directory=None,
               log_file='/var/logs/supervisord.log',
               log_file_max_mb=50,
               log_file_backups=10,
               log_level='info',
               pidfile='/var/run/supervisord.pid',
               user=None):
        if config_file_directory is None:
            config_file_directory = '/home/%s' % self.context['owner']
        if user is None:
            user = self.context['owner']

        self.context['supervisor-config'] = {
            'config_file_directory': config_file_directory,
            'log_file': log_file,
            'log_file_max_mb': log_file_max_mb,
            'log_file_backups': log_file_backups,
            'log_level': log_level,
            'pidfile': pidfile,
            'user': user
        }

        self.ensure_config_update()

    def update_config_file(self):
        pass

    def cleanup(self):
        if 'must-update-supervisor-config' in self.context and self.context['must-update-supervisor-config']:
            self.update_init_script()
            self.update_config_file()
            self.ensure_restart()

        if 'must-restart-supervisor' in self.context and self.context['must-restart-supervisor']:
            self.restart()

    def ensure_restart(self):
        self.context['must-restart-supervisor'] = True

    def restart(self):
        command = '/etc/init.d/supervisor restart'
        self.execute(command, sudo=True)


