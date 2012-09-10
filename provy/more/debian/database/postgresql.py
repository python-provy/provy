#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to provide PostgreSQL database management utilities for Debian distributions.
'''

from provy.core import Role
from provy.more.debian.package.aptitude import AptitudeRole


class PostgreSQLRole(Role):
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
            role.ensure_package_installed('postgresql-server-dev-9.1')

    def __execute(self, command, stdout=False):
        if not stdout:
            self.log(command)
        return self.execute(command, stdout=stdout, sudo=True, user='postgres')

    def create_user(self, username, ask_password=True):
        '''
        Creates a user for the database.
        <em>Parameters</em>
        username - name of the user to be created.
        ask_password - if False, doesn't ask for the user password now. Defaults to True, which makes the role prompt for the password.
        <em>Sample usage</em>
        <pre class="sh_python">
            class MySampleRole(Role):
                def provision(self):
                    with self.using(PostgreSQLRole) as role:
                        role.create_user("john", ask_password=False)
        </pre>
        '''
        pass_prompt_arg = "-P " if ask_password else ""
        return self.__execute("createuser %s%s" % (pass_prompt_arg, username), stdout=True)

    def drop_user(self, username):
        '''
        Drops a user from the database.
        <em>Parameters</em>
        username - name of the user to be dropped.
        <em>Sample usage</em>
        <pre class="sh_python">
            class MySampleRole(Role):
                def provision(self):
                    with self.using(PostgreSQLRole) as role:
                        role.drop_user("john")
        </pre>
        '''
        return self.__execute("dropuser %s" % username, stdout=True)

    def user_exists(self, username):
        '''
        Checks if a user exists in the database.
        <em>Parameters</em>
        username - name of the user to be checked.
        <em>Sample usage</em>
        <pre class="sh_python">
            class MySampleRole(Role):
                def provision(self):
                    with self.using(PostgreSQLRole) as role:
                        role.user_exists("john") # True or False
        </pre>
        '''
        return bool(self.__execute("psql -tAc \"SELECT 1 FROM pg_roles WHERE rolname='%s'\"" % username))

    def ensure_user(self, username, ask_password=True):
        '''
        Ensures that a user exists in the database. If it doesn't, create it.
        <em>Parameters</em>
        username - name of the user to be checked/created.
        ask_password - if False, doesn't ask for the user password now. Defaults to True, which makes the role prompt for the password.
        <em>Sample usage</em>
        <pre class="sh_python">
            class MySampleRole(Role):
                def provision(self):
                    with self.using(PostgreSQLRole) as role:
                        role.ensure_user("john", ask_password=False)
        </pre>
        '''
        if not self.user_exists(username):
            return self.create_user(username, ask_password)
        return True

    def create_database(self, database, owner=None):
        '''
        Creates a database.
        <em>Parameters</em>
        database - name of the database to be created.
        owner - the database owner. If not provided, will be the Postgres default.
        <em>Sample usage</em>
        <pre class="sh_python">
            class MySampleRole(Role):
                def provision(self):
                    with self.using(PostgreSQLRole) as role:
                        role.create_database("foo", owner="john")
        </pre>
        '''
        owner_arg = " -O %s" % owner if owner is not None else ""
        return self.__execute("createdb %s%s" % (database, owner_arg), stdout=True)

    def drop_database(self, database):
        '''
        Drops a database.
        <em>Parameters</em>
        database - name of the database to be dropped.
        <em>Sample usage</em>
        <pre class="sh_python">
            class MySampleRole(Role):
                def provision(self):
                    with self.using(PostgreSQLRole) as role:
                        role.drop_database("foo")
        </pre>
        '''
        return self.__execute("dropdb %s" % database, stdout=True)

    def database_exists(self, database):
        '''
        Checks if a database exists.
        <em>Parameters</em>
        database - name of the database to be checked.
        <em>Sample usage</em>
        <pre class="sh_python">
            class MySampleRole(Role):
                def provision(self):
                    with self.using(PostgreSQLRole) as role:
                        role.database_exists("foo") # True or False
        </pre>
        '''
        return bool(self.__execute('psql -tAc "\l" | grep "%s"' % database))

    def ensure_database(self, database, owner=None):
        '''
        Ensures that a database exists. If it doesn't, create it.
        <em>Parameters</em>
        database - name of the database to be checked/created.
        owner - the database owner. If not provided, will be the Postgres default.
        <em>Sample usage</em>
        <pre class="sh_python">
            class MySampleRole(Role):
                def provision(self):
                    with self.using(PostgreSQLRole) as role:
                        role.ensure_database("foo", owner="john")
        </pre>
        '''
        if not self.database_exists(database):
            return self.create_database(database, owner)
        return True
