#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to provide PostgreSQL database management utilities for Debian distributions.
'''

from provy.more.base.database.postgresql import BasePostgreSQLRole
from provy.more.debian.package.aptitude import AptitudeRole


class PostgreSQLRole(BasePostgreSQLRole):
    '''
    This role provides PostgreSQL database management utilities for Debian distributions.
    <em>Sample usage</em>
    <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import PostgreSQLRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(PostgreSQLRole) as role:
                    role.ensure_user("john")
                    role.ensure_database("foo", owner="john")

    </pre>
    '''
    def provision(self):
        '''
        Installs PostgreSQL and its dependencies. This method should be called upon if overriden in base classes, or PostgreSQL won't work properly in the remote server.
        <em>Sample usage</em>
        <pre class="sh_python">
            class MySampleRole(Role):
                def provision(self):
                    self.provision_role(PostgreSQLRole) # no need to call this if using with block.
        </pre>
        '''
        with self.using(AptitudeRole) as role:
            role.ensure_package_installed('postgresql')
            role.ensure_package_installed('postgresql-server-dev-%s' % self.__get_version())

    def __get_version(self):
        distro = self.get_distro_info()
        if distro.distributor_id.lower() == 'ubuntu':
            version = '9.1'
        else:
            version = '8.4'
        return version
