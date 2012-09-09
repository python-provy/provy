from contextlib import contextmanager
from unittest import TestCase

from mock import MagicMock, patch
from nose.tools import istest

from provy.more.debian.database.postgresql import PostgreSQLRole


class PostgreSQLRoleTestCase(TestCase):
    def setUp(self):
        self.successful_execute = MagicMock(return_value=True)
        self.failed_execute = MagicMock(return_value=False)
        self.role = PostgreSQLRole(prov=None, context={})
        self.current_execute = None

    @contextmanager
    def successful_execution(self, *args, **kwargs):
        self.current_execute = self.successful_execute
        with patch('provy.core.roles.Role.execute', self.current_execute):
            yield
            self.assert_executed(*args, **kwargs)

    @contextmanager
    def failed_execution(self, *args, **kwargs):
        self.current_execute = self.failed_execute
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
