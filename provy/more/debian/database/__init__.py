#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Roles in this namespace are meant to enable database management for database servers as MySQL, MongoDB, Redis and such, in Debian distributions.
'''

from provy.more.debian.database.mongodb import MongoDBRole
from provy.more.debian.database.mysql import MySQLRole
from provy.more.debian.database.postgresql import PostgreSQLRole
from provy.more.debian.database.redis import RedisRole
