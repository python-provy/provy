#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to provide `MySQL <http://www.mysql.com/>`_ database management utilities for CentOS distributions.
'''

import re

from provy.core import Role
from provy.more.centos.package.yum import YumRole


class MySQLRole(Role):
    '''
    This role provides `MySQL <http://www.mysql.com/>`_ database management utilities for CentOS distributions.

    This role uses two context keys: `mysql_root_user` and `mysql_root_pass`. If none are found, it uses 'root' and empty password.

    Example:
    ::

        from provy.core import Role
        from provy.more.centos import MySQLRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(MySQLRole) as role:
                    role.ensure_user(username=self.context['mysql_user'], identified_by=self.context['mysql_password'])
                    role.ensure_database(self.context['mysql_database'], owner=self.context['mysql_user'])
    '''
    def __init__(self, prov, context):
        super(MySQLRole, self).__init__(prov, context)
        self.mysql_root_user = 'mysql_root_user' in self.context and self.context['mysql_root_user'] or 'root'
        self.mysql_root_pass = 'mysql_root_pass' in self.context and self.context['mysql_root_pass'] or ''

    def provision(self):
        '''
        Installs `MySQL <http://www.mysql.com/>`_ Server and its dependencies.
        This method should be called upon if overriden in base classes, or MySQL won't work properly in the remote server.

        Example:
        ::

            class MySampleRole(Role):
                def provision(self):
                    self.provision_role(MySQLRole) # no need to call this if using with block.
        '''
        with self.using(YumRole) as role:

            role.ensure_up_to_date()

            result = role.ensure_package_installed('mysql-server')
            role.ensure_package_installed('mysql-devel')
            role.ensure_package_installed('mysql-libs')

            if result:
                self.log("setting root user %s password..." % self.mysql_root_user)
                self.execute("mysqladmin -u %s -p'temppass' password '%s'" % (self.mysql_root_user, self.mysql_root_pass), stdout=False, sudo=True)

    def __execute_non_query(self, query):
        pass_string = ""
        if self.mysql_root_pass:
            pass_string = '--password="%s" ' % self.mysql_root_pass

        self.execute('mysql -u %s %s-e "%s" mysql' % (self.mysql_root_user, pass_string, query), stdout=False, sudo=True)

    def __execute_query(self, query):
        pass_string = ""
        if self.mysql_root_pass:
            pass_string = '--password="%s" ' % self.mysql_root_pass

        result = self.execute('mysql -u %s %s-E -e "%s" mysql' % (self.mysql_root_user, pass_string, query), stdout=False, sudo=True)
        rows = self.__get_rows(result)

        return rows

    def __get_rows(self, result):
        index_re = re.compile('(\d+)[.]')
        items = []
        item = None
        for line in result.split('\n'):
            if not line.strip():
                continue
            if line.startswith('*'):
                if item:
                    items.append(item)
                item = {
                    'index': index_re.search(line).groups()[0]
                }
            else:
                key, value = line.split(':', 1)
                item[key.strip()] = value.strip()
        if item:
            items.append(item)

        return items

    def get_user_hosts(self, username):
        '''
        Returns all the available hosts that this user can login from.

        :param username: Name of the user to be verified.
        :type username: :class:`str`
        :return: The user hosts.
        :rtype: :class:`list`

        Example:
        ::

            class MySampleRole(Role):
                def provision(self):
                    with self.using(MySQLRole) as role:
                        if not '%' in role.get_user_hosts('someuser'):
                            pass
        '''
        users = self.__execute_query("select Host from mysql.user where LOWER(User)='%s'" % username.lower())
        hosts = []
        if users:
            for user in users:
                hosts.append(user['Host'])

        return hosts

    def user_exists(self, username, login_from='%'):
        '''
        Returns :data:`True` if the given user exists for the given location in mysql server.

        :param username: Name of the user to be verified.
        :type username: :class:`str`
        :param login_from: Locations that this user can login from. Defaults to '%' (anywhere).
        :type login_from: :class:`str`
        :return: Whether the user exists.
        :rtype: :class:`bool`

        Example:
        ::

            class MySampleRole(Role):
                def provision(self):
                    with self.using(MySQLRole) as role:
                        if not role.user_exists('someuser'):
                            pass
        '''
        return login_from in self.get_user_hosts(username)

    def ensure_user(self, username, identified_by, login_from='%'):
        '''
        Ensure the given user is created in the database and can login from the specified location.

        :param username: Name of the user to be created.
        :type username: :class:`str`
        :param identified_by: Password that the user will use to login to mysql server.
        :type identified_by: :class:`str`
        :param login_from: Locations that this user can login from. Defaults to '%' (anywhere).
        :type login_from: :class:`str`
        :return: Whether the user had to be created or not.
        :rtype: :class:`bool`

        Example:
        ::

            class MySampleRole(Role):
                def provision(self):
                    with self.using(MySQLRole) as role:
                        role.ensure_user('someuser', 'somepass', 'localhost')
        '''
        if not self.user_exists(username, login_from):
            self.__execute_non_query("CREATE USER '%s'@'%s' IDENTIFIED BY '%s';" % (username, login_from, identified_by))
            self.log("User %s not found with login access for %s. User created!" % (username, login_from))
            return True

        return False

    def is_database_present(self, database_name):
        '''
        Returns :data:`True` if the database is already created.

        :param database_name: Database to verify.
        :type database_name: :class:`str`
        :return: Whether the database is present or not.
        :rtype: :class:`bool`

        Example:
        ::

            class MySampleRole(Role):
                def provision(self):
                    with self.using(MySQLRole) as role:
                        if role.is_database_present('database'):
                            pass
        '''
        result = self.__execute_query('SHOW DATABASES')
        is_there = False
        if result:
            for row in result:
                if row['Database'].lower() == database_name.lower():
                    is_there = True

        return is_there

    def ensure_database(self, database_name):
        '''
        Creates the database if it does not exist.

        :param database_name: Database to create.
        :type database_name: :class:`str`
        :return: Whether the database had to be created or not.
        :rtype: :class:`bool`

        Example:
        ::

            class MySampleRole(Role):
                def provision(self):
                    with self.using(MySQLRole) as role:
                        role.ensure_database('database')
        '''
        if not self.is_database_present(database_name):
            self.__execute_non_query('CREATE DATABASE %s' % database_name)
            self.log("Database %s not found. Database created!" % database_name)
            return True
        return False

    def get_user_grants(self, username, login_from='%'):
        '''
        Returns all grants for the given user at the given location.

        :param username: Name of the user to be verify.
        :type username: :class:`str`
        :param login_from: Locations that this user can login from. Defaults to '%' (anywhere).
        :type login_from: :class:`str`
        :return: The user grants.
        :rtype: :class:`list`

        Example:
        ::

            class MySampleRole(Role):
                def provision(self):
                    with self.using(MySQLRole) as role:
                        if role.get_user_grants('user', login_from='%'):
                            pass
        '''
        grants = self.__execute_query("SHOW GRANTS FOR '%s'@'%s';" % (username, login_from))
        only_grants = []
        for grant in grants:
            filtered_grants = filter(lambda x: x.startswith('GRANT '), grant.itervalues())
            only_grants.extend(filtered_grants)

        return only_grants

    def has_grant(self, privileges, on, username, login_from, with_grant_option):
        '''
        Returns :data:`True` if the user has the specified privileges on the specified object in the given location.

        :param privileges: Privileges that are being verified.
        :type privileges: :class:`str`
        :param on: Database object that the user holds privileges on.
        :type on: :class:`str`
        :param username: Name of the user to be verify.
        :type username: :class:`str`
        :param login_from: Locations that this user can login from. Defaults to '%' (anywhere).
        :type login_from: :class:`str`
        :param with_grant_option: Indicates if we are verifying against grant option.
        :type with_grant_option: :class:`bool`
        :return: Whether the user has the privileges or not.
        :rtype: :class:`bool`

        Example:
        ::

            class MySampleRole(Role):
                def provision(self):
                    with self.using(MySQLRole) as role:
                        if role.has_grant('ALL PRIVILEGES',
                                          'database',
                                          'user',
                                          login_from='%',
                                          with_grant_option=True):
                            pass
        '''

        grants = self.get_user_grants(username, login_from)
        grant_option_string = self._get_grant_option_string(with_grant_option)
        privileges = self._get_privileges(privileges)
        grant_strings = self._get_possible_grant_strings(on, username, privileges, login_from, grant_option_string)

        for grant_string in grant_strings:
            if grant_string in grants:
                return True

        return False

    def _get_privileges(self, privileges):
        privileges = privileges.upper()
        if privileges == 'ALL':
            privileges = 'ALL PRIVILEGES'
        return privileges

    def _get_grant_option_string(self, with_grant_option):
        grant_option_string = ""
        if with_grant_option:
            grant_option_string = " WITH GRANT OPTION"
        return grant_option_string

    def _get_possible_grant_strings(self, on, username, privileges, login_from, grant_option_string):
        # These possible "ON" tokens are used because MySQL can behave differently depending on the version and system
        possible_on_tokens = [
            '`%s`.*' % on,
            '`%s`.`*`' % on,
            '%s.*' % on,
        ]
        grant_strings = ["GRANT %s ON %s TO '%s'@'%s'%s" % (privileges, on_token, username, login_from, grant_option_string)
                         for on_token in possible_on_tokens]
        return grant_strings

    def ensure_grant(self, privileges, on, username, login_from="%", with_grant_option=False):
        '''
        Ensures that the given user has the given privileges on the specified location.

        :param privileges: Privileges to assign to user (e.g.: "ALL PRIVILEGES").
        :type privileges: :class:`str`
        :param on: Object to assign privileges to. If only the name is supplied, '.*' will be appended to the name. If you want all databases pass '*.*'.
        :type on: :class:`str`
        :param username: User to grant the privileges to.
        :type username: :class:`str`
        :param login_from: Location where the user gets the grants. Defaults to '%' (anywhere).
        :type login_from: :class:`str`
        :param with_grant_option: If :data:`True`, indicates that this user may grant other users the same privileges. Defaults to :data:`False`.
        :type with_grant_option: :class:`bool`
        :return: Whether the grant had to be added or not.
        :rtype: :class:`bool`

        Example:
        ::

            class MySampleRole(Role):
                def provision(self):
                    with self.using(MySQLRole) as role:
                        role.ensure_grant('ALL PRIVILEGES',
                                          on='database',
                                          username='backend',
                                          login_from='%',
                                          with_grant_option=True)
        '''

        if self.has_grant(privileges, on, username, login_from, with_grant_option):
            return False

        grant_option_string = ""
        if with_grant_option:
            grant_option_string = " WITH GRANT OPTION"

        if not '.' in on:
            on = '%s.*' % on

        grant_string = "GRANT %s ON %s TO '%s'@'%s'%s" % (privileges, on, username, login_from, grant_option_string)
        self.__execute_non_query(grant_string)
        self.log("User %s@%s did not have grant '%s' on %s. Privileges granted!" % (username, login_from, privileges, on))

        return True
