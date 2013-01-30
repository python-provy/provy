#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Roles in this namespace are meant to provide user management operations for Debian distributions.'''

from provy.core import Role


class UserRole(Role):
    '''
    This role provides many utility methods for user management operations within Debian distributions.

    Example:
    ::

        from provy.core import Role
        from provy.more.debian import UserRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(UserRole) as role:
                    role.ensure_user('myuser', identified_by='mypass', is_admin=True)
    '''

    def group_exists(self, group_name):
        '''
        Returns :data:`True` if the given group exist, :data:`False` otherwise.

        :param group_name: Name of the group to verify.
        :type group_name: :class:`str`
        :return: Whether the group exists or not.
        :rtype: :class:`bool`

        Example:
        ::

            class MySampleRole(Role):
                def provision(self):
                    with self.using(UserRole) as role:
                        if role.group_exists('usersgroup'):
                            pass
        '''
        values = self.__first_values_from('group')
        return group_name in values

    def __first_values_from(self, basename):
        values = self.execute("cat /etc/%s | cut -d ':' -f 1" % basename, stdout=False, sudo=True)
        values = values.strip().split()
        return values

    def user_exists(self, username):
        '''
        Returns :data:`True` if the given user exist, :data:`False` otherwise.

        :param username: Name of the user to verify.
        :type username: :class:`str`
        :return: Whether the user exists or not.
        :rtype: :class:`bool`

        Example:
        ::

            class MySampleRole(Role):
                def provision(self):
                    with self.using(UserRole) as role:
                        if role.user_exists('myuser'):
                            pass
        '''
        values = self.__first_values_from('passwd')
        return username in values

    def user_in_group(self, username, group_name):
        '''
        Returns :data:`True` if the given user is in the given group, :data:`False` otherwise.

        :param username: Name of the user to verify.
        :type username: :class:`str`
        :param group_name: Name of the group to verify.
        :type group_name: :class:`str`
        :return: Whether the user pertains to the group or not.
        :rtype: :class:`bool`

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import UserRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(UserRole) as role:
                        if role.user_in_group('myuser', 'mygroup'):
                            pass
        '''
        raw_groups = self.execute('groups %s' % username, sudo=True, stdout=False).strip()
        if not raw_groups.startswith(username):
            raise ValueError("User '%s' doesn't exist" % username)
        groups_string = raw_groups.replace('%s : ' % username, '')
        groups = groups_string.split()
        return group_name in groups

    def ensure_group(self, group_name):
        '''
        Ensures that a given user group is present in the remote server.

        :param group_name: Name of the group to create.
        :type group_name: :class:`str`

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import UserRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(UserRole) as role:
                        role.ensure_group('users-group')
        '''
        if not self.group_exists(group_name):
            self.log("Group %s not found! Creating..." % group_name)
            self.execute('groupadd %s' % group_name, stdout=False, sudo=True)
            self.log("Group %s created!" % group_name)

    def ensure_user_groups(self, username, groups=[]):
        for user_group in groups:
            if not self.user_in_group(username, user_group):
                self.log("User %s should be in group %s! Rectifying that..." % (username, user_group))
                self.execute('usermod -G %s %s' % (user_group, username), stdout=False, sudo=True)
                self.log("User %s is in group %s now!" % (username, user_group))

    def ensure_user(self, username, identified_by=None, home_folder=None, default_script="/bin/bash", groups=[], is_admin=False):
        '''
        Ensures that a given user is present in the remote server.

        :param username: Name of the user.
        :type username: :class:`str`
        :param identified_by: Password that the user will use to login to the remote server. If set to :data:`None`, the user will not have a password.
        :type identified_by: :class:`str`
        :param home_folder: Specifies the user's home folder. Defaults to `/home/<username>`.
        :type home_folder: :class:`str`
        :param default_script: Sets the user's default script, the one that will execute commands per default when logging in. Defaults to `/bin/sh`.
        :type default_script: :class:`str`
        :param groups: Groups that this user belongs to. If the groups do not exist they are created prior to user creation. Defaults to the name of the user.
        :type groups: :class:`iterable`
        :param is_admin: If set to :data:`True` the user is added to the 'admin' user group as well. Defaults to :data:`False`.
        :type is_admin: :class:`bool`

        Example:
        ::

            from provy.core import Role
            from provy.more.debian import UserRole

            class MySampleRole(Role):
                def provision(self):
                    with self.using(UserRole) as role:
                        role.ensure_user('myuser', identified_by='mypass', is_admin=True)
        '''

        is_admin_command = "-G admin"
        command = "useradd -g %(group)s %(is_admin_command)s -s %(default_script)s -p %(password)s -d %(home_folder)s -m %(username)s"

        home_folder = home_folder or '/home/%s' % username

        group = groups and groups[0] or username

        for user_group in groups:
            self.ensure_group(user_group)
        self.ensure_group(group)

        if not self.user_exists(username):
            self.log("User %s not found! Creating..." % username)
            self.execute(command % {
                'group': group or username,
                'is_admin_command': is_admin and is_admin_command or '',
                'password': identified_by or 'none',
                'home_folder': home_folder,
                'default_script': default_script,
                'username': username
            }, stdout=False, sudo=True)
            self.log("User %s created!" % username)
        elif is_admin and not self.user_in_group(username, 'admin'):
            self.log("User %s should be admin! Rectifying that..." % username)
            self.execute('usermod -G admin %s' % username, stdout=False, sudo=True)
            self.log("User %s is admin now!" % username)

        self.ensure_user_groups(username, groups)

        if identified_by:
            self.execute('echo "%s:%s" | chpasswd' % (username, identified_by), stdout=False, sudo=True)

        self.context['owner'] = username
