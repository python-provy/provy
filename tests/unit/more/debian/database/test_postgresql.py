from contextlib import contextmanager
from unittest import TestCase

from mock import MagicMock, patch
from nose.tools import istest

from provy.more.debian.database.postgresql import PostgreSQLRole


class PostgreSQLRoleTestCase(TestCase):
    def setUp(self):
        self.role = PostgreSQLRole(prov=None, context={})
        self.execute = MagicMock(side_effect=self.return_execution_result)
        self.execution_results = []

    def successful_execution(self, *args, **kwargs):
        return self.execution(True, *args, **kwargs)

    def failed_execution(self, *args, **kwargs):
        return self.execution(False, *args, **kwargs)

    def return_execution_result(self, *args, **kwargs):
        return self.execution_results.pop(0)

    @contextmanager
    def execution(self, return_value, *args, **kwargs):
        self.execution_results.append(return_value)
        with patch('provy.core.roles.Role.execute', self.execute) as mock_execute:
            yield
            self.assert_executed(*args, **kwargs)

    def assert_executed(self, *args, **kwargs):
        self.execute.assert_called_with(*args, **kwargs)


class PostgreSQLRoleTest(PostgreSQLRoleTestCase):
    @istest
    def nested_test(self):
        """This test is to guarantee that the execution results go from the outer to the inner context managers."""
        with self.successful_execution(""), self.failed_execution(""):
            self.assertTrue(self.execute(""))
            self.assertFalse(self.execute(""))

    @istest
    def creates_a_user_prompting_for_password(self):
        with self.successful_execution("createuser -P foo", stdout=False):
            self.assertTrue(self.role.create_user("foo"))

    @istest
    def creates_a_user_without_prompting_for_password(self):
        with self.successful_execution("createuser foo", stdout=False):
            self.assertTrue(self.role.create_user("foo", ask_password=False))

    @istest
    def drops_the_user(self):
        with self.successful_execution("dropuser foo", stdout=False):
            self.assertTrue(self.role.drop_user("foo"))

    @istest
    def verifies_that_the_user_exists(self):
        with self.successful_execution("psql -tAc \"SELECT 1 FROM pg_roles WHERE rolname='foo'\"", stdout=False):
            self.assertTrue(self.role.user_exists("foo"))

    @istest
    def verifies_that_the_user_doesnt_exist(self):
        with self.failed_execution("psql -tAc \"SELECT 1 FROM pg_roles WHERE rolname='bar'\"", stdout=False):
            self.assertFalse(self.role.user_exists("bar"))
