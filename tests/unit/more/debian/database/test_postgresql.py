from unittest import TestCase

from mock import MagicMock, patch
from nose.tools import istest

from provy.more.debian.database.postgresql import PostgreSQLRole


class PostgreSQLRoleTest(TestCase):
    def setUp(self):
        self.successful_execute = MagicMock(return_value=True)
        self.role = PostgreSQLRole(prov=None, context={})
        self.current_execute = None

    def successful_execution(self):
        self.current_execute = self.successful_execute
        return patch('provy.core.roles.Role.execute', self.successful_execute)

    def assert_executed(self, *args, **kwargs):
        self.current_execute.assert_called_with(*args, **kwargs)

    @istest
    def creates_a_user_prompting_for_password(self):
        with self.successful_execution():
            self.assertTrue(self.role.create_user("foo"))
            self.assert_executed("createuser -P foo", stdout=False)

    @istest
    def creates_a_user_without_prompting_for_password(self):
        with self.successful_execution():
            self.assertTrue(self.role.create_user("foo", ask_password=False))
            self.assert_executed("createuser foo", stdout=False)

    @istest
    def drops_the_user(self):
        with self.successful_execution():
            self.assertTrue(self.role.drop_user("foo"))
            self.assert_executed("dropuser foo", stdout=False)
