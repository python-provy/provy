from io import StringIO
import json
from operator import itemgetter

__author__ = 'jb'

from provy.core import Role

class VersionedRole(Role):

    """
        Something that supports versioned provisioning. We have set of computers with the same desired configuration.
        The problem is that this configuration changes in time. And from time to time provisioning may fail on
        some machines (because of other peoples sysystem modifications), so we need to keep track on what role
        had been provisioned succesfully.

        The idea is that this role stores a list of roles that can be provisioned with associated numeric versions.
        These roles are executed one by another, in order of ascending versions. After role is executed succesfully
        information about it is stored on the server.

        If we rerun this role on the same server it will only execute new roles.
    """

    initial_version = 0

    version_file = "/etc/provisioned_version"
    """
        File that stores last executed role
    """

    versioned_roles = tuple([])
    """
        A touple of two-touples that maps numeric role_id to role instance that provisions system
    """



    @property
    def ordered_roles(self):
        return sorted(self.versioned_roles, key=itemgetter(0))

    @property
    def current_version(self):
        if not self.remote_exists(self.version_file):
            return self.initial_version
        data = json.loads(self.read_remote_file(self.version_file))
        return data['last_version']

    def prepare_data_dict(self, version = None):
        if version is None:
            version = self.current_version
        return {
            "last_version" : version
        }

    def save_version_file(self, version = None):
        self.put_file(StringIO(unicode(json.dumps(self.prepare_data_dict(version)))), to_file=self.version_file, owner="root:root")
        self.change_dir_mode(self.version_file, 644)

    def execute_role(self, role, version):
        if isinstance(role, type):
            with self.using(role):
                pass
        else:
            role.provision()
        self.save_version_file(version)

    def provision(self):
        version = self.current_version
        for ver, role in self.ordered_roles:
            if version < ver:
                self.execute_role(role, ver)

