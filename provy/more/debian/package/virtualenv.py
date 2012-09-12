import os

from provy.core import Role


class VirtualenvRole(Role):
    def __init__(self, prov, context):
        super(VirtualenvRole, self).__init__(prov, context)
        self.user = context['user']
        self.base_directory = os.path.join(self.__get_user_dir(), 'Envs')

    def __get_user_dir(self):
        if self.user == 'root':
            return '/root'
        else:
            return '/home/%s' % self.user
