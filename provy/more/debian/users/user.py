#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Roles in this namespace are meant to provide user management operations for Debian distributions.'''

from provy.core import Role


class UserRole(Role):
    '''
    This role provides many utility methods for user management operations within Debian distributions.
    <em>Sample usage</em>
    <pre class="sh_python">
    from provy.core import Role
    from provy.more.debian import UserRole

    class MySampleRole(Role):
        def provision(self):
            with self.using(UserRole) as role:
                role.ensure_user('myuser', identified_by='mypass', is_admin=True)
    </pre>
    '''

    def group_exists(self, group_name):
        '''
        Returns True if the given group exist, False otherwise.
        <em>Parameters</em>
        group_name - Name of the group to verify.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import UserRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(UserRole) as role:
                    if role.group_exists('usersgroup'):
                        # do something
        </pre>
        '''
        return group_name in self.execute("cat /etc/group", stdout=False)

    def user_exists(self, username):
        '''
        Returns True if the given user exist, False otherwise.
        <em>Parameters</em>
        username - Name of the user to verify.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import UserRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(UserRole) as role:
                    if role.user_exists('myuser'):
                        # do something
        </pre>
        '''
        return username in self.execute("cat /etc/passwd", stdout=False)

    def user_in_group(self, username, group_name):
        '''
        Returns True if the given user is in the given group, False otherwise.
        <em>Parameters</em>
        username - Name of the user to verify.
        group_name - Name of the group to verify.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import UserRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(UserRole) as role:
                    if role.user_in_group('myuser', 'mygroup'):
                        # do something
        </pre>
        '''

        return group_name in self.execute('groups %s' % username, sudo=True, stdout=False)

    def ensure_group(self, group_name):
        '''
        Ensures that a given user group is present in the remote server.
        <em>Parameters</em>
        group_name - Name of the group to create.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import UserRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(UserRole) as role:
                    role.ensure_group('users-group')
        </pre>
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
        <em>Parameters</em>
        username - Name of the user.
        identified_by - Password that the user will use to login to the remote server. If set to None, the user will not have a password.
        home_folder - Defaults to /home/&lt;username&gt;. Specifies the user's home folder.
        default_script - Defaults to /bin/sh. Sets the user's default script, the one that will execute commands per default when logging in.
        groups - Defaults to the name of the user. Groups that this user belongs to. If the groups do not exist they are created prior to user creation.
        is_admin - If set to True the user is added to the 'admin' user group as well.
        <em>Sample usage</em>
        <pre class="sh_python">
        from provy.core import Role
        from provy.more.debian import UserRole

        class MySampleRole(Role):
            def provision(self):
                with self.using(UserRole) as role:
                    role.ensure_user('myuser', identified_by='mypass', is_admin=True)
        </pre>
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
