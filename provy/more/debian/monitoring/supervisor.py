#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to provide Supervisor monitoring utility methods for Debian distributions.
'''

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
    '''
    This role provides supervisor monitoring utilities for Debian distributions.
    <em>Sample usage</em>
    <pre class="sh_python">
    from provy.core import Role
    from provy.more.debian import SupervisorRole

    class MySampleRole(Role):
        def provision(self):
            with self.using(SupervisorRole) as role:
                role.config(
                    config_file_directory='/home/backend',
                    log_folder='/home/backend/logs',
                    user=self.context['supervisor-user']
                )

                with role.with_program('website') as program:
                    program.directory = '/home/backend/provy/tests/functional'
                    program.command = 'python website.py 800%(process_num)s'
                    program.number_of_processes = 4

                    program.log_folder = '/home/backend/logs'
    </pre>
    '''

    def provision(self):
        '''
        Installs Supervisor and its dependencies. This method should be called upon if overriden in base classes, or Supervisor won't work properly in the remote server.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import SupervisorRole

        class MySampleRole(Role):
            def provision(self):
                self.provision_role(SupervisorRole) # no need to call this if using with block.
        </pre>
        '''
        self.register_template_loader('provy.more.debian.monitoring')

        with self.using(PipRole) as pip:
            pip.set_sudo()
            pip.ensure_package_installed('supervisor')

    def update_init_script(self, config_file_path):
        '''
        Creates a supervisord /etc/init.d script that points to the specified config file path.
        <em>Parameters</em>
        config_file_path - path to the supervisord.conf at the server.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import SupervisorRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(SupervisorRole) as role:
                    role.update_init_script('/etc/supervisord.conf')
        </pre>
        '''

        options = {'config_file': join(config_file_path, 'supervisord.conf')}
        result = self.update_file('supervisord.init.template', '/etc/init.d/supervisord', owner=self.context['owner'], options=options, sudo=True)

        if result:
            self.execute('chmod +x /etc/init.d/supervisord', stdout=False, sudo=True)
            self.execute('update-rc.d supervisord defaults', stdout=False, sudo=True)
            self.ensure_restart()

    def ensure_config_update(self):
        '''
        Makes sure that the config file is updated upon cleanup.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import SupervisorRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(SupervisorRole) as role:
                    role.ensure_config_update()
        </pre>
        '''

        self.context[MUST_UPDATE_CONFIG_KEY] = True

    def config(self,
               config_file_directory=None,
               log_folder='/var/log',
               log_file_max_mb=50,
               log_file_backups=10,
               log_level='info',
               pidfile='/var/run/supervisord.pid',
               user=None):
        '''
        Configures supervisor by creating a supervisord.conf file at the specified location.
        <em>Parameters</em>
        config_file_directory - directory to create the supervisord.conf file at the server.
        log_folder - path where log files will be created by supervisor. Defaults to /var/log (if you use the default, make sure your user has access).
        log_file_max_mb - Maximum size of log file in megabytes. Defaults to 50.
        log_file_backups - Number of log backups that supervisor keeps. Defaults to 10.
        log_level - Level of logging for supervisor. Defaults to 'info'.
        pidfile - Path for the pidfile that supervisor creates for itself. Defaults to /var/run/supervisor.pid (if you use the default, make sure your user has access).
        user - User that runs supervisor. Defaults to the last created user.

        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import SupervisorRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(SupervisorRole) as role:
                    role.config(
                        config_file_directory='/home/backend',
                        log_folder='/home/backend/logs',
                        pidfile='/home/backend/supervisord.pid',
                        user='backend'
                    )
        </pre>
        '''
        self.log_folder = log_folder
        self.config_file_directory = config_file_directory,
        self.log_folder = log_folder
        self.log_file_max_mb = log_file_max_mb
        self.log_file_backups = log_file_backups
        self.log_level = log_level
        self.pidfile = pidfile
        self.user = user

        if config_file_directory is None:
            config_file_directory = '/home/%s' % self.context['owner']
        if user is None:
            user = self.context['owner']

        self.context[CONFIG_KEY] = {
            'config_file_directory': config_file_directory,
            'log_file': join(log_folder, 'supervisord.log'),
            'log_file_max_mb': log_file_max_mb,
            'log_file_backups': log_file_backups,
            'log_level': log_level,
            'pidfile': pidfile,
            'user': user
        }

        self.ensure_config_update()

    def with_program(self, name):
        '''
        Enters a with block with a Program variable that allows you to configure a program entry in supervisord.conf.
        <em>Parameters</em>
        name - name of the program being supervised.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import SupervisorRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(SupervisorRole) as role:
                    with role.with_program('website') as program:
                        program.directory = '/home/backend/provy/tests/functional'
                        program.command = 'python website.py 800%(process_num)s'
                        program.number_of_processes = 4
                        program.log_folder = '/home/backend/logs'
        </pre>
        '''
        return WithProgram(self, name)

    def update_config_file(self):
        '''
        Updates the config file to match the configurations done under the <em>config</em> method.
        There's no need to call this method after config, since SupervisorRole cleanup will call it for you.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import SupervisorRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(SupervisorRole) as role:
                    role.update_config_file()
        </pre>
        '''
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
        '''
        Updates the config file and/or init files and restarts supervisor if needed.
        There's no need to call this method since provy's lifecycle will make sure it is called.
        '''

        if MUST_UPDATE_CONFIG_KEY in self.context and self.context[MUST_UPDATE_CONFIG_KEY]:
            self.update_init_script(self.context[CONFIG_KEY]['config_file_directory'])
            self.update_config_file()

        if MUST_RESTART_KEY in self.context and self.context[MUST_RESTART_KEY]:
            self.restart()

    def ensure_restart(self):
        '''
        Makes sure supervisor is restarted on cleanup.
        There's no need to call this method since it will be called when changes occur by the other methods.
        '''

        self.context[MUST_RESTART_KEY] = True

    def restart(self):
        '''
        Forcefully restarts supervisor.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import SupervisorRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(SupervisorRole) as role:
                    role.restart()
        </pre>
        '''
        if not self.is_process_running('supervisord'):
            command = '/etc/init.d/supervisord start'
        else:
            command = '/etc/init.d/supervisord restart'
        self.execute(command, sudo=True)
