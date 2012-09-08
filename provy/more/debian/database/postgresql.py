#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to provide PostgreSQL database management utilities for Debian distributions.
'''

from provy.core import Role
from provy.more.debian.package.aptitude import AptitudeRole


class PostgresqlRole(Role):
    def create_user(self, username):
        return self.execute("createuser -P %s" % username, stdout=False)
