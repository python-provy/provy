#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to provide PostgreSQL database management utilities for Debian distributions.
'''
from StringIO import StringIO

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

    def execute_script(self, database, script):
        """
            Executes sql snippet via psql command. It is safer tha


        """
        self.execute_script_file(database, StringIO(script))



    def execute_script_file(self, database, local_script_file):
        sql = self.create_temp_file()
        self.put_file(local_script_file, sql, sudo=True, stdout=False)
        self.change_file_owner(sql, "postgres")
        self.execute("psql -f {temp_file} {database}".format(temp_file = sql, database = database), user="postgres")
        self.remove_file(sql, sudo = True, stdout=False)



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

    def __execute(self, command, stdout=True):
        return self.execute(command, stdout=stdout, sudo=True, user='postgres')

    def create_user(self, username, password, is_superuser=False, can_create_databases=False, can_create_roles=False):
        """
        Creates a user for the database.
        <em>Parameters</em>
        username - name of the user to be created.
        ask_password - if False, doesn't ask for the user password now. Defaults to True, which makes the role prompt for the password. Defaults to True.
        is_superuser - if True, creates as a superuser and ignores can_create_databases and can_create_roles arguments (as they would be implicit). Defaults to False.
        can_create_databases - if True, gives database creation privilege to the user. Defaults to False.
        can_create_roles - if True, gives this user privilege to create other users. Defaults to False.
        <em>Sample usage</em>
        <pre class="sh_python">
            class MySampleRole(Role):
                def provision(self):
                    with self.using(PostgreSQLRole) as role:
                        role.create_user("john", ask_password=False)
        </pre>
        """

        script_parts = []
        script_parts.append("CREATE USER")
        script_parts.append('"{}"'.format(username))
        script_parts.append("WITH")
        if is_superuser:
            script_parts.append("SUPERUSER")
        else:
            script_parts.append("NOSUPERUSER")
        if can_create_databases:
            script_parts.append("CREATEDB")
        else:
            script_parts.append("NOCREATEDB")
        if password:
            script_parts.append("PASSWORD '{}'".format(password))
        if can_create_roles:
            raise ValueError("Can create roles attribute for now is unsupported")
        self.execute_script("postgres", " ".join(script_parts))

    def __collect_user_creation_args(self, ask_password, is_superuser, can_create_databases, can_create_roles):
        creation_args = []
        if ask_password:
            creation_args.append('P')
        creation_args.append('S' if not is_superuser else 's')
        if not is_superuser:
            creation_args.append('D' if not can_create_databases else 'd')
            creation_args.append('R' if not can_create_roles else 'r')
        return creation_args

    def drop_user(self, username, ignore_if_not_exists =False):
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
        script = ["DROP USER"]

        if ignore_if_not_exists:
            script.append("IF EXISTS")
        script.append(username)
        script.append(";")

        self.execute_script("postgres",  " ".join(script))

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
        return bool(self.__execute("psql -tAc \"SELECT 1 FROM pg_roles WHERE rolname='%s'\"" % username, stdout=False))

    def ensure_user(self, username, ask_password=True, is_superuser=False, can_create_databases=False, can_create_roles=False):
        '''
        Ensures that a user exists in the database. If it doesn't, create it.
        <em>Parameters</em>
        username - name of the user to be checked/created.
        ask_password - if False, doesn't ask for the user password now. Defaults to True, which makes the role prompt for the password.
        is_superuser - if True, creates as a superuser and ignores can_create_databases and can_create_roles arguments (as they would be implicit). Defaults to False.
        can_create_databases - if True, gives database creation privilege to the user. Defaults to False.
        can_create_roles - if True, gives this user privilege to create other users. Defaults to False.
        <em>Sample usage</em>
        <pre class="sh_python">
            class MySampleRole(Role):
                def provision(self):
                    with self.using(PostgreSQLRole) as role:
                        role.ensure_user("john", ask_password=False)
        </pre>
        '''
        if not self.user_exists(username):
            self.log('User "%s" does not exist yet. Creating...' % username)
            return self.create_user(username, ask_password, is_superuser, can_create_databases, can_create_roles)
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
        return self.__execute("createdb %s%s" % (database, owner_arg))

    def drop_database(self, database, ignore_if_not_exists =False):
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
        script = ["DROP DATABASE"]
        if ignore_if_not_exists:
            script.append("IF EXISTS")
        script.append(database)
        return self.execute_script("postgres", " ".join(script))

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
        return bool(self.__execute('psql -tAc "SELECT 1 from pg_database WHERE datname=\'%s\'"' % database, stdout=False))

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
            self.log('Database "%s" does not exist yet. Creating...' % database)
            return self.create_database(database, owner)
        return True
