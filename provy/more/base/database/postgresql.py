# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to provide
`PostgreSQL <http://www.postgresql.org/>`_ database management utilities.
'''

import getpass
from provy.core import Role

from StringIO import StringIO


class BasePostgreSQLRole(Role):
    '''
    This role provides PostgreSQL database management utilities for most os.

    This role assumes that:

    * There is a remote shell command psql
    * Administrative user is postgres
    * Administrative database is named postgres
    '''

    def execute_script(self, database, script):
        """
            Executes sql snippet via psql command.

        """
        self.execute_script_file(database, StringIO(script))

    def execute_script_file(self, database, local_script_file):
        sql = self.create_remote_temp_file(suffix="sql", cleanup=True)
        self.put_file(local_script_file, sql, sudo=True, stdout=False)
        self.change_path_owner(sql, "postgres")
        self.execute(
            "psql -f {temp_file} {database}".format(
                        temp_file=sql, database=database),
            user="postgres")
        self.remove_file(sql, sudo=True, stdout=False)

    def provision(self):
        '''
        This method should be implemented by the concrete PostgreSQLRole
         classes, according to each provisioning steps for each distribution.

        :raise: NotImplementedError
        '''
        raise NotImplementedError

    def _execute(self, command, stdout=True):
        return self.execute(command, stdout=stdout, sudo=True, user='postgres')

    def get_password(self, username):
        for ii in range(3):
            p = getpass.getpass(
                "Provide password for user {user}  while provisioning {host}"
                .format(
                    user=username,
                    host=self.context.get('host', "unknown")
                ))

            r = getpass.getpass("Repeat password")
            if p != r:
                print("Passwords did not match, repeat")
            else:
                return p
        else:
            print ("Number of tries exceeded, bailing out.")
            raise ValueError()

    def create_user(self, username, password=False, ask_password=True,
                    is_superuser=False, can_create_databases=False,
                    can_create_roles=False):
        """
        Creates a user for the database.

        :param username: Name of the user to be created.
        :type username: :class:`str`
        :param ask_password: If :data:`False`, doesn't ask for the user password
            now. Defaults to :data:`True`, which makes the role prompt
            for the password.
        :type ask_password: :class:`bool`
        :param is_superuser: If :data:`True`, creates as a superuser and ignores
         can_create_databases and can_create_roles
         arguments (as they would be implicit).
            Defaults to :data:`False`.
        :type is_superuser: :class:`bool`
        :param can_create_databases: If :data:`True`, gives database creation
            privilege to the user. Defaults to :data:`False`.
        :type can_create_databases: :class:`bool`
        :param can_create_roles: If :data:`True`, gives this user privilege to
        create other users. Defaults to :data:`False`.
        :type can_create_roles: :class:`bool`

        :return: The result output of the execution.
        :rtype: :class:`str`

        Example:
        ::

            class MySampleRole(Role):
                def provision(self):
                    with self.using(PostgreSQLRole) as role:
                        role.create_user("john", ask_password=False)
        """

        script_parts = []
        script_parts.append("CREATE USER")
        script_parts.append('"{}"'.format(username))
        script_parts.append("WITH")

        if not password and ask_password:
            password = self.get_password(username)
        if is_superuser:
            script_parts.append("SUPERUSER")
        else:
            script_parts.append("NOSUPERUSER")
        if not is_superuser:
            if can_create_databases:
                script_parts.append("CREATEDB")
            else:
                script_parts.append("NOCREATEDB")
            if can_create_roles:
                script_parts.append("CREATEROLE")
            else:
                script_parts.append("NOCREATEROLE")

        if password:
            script_parts.append("PASSWORD '{}'".format(password))
        script_parts.append(";")
        return self.execute_script("postgres", " ".join(script_parts))

    def drop_user(self, username, ignore_if_not_exists=False):
        '''
        Drops a user from the database.

        :param username: Name of the user to be dropped.
        :type username: :class:`str`

        :param ignore_if_not_exists: If set to True we will ignore if there is
        no user with this username.

        :return: The result output of the execution.
        :rtype: :class:`str`

        Example:
        ::
            class MySampleRole(Role):
                def provision(self):
                    with self.using(PostgreSQLRole) as role:
                        role.drop_user("john")
        </pre>
        '''
        script = ["DROP USER"]

        if ignore_if_not_exists:
            script.append("IF EXISTS")
        script.append('''"{}"'''.format(username))
        script.append(";")

        return self.execute_script("postgres", " ".join(script))

    def user_exists(self, username):
        '''
       Checks if a user exists in the database.

       :param username: Name of the user to be checked.
       :type username: :class:`str`

       :return: Whether the user exists or not.
       :rtype: :class:`bool`

       Example:
       ::

           class MySampleRole(Role):
               def provision(self):
                   with self.using(PostgreSQLRole) as role:
                       role.user_exists("john") # True or False
       '''
        return bool(self._execute("psql -tAc \"SELECT 1 FROM pg_roles WHERE rolname='%s'\"" % username, stdout=False))

    def ensure_user(self, username, password=None, ask_password=True,
                    is_superuser=False, can_create_databases=False,
                    can_create_roles=False):
        '''
        Ensures that a user exists in the database. If it doesn't, create it.

        :param username: Name of the user to be checked/created.
        :type username: :class:`str`
        :param password: Password for the created user.
        :param ask_password: If :data:`False`, doesn't ask for the user password
            now. Defaults to :data:`True`, which makes the role
            prompt for the password.
        :type ask_password: :class:`bool`
        :param is_superuser: If :data:`True`, creates as a superuser and
        ignores can_create_databases and can_create_roles arguments (as they
            would be implicit).
            Defaults to :data:`False`.
        :type is_superuser: :class:`bool`
        :param can_create_databases: If :data:`True`, gives database creation
            privilege to the user. Defaults to :data:`False`.
        :type can_create_databases: :class:`bool`
        :param can_create_roles: If :data:`True`, gives this user privilege
            to create other users. Defaults to :data:`False`.
        :type can_create_roles: :class:`bool`

        :return: The result output of the execution.
        :rtype: :class:`str`

        Example:
        ::

            class MySampleRole(Role):
                def provision(self):
                    with self.using(PostgreSQLRole) as role:
                        role.ensure_user("john", ask_password=False)
        '''
        if not self.user_exists(username):
            self.log('User "%s" does not exist yet. Creating...' % username)
            return self.create_user(username, password, ask_password,
                                    is_superuser, can_create_databases,
                                    can_create_roles)
        return True

    def create_database(self, database, owner=None):
        '''
        Creates a database.

        :param database: Name of the database to be created.
        :type database: :class:`str`
        :param owner: The database owner. If not provided,
            will be the Postgres default.
        :type owner: :class:`str`

        :return: The result output of the execution.
        :rtype: :class:`str`

        Example:
        ::

            class MySampleRole(Role):
                def provision(self):
                    with self.using(PostgreSQLRole) as role:
                        role.create_database("foo", owner="john")
        '''
        script = ["CREATE DATABASE", '"{}"'.format(database)]
        if owner:
            script.extend(("OWNER", '"{}"'.format(owner)))
        script.append(";")
        self.execute_script("postgres", " ".join(script))

    def drop_database(self, database, ignore_if_not_exists=False):
        '''
        Drops a database.

        :param database: Name of the database to be dropped.
        :type database: :class:`str`

        :return: The result output of the execution.
        :rtype: :class:`str`

        Example:
        ::

            class MySampleRole(Role):
                def provision(self):
                    with self.using(PostgreSQLRole) as role:
                        role.drop_database("foo")
        '''
        script = ["DROP DATABASE"]
        if ignore_if_not_exists:
            script.append("IF EXISTS")
        script.append('"{}"'.format(database))
        script.append(";")
        return self.execute_script("postgres", " ".join(script))

    def database_exists(self, database):
        '''
        Checks if a database exists.

        :param database: Name of the database to be checked.
        :type database: :class:`str`

        :return: Whether the database exists.
        :rtype: :class:`bool`

        Example:
        ::

            class MySampleRole(Role):
                def provision(self):
                    with self.using(PostgreSQLRole) as role:
                        role.database_exists("foo") # True or False
        '''
        return bool(self._execute('psql -tAc "SELECT 1 from pg_database WHERE datname=\'%s\'"' % database, stdout=False))

    def ensure_database(self, database, owner=None):
        '''
        Ensures that a database exists. If it doesn't, create it.

        :param database: Name of the database to be checked/created.
        :type database: :class:`str`
        :param owner: The database owner. If not provided, will be the
                        Postgres default.
        :type owner: :class:`str`

        :return: The result output of the execution.
        :rtype: :class:`str`

        Example:
        ::

            class MySampleRole(Role):
                def provision(self):
                    with self.using(PostgreSQLRole) as role:
                        role.ensure_database("foo", owner="john")
        '''
        if not self.database_exists(database):
            self.log('Database "%s" does not exist yet. Creating...' % database)
            return self.create_database(database, owner)
        return True
