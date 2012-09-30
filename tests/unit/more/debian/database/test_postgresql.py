from contextlib import contextmanager

from mock import MagicMock, patch, call
from nose.tools import istest

from provy.more.debian import AptitudeRole, PostgreSQLRole
from tests.unit.tools.helpers import ProvyTestCase


class PostgreSQLRoleTestCase(ProvyTestCase):
    def setUp(self):
        self.role = PostgreSQLRole(prov=None, context={})
        self.execute = MagicMock(side_effect=self.return_execution_result)
        self.execution_results = []
        self.execution_count = -1
        self.assertion_count = -1

    def successful_execution(self, query):
        return self.execution(True, query)

    def failed_execution(self, query):
        return self.execution(False, query)

    def return_execution_result(self, *args, **kwargs):
        self.execution_count += 1
        return self.execution_results[self.execution_count]

    @contextmanager
    def execution(self, return_value, query):
        count = self.execution_count
        self.execution_results.append(return_value)
        with patch('provy.core.roles.Role.execute', self.execute):
            yield
            self.assert_executed(query)

    def assert_executed(self, query):
        name, e_args, e_kwargs = self.execute.mock_calls[self.assertion_count]
        self.assertion_count -= 1
        self.assertEqual(e_args[0], query)
        self.assertEqual(e_kwargs['user'], 'postgres')


class PostgreSQLRoleTest(PostgreSQLRoleTestCase):
    @istest
    def nested_test(self):
        """This test is to guarantee that the execution results go from the outer to the inner context managers."""
        with self.successful_execution("1"), self.failed_execution("2"):
            self.assertTrue(self.execute("1", stdout=False, user='postgres'))
            self.assertFalse(self.execute("2", stdout=False, user='postgres'))

    @istest
    def creates_a_user_prompting_for_password(self):
        with self.successful_execution("createuser -PSDR foo"):
            self.assertTrue(self.role.create_user("foo"))
            name, e_args, e_kwargs = self.execute.mock_calls[0]
            self.assertEqual(e_kwargs['stdout'], True)

    @istest
    def creates_a_user_without_password(self):
        with self.successful_execution("createuser -SDR foo"):
            self.assertTrue(self.role.create_user("foo", ask_password=False))
            name, e_args, e_kwargs = self.execute.mock_calls[0]
            self.assertEqual(e_kwargs['stdout'], True)

    @istest
    def creates_a_superuser(self):
        with self.successful_execution("createuser -Ps foo"):
            self.assertTrue(self.role.create_user("foo", is_superuser=True))
            name, e_args, e_kwargs = self.execute.mock_calls[0]
            self.assertEqual(e_kwargs['stdout'], True)

    @istest
    def creates_a_user_that_can_create_databases(self):
        with self.successful_execution("createuser -PSdR foo"):
            self.assertTrue(self.role.create_user("foo", can_create_databases=True))
            name, e_args, e_kwargs = self.execute.mock_calls[0]
            self.assertEqual(e_kwargs['stdout'], True)

    @istest
    def creates_a_user_that_can_create_roles(self):
        with self.successful_execution("createuser -PSDr foo"):
            self.assertTrue(self.role.create_user("foo", can_create_roles=True))
            name, e_args, e_kwargs = self.execute.mock_calls[0]
            self.assertEqual(e_kwargs['stdout'], True)

    @istest
    def drops_the_user(self):
        with self.successful_execution("dropuser foo"):
            self.assertTrue(self.role.drop_user("foo"))
            name, e_args, e_kwargs = self.execute.mock_calls[0]
            self.assertEqual(e_kwargs['stdout'], True)

    @istest
    def verifies_that_the_user_exists(self):
        with self.successful_execution("psql -tAc \"SELECT 1 FROM pg_roles WHERE rolname='foo'\""):
            self.assertTrue(self.role.user_exists("foo"))

    @istest
    def verifies_that_the_user_doesnt_exist(self):
        with self.failed_execution("psql -tAc \"SELECT 1 FROM pg_roles WHERE rolname='bar'\""):
            self.assertFalse(self.role.user_exists("bar"))

    @istest
    def ensures_user_is_created_if_it_doesnt_exist_yet(self):
        with self.failed_execution("psql -tAc \"SELECT 1 FROM pg_roles WHERE rolname='bar'\""):
            with self.successful_execution("createuser -PSDR bar"):
                self.assertTrue(self.role.ensure_user("bar"))

    @istest
    def ensures_user_is_created_without_password_if_it_doesnt_exist_yet(self):
        with self.failed_execution("psql -tAc \"SELECT 1 FROM pg_roles WHERE rolname='bar'\""):
            with self.successful_execution("createuser -SDR bar"):
                self.assertTrue(self.role.ensure_user("bar", ask_password=False))

    @istest
    def doesnt_create_user_if_it_already_exists(self):
        with self.successful_execution("psql -tAc \"SELECT 1 FROM pg_roles WHERE rolname='baz'\""):
            self.assertTrue(self.role.ensure_user("baz"))

    @istest
    def ensures_superuser_is_created_if_it_doesnt_exist_yet(self):
        with self.failed_execution("psql -tAc \"SELECT 1 FROM pg_roles WHERE rolname='bar'\""):
            with self.successful_execution("createuser -Ps bar"):
                self.assertTrue(self.role.ensure_user("bar", is_superuser=True))

    @istest
    def ensures_user_with_more_privileges_is_created_if_it_doesnt_exist_yet(self):
        with self.failed_execution("psql -tAc \"SELECT 1 FROM pg_roles WHERE rolname='bar'\""):
            with self.successful_execution("createuser -PSdr bar"):
                self.assertTrue(self.role.ensure_user("bar", can_create_databases=True, can_create_roles=True))

    @istest
    def creates_a_database(self):
        with self.successful_execution("createdb foo"):
            self.assertTrue(self.role.create_database("foo"))
            name, e_args, e_kwargs = self.execute.mock_calls[0]
            self.assertEqual(e_kwargs['stdout'], True)

    @istest
    def creates_a_database_with_a_particular_owner(self):
        with self.successful_execution("createdb foo -O bar"):
            self.assertTrue(self.role.create_database("foo", owner="bar"))
            name, e_args, e_kwargs = self.execute.mock_calls[0]
            self.assertEqual(e_kwargs['stdout'], True)

    @istest
    def drops_the_database(self):
        with self.successful_execution("dropdb foo"):
            self.assertTrue(self.role.drop_database("foo"))
            name, e_args, e_kwargs = self.execute.mock_calls[0]
            self.assertEqual(e_kwargs['stdout'], True)

    @istest
    def verifies_that_the_database_exists(self):
        with self.successful_execution('psql -tAc "SELECT 1 from pg_database WHERE datname=\'foo\'"'):
            self.assertTrue(self.role.database_exists("foo"))

    @istest
    def verifies_that_the_database_doesnt_exist(self):
        with self.failed_execution('psql -tAc "SELECT 1 from pg_database WHERE datname=\'foo\'"'):
            self.assertFalse(self.role.database_exists("foo"))

    @istest
    def creates_database_if_it_doesnt_exist_yet(self):
        with self.failed_execution('psql -tAc "SELECT 1 from pg_database WHERE datname=\'bar\'"'):
            with self.successful_execution("createdb bar"):
                self.assertTrue(self.role.ensure_database("bar"))

    @istest
    def creates_database_with_particular_owner_if_it_doesnt_exist_yet(self):
        with self.failed_execution('psql -tAc "SELECT 1 from pg_database WHERE datname=\'bar\'"'):
            with self.successful_execution("createdb bar -O baz"):
                self.assertTrue(self.role.ensure_database("bar", owner="baz"))

    @istest
    def doesnt_create_database_if_it_already_exists(self):
        with self.successful_execution('psql -tAc "SELECT 1 from pg_database WHERE datname=\'bar\'"'):
            self.assertTrue(self.role.ensure_database("bar"))

    @istest
    def installs_necessary_packages_to_provision(self):
        with self.using_stub(AptitudeRole) as mock_aptitude:
            self.role.provision()
            install_calls = mock_aptitude.ensure_package_installed.mock_calls
            self.assertEqual(install_calls, [call('postgresql'), call('postgresql-server-dev-9.1')])
