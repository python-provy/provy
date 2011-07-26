#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to provide Django app server utility methods for Debian distributions.
'''

from os.path import dirname, join, splitext, split

from provy.core import Role
from provy.more.debian.package.pip import PipRole
from provy.more.debian.package.aptitude import AptitudeRole
from provy.more.debian.monitoring.supervisor import SupervisorRole

SITES_KEY = 'django-sites'
MUST_RESTART_KEY = 'restart-django-sites'


class WithSite(object):
    def __init__(self, django, name):
        self.django = django
        self.auto_start = True
        self.daemon = True
        self.name = name
        self.settings_path = None
        self.host = '0.0.0.0'
        self.pid_file_path = '/var/run'
        self.threads = 1
        self.processes = 1
        self.starting_port = 8000
        self.user = None
        if SupervisorRole in self.django.context['roles_in_context']:
            self.use_supervisor = True
            self.supervisor_log_folder = self.django.context['roles_in_context'][SupervisorRole].log_folder
        else:
            self.use_supervisor = False
            self.supervisor_log_folder = '/var/log'

        self.settings = {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if not self.settings_path:
            raise RuntimeError('[Django] The path to the site must be specified and should correspond to the directory where the settings.py file is for site %s.' % self.name)

        if SITES_KEY not in self.django.context:
            self.django.context[SITES_KEY] = []

        if self.use_supervisor:
            self.daemon = False
            self.auto_start = False
            self.django.restart_supervisor_on_changes = True

        self.django.context[SITES_KEY].append(self)


class DjangoRole(Role):
    '''
    This role provides Django app server management utilities for Debian distributions.
    When running Django under supervisor, remember to set <em>restart_supervisor_on_changes</em> to True.
    If you choose to automatically include supervisor support in your sites, don't forget to call <em>SupervisorRole</em> config method.
    When creating a new site using <em>with role.create_site('somesite') as site</em> these are the properties available in the site object:
    <em>auto_start</em> - Indicates whether the site should be automatically started by the operating system. Defaults to True. If using supervisor, explicitly set this to False.
    <em>daemon</em> - Indicates whether the init.d command for the website should daemonize itself. Defaults to True. If using supervisor, explicitly set this to False.
    <em>settings_path</em> - This is the only mandatory argument. This is the full path to django's settings.py file.
    <em>host</em> - The host IP address that django will listen to incoming requests. Defaults to '0.0.0.0'.
    <em>starting_port</em> - The first port that Django will be started in the event that more than one process is used. Defaults to 8000.
    <em>processes</em> - The number of processes that will have commands created at the server. As an example, if this is set to 2 and the name of the site is 'website', two commands will be created: /etc/init.d/website-8000 and /etc/init.d/website-8001. Defaults to 1.
    <em>pid_file_path</em> - Path to create the pid file. Defaults to '/var/run'.
    <em>threads</em> - Number of worker threads that Green Unicorn will use when spawning Django. Defaults to 1.
    <em>user</em> - User that gunicorn will run under. Defaults to the last created user. When using supervisor it is VERY important that this user is the same user as supervisor's.
    <em>use_supervisor</em> - States that supervisor configuration for these django website should be automatically included.
    <em>supervisor_log_folder</em> - Log folder that supervisor will store the configurations for this site.
    <em>settings</em> - Dictionary with settings that will overwrite Django's defaults. These settings will be included in a local_settings.py module that imports the original settings as KEY=value pairs. All values included here will have their string representation used in the local_settings.

    <em>Sample usage</em>
    <pre class="sh_python">
    from provy.core import Role
    from provy.more.debian import DjangoRole

    class MySampleRole(Role):
        def provision(self):
            with self.using(SupervisorRole) as role:
                role.config(
                    config_file_directory='/home/someuser',
                    log_file='/home/someuser/logs/supervisord.log',
                    user='myuser'
                )

            with self.using(DjangoRole) as role:
                role.restart_supervisor_on_changes = True
                with role.create_site('mysite') as site:
                    site.path = '/some/folder/with/settings.py'
                    site.use_supervisor = True
                    site.supervisor_log_path = '/some/folder/to/log'
                    site.threads = 4
                    site.processes = 2
                    site.user = 'myuser'
                    # settings that override the website defaults.
                    site.settings = {

                    }
    </pre>
    '''
    def __init__(self, prov, context):
        super(DjangoRole, self).__init__(prov, context)
        self.restart_supervisor_on_changes = False

    def provision(self):
        '''
        Installs Django and its dependencies. This method should be called upon if overriden in base classes, or Django won't work properly in the remote server.
        If you set a variable called django-version in the context, that version of django will be installed instead of latest.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import DjangoRole

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
        self.register_template_loader('provy.more.debian.web')

        with self.using(AptitudeRole) as role:
            role.ensure_package_installed('python-mysqldb')

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
        from provy.core import Role
        from provy.more.debian import DjangoRole

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

    def cleanup(self):
        '''
        Updates the website and/or init files and restarts websites if needed.
        There's no need to call this method since provy's lifecycle will make sure it is called.
        '''

        if SITES_KEY in self.context:
            for website in self.context[SITES_KEY]:
                updated = self.__update_init_script(website)
                settings_updated = self.__update_settings(website)
                if website.use_supervisor:
                    self.__update_supervisor_program(website)
                if updated or settings_updated:
                    self.__ensure_restart(website)

        if MUST_RESTART_KEY in self.context and self.context[MUST_RESTART_KEY]:
            if self.restart_supervisor_on_changes:
                with self.using(SupervisorRole) as role:
                    role.ensure_restart()
            for site in self.context[MUST_RESTART_KEY]:
                self.__restart(site)

    def __update_supervisor_program(self, website):
        with self.using(SupervisorRole) as role:
            for process_number in range(website.processes):
                port = website.starting_port + process_number
                script_name = "%s-%d" % (website.name, port)
                with role.with_program(script_name) as program:
                    program.directory = dirname(website.settings_path)
                    program.command = '/etc/init.d/%s start' % script_name
                    program.name = script_name
                    program.number_of_processes = 1
                    program.user = website.user
                    program.log_folder = website.supervisor_log_folder

    def __ensure_restart(self, website):
        if not MUST_RESTART_KEY in self.context:
            self.context[MUST_RESTART_KEY] = []
        self.context[MUST_RESTART_KEY].append(website)

    def __restart(self, website):
        if not website.auto_start:
            return
        for process_number in range(website.processes):
            port = website.starting_port + process_number
            script_name = "%s-%d" % (website.name, port)
            if self.remote_exists(join(website.pid_file_path.rstrip('/'), '%s_%s.pid' % (website.name, port))):
                self.execute('/etc/init.d/%s stop' % script_name, stdout=False, sudo=True)
            self.execute('/etc/init.d/%s start' % script_name, stdout=False, sudo=True)

    def __update_settings(self, website):
        local_settings_path = join(dirname(website.settings_path), 'local_settings.py')
        options = {
            'settings_file': splitext(split(website.settings_path)[-1])[0],
            'settings': website.settings
        }
        result = self.update_file('local.settings.template', local_settings_path, owner=website.user, options=options, sudo=True)
        return result

    def __update_init_script(self, website):
        at_least_one_updated = False
        for process_number in range(website.processes):
            port = website.starting_port + process_number
            options = {
                'name': website.name,
                'pid_file_path': website.pid_file_path.rstrip('/'),
                'user': website.user,
                'host': website.host,
                'port': port,
                'threads': website.threads,
                'daemon': website.daemon,
                'user': website.user,
                'settings_directory': dirname(website.settings_path)
            }
            script_name = '%s-%d' % (website.name, port)
            result = self.update_file('website.init.template', '/etc/init.d/%s' % script_name, owner=website.user, options=options, sudo=True)

            if result:
                at_least_one_updated = True
                self.execute('chmod +x /etc/init.d/%s' % script_name, stdout=False, sudo=True)
                if website.auto_start:
                    self.execute('update-rc.d %s defaults' % script_name, stdout=False, sudo=True)

        return at_least_one_updated
