import os

from provy.core import Role


class VirtualenvRole(Role):
    def __init__(self, prov, context):
        super(VirtualenvRole, self).__init__(prov, context)
        self.base_directory = os.path.join(os.path.expanduser('~'), 'Envs')