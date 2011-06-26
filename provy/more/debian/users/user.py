#!/usr/bin/python
# -*- coding: utf-8 -*-

from provy.core import Role

class UserRole(Role):
    def group_exists(self, group_name):
        return group_name in self.execute("cat /etc/group", stdout=False)

    def user_exists(self, username):
        return username in self.execute("cat /etc/passwd", stdout=False)

    def user_in_group(self, username, group_name):
        return group_name in self.execute('groups %s' % username, stdout=False)

    def ensure_group(self, group_name):
        if not self.group_exists(group_name):
            self.log("Group %s not found! Creating..." % group_name)
            self.execute('groupadd %s' % group_name, stdout=False, sudo=True)
            self.log("Group %s created!" % group_name)

    def ensure_user(self, username, identified_by=None, home_folder=None, default_script="/bin/sh", group=None, is_admin=False):
        is_admin_command = "-G admin"
        command = "useradd -g %(group)s %(is_admin_command)s -s %(default_script)s -p %(password)s -d %(home_folder)s -m %(username)s"

        home_folder = home_folder or '/home/%s' % username

        group = group or username

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

        if identified_by:
            self.execute('echo "%s:%s" | chpasswd' % (username, identified_by), stdout=False, sudo=True)

