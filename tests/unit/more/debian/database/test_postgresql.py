from contextlib import contextmanager
from unittest import TestCase

from mock import MagicMock, patch
from nose.tools import istest

from provy.more.debian.database.postgresql import PostgreSQLRole


class PostgreSQLRoleTestCase(TestCase):
    def setUp(self):
        self.role = PostgreSQLRole(prov=None, context={})
        self.current_execute = None

    def successful_execution(self, *args, **kwargs):
        self.current_execute = MagicMock(return_value=True)
        return self.execution(*args, **kwargs)

    def failed_execution(self, *args, **kwargs):
        self.current_execute = MagicMock(return_value=False)
        return self.execution(*args, **kwargs)

    @contextmanager
    def execution(self, *args, **kwargs):
        with patch('provy.core.roles.Role.execute', self.current_execute):
            yield
            self.assert_executed(*args, **kwargs)

    def assert_executed(self, *args, **kwargs):
        self.current_execute.assert_called_with(*args, **kwargs)


class PostgreSQLRoleTest(PostgreSQLRoleTestCase):
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
