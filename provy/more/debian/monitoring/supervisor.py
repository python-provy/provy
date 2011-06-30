#!/usr/bin/python
# -*- coding: utf-8 -*-

from os.path import join

from provy.core import Role
from provy.more.debian.package.pip import PipRole

PROGRAMS_KEY = 'supervisor-programs'
CONFIG_KEY = 'supervisor-config'
MUST_UPDATE_CONFIG_KEY = 'must-update-supervisor-config'
MUST_RESTART_KEY = 'must-restart-supervisor'

class WithProgram(object):
    def __init__(self, supervisor, name):
        self.supervisor = supervisor
        self.name = name
        self.directory = None
        self.command = None

        self.process_name = name + '-%(process_num)s'
        self.number_of_processes = 1
        self.priority = 100
        self.user = self.supervisor.context['owner']

        self.auto_start = True
        self.auto_restart = True
        self.start_retries = 3
        self.stop_signal = 'TERM'

        self.log_folder = '/var/log'
        self.log_file_max_mb = 1
        self.log_file_backups = 10

        self.environment = {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if not self.directory or not self.command:
            raise RuntimeError('[Supervisor] Both directory and command properties must be specified for program %s' % self.name)

        if PROGRAMS_KEY not in self.supervisor.context:
            self.supervisor.context[PROGRAMS_KEY] = []

        env = []
        for key, value in self.environment.iteritems():
            env.append('%s="%s"' % (key, value))
        env = ",".join(env)

        self.supervisor.context[PROGRAMS_KEY].append({
            'name': self.name,
            'directory': self.directory,
            'command': self.command,
            'process_name': self.process_name,
            'number_of_processes': self.number_of_processes,
            'priority': self.priority,
            'user': self.user,
            'auto_start': self.auto_start,
            'auto_restart': self.auto_restart,
            'start_retries': self.start_retries,
            'stop_signal': self.stop_signal,
            'log_folder': self.log_folder,
            'log_file_max_mb': self.log_file_max_mb,
            'log_file_backups': self.log_file_backups,
            'environment': env
        })

class SupervisorRole(Role):
    def provision(self):
        self.register_template_loader('provy.more.debian.monitoring')

        with self.using(PipRole) as role:
            role.ensure_package_installed('supervisor')

    def update_init_script(self, config_file_path):
        options = { 'config_file': join(config_file_path, 'supervisord.conf') }
        result = self.update_file('supervisord.init.template', '/etc/init.d/supervisord', owner=self.context['owner'], options=options, sudo=True)

        if result:
            self.execute('chmod +x /etc/init.d/supervisord', stdout=False, sudo=True)
            self.execute('update-rc.d supervisord defaults', stdout=False, sudo=True)
            self.ensure_restart()

    def ensure_config_update(self):
        self.context[MUST_UPDATE_CONFIG_KEY] = True

    def config(self,
               config_file_directory=None,
               log_file='/var/log/supervisord.log',
               log_file_max_mb=50,
               log_file_backups=10,
               log_level='info',
               pidfile='/var/run/supervisord.pid',
               user=None):
        if config_file_directory is None:
            config_file_directory = '/home/%s' % self.context['owner']
        if user is None:
            user = self.context['owner']

        self.context[CONFIG_KEY] = {
            'config_file_directory': config_file_directory,
            'log_file': log_file,
            'log_file_max_mb': log_file_max_mb,
            'log_file_backups': log_file_backups,
            'log_level': log_level,
            'pidfile': pidfile,
            'user': user
        }

        self.ensure_config_update()

    def with_program(self, name):
        return WithProgram(self, name)

    def update_config_file(self):
        if CONFIG_KEY in self.context or PROGRAMS_KEY in self.context:
            if CONFIG_KEY not in self.context:
                self.config()

            config = self.context[CONFIG_KEY]

            conf_path = join(config['config_file_directory'], 'supervisord.conf')
            options = config

            if PROGRAMS_KEY in self.context:
                options['programs'] = self.context[PROGRAMS_KEY]

            result = self.update_file('supervisord.conf.template', conf_path, options=options, owner=self.context['owner'], sudo=True)

            if result:
                self.ensure_restart()

    def cleanup(self):
        if MUST_UPDATE_CONFIG_KEY in self.context and self.context[MUST_UPDATE_CONFIG_KEY]:
            self.update_init_script(self.context[CONFIG_KEY]['config_file_directory'])
            self.update_config_file()

        if MUST_RESTART_KEY in self.context and self.context[MUST_RESTART_KEY]:
            self.restart()

    def ensure_restart(self):
        self.context[MUST_RESTART_KEY] = True

    def restart(self):
        if not self.is_process_running('supervisord'):
            command = '/etc/init.d/supervisord start'
        else:
            command = '/etc/init.d/supervisord restart'
        self.execute(command, sudo=True)

