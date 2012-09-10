#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to provide PostgreSQL database management utilities for Debian distributions.
'''

from provy.core import Role
from provy.more.debian.package.aptitude import AptitudeRole


class PostgreSQLRole(Role):
    def provision(self):
        with self.using(AptitudeRole) as role:
            role.ensure_package_installed('postgresql')
            role.ensure_package_installed('postgresql-server-dev-9.1')

    def create_user(self, username, ask_password=True):
        pass_prompt_arg = "-P " if ask_password else ""
        return self.execute("createuser %s%s" % (pass_prompt_arg, username), stdout=False)

    def drop_user(self, username):
        return self.execute("dropuser %s" % username, stdout=False)

    def user_exists(self, username):
        return self.execute("psql -tAc \"SELECT 1 FROM pg_roles WHERE rolname='%s'\"" % username, stdout=False)

    def ensure_user(self, username):
        if not self.user_exists(username):
            return self.create_user(username)
        return True

    def create_database(self, database, owner=None):
        owner_arg = " -O %s" % owner if owner is not None else ""
        return self.execute("createdb %s%s" % (database, owner_arg), stdout=False)

    def drop_database(self, database):
        return self.execute("dropdb %s" % database, stdout=False)

    def database_exists(self, database):
        return self.execute('psql -tAc "\l" | grep "%s"' % database, stdout=False)

    def ensure_database(self, database):
        if not self.database_exists(database):
            return self.create_database(database)
        return True
