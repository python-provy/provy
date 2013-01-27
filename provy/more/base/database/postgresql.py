#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to provide `PostgreSQL <http://www.postgresql.org/>`_ database management utilities.
'''

from provy.core import Role


class BasePostgreSQLRole(Role):
    def provision(self):
        '''
        This method should be implemented by the concrete PostgreSQLRole classes, according to each provisioning steps for each distribution.

        :raise: NotImplementedError
        '''
        raise NotImplementedError

    def _execute(self, command, stdout=True):
        return self.execute(command, stdout=stdout, sudo=True, user='postgres')

    def create_user(self, username, ask_password=True, is_superuser=False, can_create_databases=False, can_create_roles=False):
        '''
        Creates a user for the database.

        :param username: Name of the user to be created.
        :type username: :class:`str`
        :param ask_password: If :data:`False`, doesn't ask for the user password now. Defaults to :data:`True`, which makes the role prompt for the password.
        :type ask_password: :class:`bool`
        :param is_superuser: If :data:`True`, creates as a superuser and ignores can_create_databases and can_create_roles arguments (as they would be implicit).
            Defaults to :data:`False`.
        :type is_superuser: :class:`bool`
        :param can_create_databases: If :data:`True`, gives database creation privilege to the user. Defaults to :data:`False`.
        :type can_create_databases: :class:`bool`
        :param can_create_roles: If :data:`True`, gives this user privilege to create other users. Defaults to :data:`False`.
        :type can_create_roles: :class:`bool`

        :return: The result output of the execution.
        :rtype: :class:`str`

        Example:
        ::

            class MySampleRole(Role):
                def provision(self):
                    with self.using(PostgreSQLRole) as role:
                        role.create_user("john", ask_password=False)
        '''
        creation_args = self.__collect_user_creation_args(ask_password, is_superuser, can_create_databases, can_create_roles)
        return self._execute("createuser -%s %s" % (''.join(creation_args), username))

    def __collect_user_creation_args(self, ask_password, is_superuser, can_create_databases, can_create_roles):
        creation_args = []
        if ask_password:
            creation_args.append('P')
        creation_args.append('S' if not is_superuser else 's')
        if not is_superuser:
            creation_args.append('D' if not can_create_databases else 'd')
            creation_args.append('R' if not can_create_roles else 'r')
        return creation_args

    def drop_user(self, username):
        '''
        Drops a user from the database.

        :param username: Name of the user to be dropped.
        :type username: :class:`str`

        :return: The result output of the execution.
        :rtype: :class:`str`

        Example:
        ::

            class MySampleRole(Role):
                def provision(self):
                    with self.using(PostgreSQLRole) as role:
                        role.drop_user("john")
        '''
        return self._execute("dropuser %s" % username)

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

    def ensure_user(self, username, ask_password=True, is_superuser=False, can_create_databases=False, can_create_roles=False):
        '''
        Ensures that a user exists in the database. If it doesn't, create it.

        :param username: Name of the user to be checked/created.
        :type username: :class:`str`
        :param ask_password: If :data:`False`, doesn't ask for the user password now. Defaults to :data:`True`, which makes the role prompt for the password.
        :type ask_password: :class:`bool`
        :param is_superuser: If :data:`True`, creates as a superuser and ignores can_create_databases and can_create_roles arguments (as they would be implicit).
            Defaults to :data:`False`.
        :type is_superuser: :class:`bool`
        :param can_create_databases: If :data:`True`, gives database creation privilege to the user. Defaults to :data:`False`.
        :type can_create_databases: :class:`bool`
        :param can_create_roles: If :data:`True`, gives this user privilege to create other users. Defaults to :data:`False`.
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
            return self.create_user(username, ask_password, is_superuser, can_create_databases, can_create_roles)
        return True

    def create_database(self, database, owner=None):
        '''
        Creates a database.

        :param database: Name of the database to be created.
        :type database: :class:`str`
        :param owner: The database owner. If not provided, will be the Postgres default.
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
        owner_arg = " -O %s" % owner if owner is not None else ""
        return self._execute("createdb %s%s" % (database, owner_arg))

    def drop_database(self, database):
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
        return self._execute("dropdb %s" % database)

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
        :param owner: The database owner. If not provided, will be the Postgres default.
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
