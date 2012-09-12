from contextlib import contextmanager
import os

from provy.core import Role


class VirtualenvRole(Role):
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
        from provy.more.debian import PipRole

        with self.using(PipRole) as pip:
            pip.ensure_package_installed('virtualenv')
            pip.ensure_package_installed('virtualenvwrapper')

    def create_env(self, env_name):
        env_dir = os.path.join(self.base_directory, env_name)
        self.execute('virtualenv %s' % env_dir)
        return env_dir
