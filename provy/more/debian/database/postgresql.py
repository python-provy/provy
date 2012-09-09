#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to provide PostgreSQL database management utilities for Debian distributions.
'''

from provy.core import Role
from provy.more.debian.package.aptitude import AptitudeRole


class PostgreSQLRole(Role):
    def create_user(self, username, ask_password=True):
        pass_prompt_arg = "-P " if ask_password else ""
        return self.execute("createuser %s%s" % (pass_prompt_arg, username), stdout=False)

    def drop_user(self, username):
        return self.execute("dropuser %s" % username, stdout=False)
