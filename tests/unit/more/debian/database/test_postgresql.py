from unittest import TestCase

from nose.tools import istest

from provy.more.debian.database.postgresql import PostgreSQLRole


class PostgreSQLRoleTest(TestCase):
    @istest
    def creates_a_user_prompting_for_password(self):
        role = PostgreSQLRole(prov=None, context={})
