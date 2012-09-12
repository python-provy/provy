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
    <em>Context manager parameters</em>
    env_name - name of the virtual environment to be created and to keep activated when running commands inside the context manager.
    <em>Properties</em>
    base_directory - directory where the virtual environment subdirectory will be put at. For example, if you set it as "/home/johndoe/my_envs", and use venv("some_env"), it will create a virtual environment at "/home/johndoe/my_envs/some_env". Defaults to $HOME/.virtualenvs .
    <em>Sample usage</em>
    <pre class="sh_python">
    from provy.core import Role
    from provy.more.debian import VirtualenvRole

    class MySampleRole(Role):
        def provision(self):

            # this example uses the defaults provided
            with self.using(PipRole) as pip, self.using(VirtualenvRole) as venv, venv('fancylib'):
                pip.ensure_package_installed('django')

            # this is when you want to set a different base virtualenv directory
            with self.using(PipRole) as pip, self.using(VirtualenvRole) as venv:
                venv.base_directory = '/home/johndoe/Envs'
                with venv('fancylib2'):
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

    @contextmanager
    def __call__(self, env_name):
        from fabric.api import prefix

        env_dir = self.create_env(env_name)

        with prefix('source %s/bin/activate' % env_dir):
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

    def create_env(self, env_name):
        '''
        Creates a virtual environment.
        <em>Parameters</em>
        env_name - name of the virtual environment to be created.
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
        env_dir = os.path.join(self.base_directory, env_name)
        self.execute('virtualenv %s' % env_dir)
        return env_dir
