#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to provide virtualenvs and run commands inside a virtualenv, for Debian distributions.
'''

from contextlib import contextmanager
import os

from provy.core import Role


class VirtualenvRole(Role):
    '''
    This role provides virtualenv management. It also provides virtualenvwrapper provisioning, although it's not internally used in this role.
    When using the object as a context manager (that is, using a "with" block) it will make sure that the virtual environment is created and that the commands that run inside it run within this same virtual environment (which affects, for example, the python and pip commands).
    If the virtual environment already exists, it just bypasses the creation procedure.
    <em>Context manager parameters</em>
    env_name - name of the virtual environment to be created and to keep activated when running commands inside the context manager.
    system_site_packages - if True, will include system-wide site-packages in the virtual environment. Defaults to False.
    <em>Properties</em>
    base_directory - directory where the virtual environment subdirectory will be put at. For example, if you set it as "/home/johndoe/my_envs", and use venv("some_env"), it will create a virtual environment at "/home/johndoe/my_envs/some_env". Defaults to $HOME/.virtualenvs .
    user - the user with which the virtual environment should be created. Defaults to the context user.
    <em>Sample usage</em>
    <pre class="sh_python">
    from provy.core import Role
    from provy.more.debian import VirtualenvRole

    class MySampleRole(Role):
        def provision(self):

            # this example uses the defaults provided
            with self.using(PipRole) as pip, self.using(VirtualenvRole) as venv, venv('fancylib'):
                pip.ensure_package_installed('django')

            # this is when you want to set a different base virtualenv directory and user, and include the system-wide site-packages.
            with self.using(PipRole) as pip, self.using(VirtualenvRole) as venv:
                venv.base_directory = '/home/johndoe/Envs'
                venv.user = 'johndoe'
                with venv('fancylib2', system_site_packages=True):
                    pip.ensure_package_installed('tornado')
    </pre>
    '''

    def __init__(self, prov, context):
        super(VirtualenvRole, self).__init__(prov, context)
        self.user = context['user']
        self.base_directory = os.path.join(self.__get_user_dir(), '.virtualenvs')

    def __get_user_dir(self):
        if self.user == 'root':
            return '/root'
        else:
            return '/home/%s' % self.user

    def env_dir(self, env_name):
        '''
        Gets the virtual environment directory for a given environment name.
        Please note that this doesn't check if the env actually exists.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import VirtualenvRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(VirtualenvRole) as venv, venc('fancylib'):
                    self.env_dir('fancylib')
        </pre>
        '''
        return os.path.join(self.base_directory, env_name)

    @contextmanager
    def __call__(self, env_name, system_site_packages=False):
        from fabric.api import prefix

        if not self.env_exists(env_name):
            self.create_env(env_name, system_site_packages=system_site_packages)

        with prefix('source %s/bin/activate' % self.env_dir(env_name)):
            yield

    def provision(self):
        '''
        Installs virtualenv and virtualenvwrapper, and their dependencies. This method should be called upon if overriden in base classes, or virtualenv won't work properly in the remote server.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import VirtualenvRole

        class MySampleRole(Role):
            def provision(self):
                self.provision_role(VirtualenvRole) # does not need to be called if using with block.
        </pre>
        '''

        from provy.more.debian import PipRole

        with self.using(PipRole) as pip:
            pip.ensure_package_installed('virtualenv')
            pip.ensure_package_installed('virtualenvwrapper')

    def create_env(self, env_name, system_site_packages=False):
        '''
        Creates a virtual environment.
        <em>Parameters</em>
        env_name - name of the virtual environment to be created.
        system_site_packages - if True, will include system-wide site-packages in the virtual environment. Defaults to False.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import VirtualenvRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(VirtualenvRole) as venv:
                    env_dir = venv.create_env('fancylib') # will return the directory where the virtual environment was created
        </pre>
        '''
        env_dir = self.env_dir(env_name)
        site_packages_arg = '--system-site-packages ' if system_site_packages else ''
        self.execute('virtualenv %s%s' % (site_packages_arg, env_dir), user=self.user)
        return env_dir

    def env_exists(self, env_name):
        '''
        Checks if a virtual environment exists.
        <em>Parameters</em>
        env_name - name of the virtual environment to be checked.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import VirtualenvRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(VirtualenvRole) as venv:
                    venv.env_exists('fancylib') # True or False
        </pre>
        '''
        return self.remote_exists_dir(self.env_dir(env_name))
