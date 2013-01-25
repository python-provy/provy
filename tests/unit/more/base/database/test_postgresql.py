from contextlib import contextmanager

from mock import MagicMock, patch
from nose.tools import istest

from provy.more.base import BasePostgreSQLRole
from tests.unit.tools.helpers import ProvyTestCase


#class MockPostgresqlRole(BasePostgreSQLRole):
#
#    remote_files = {}
#
#    def put_file(self, from_file, to_file, sudo=False, stdout=True):
#        """
#            This role puts queries to be executed on remote server.
#        """
#        self.remote_files[to_file] = from_file.read()

class MockPostgresqlRole(BasePostgreSQLRole):


    def __init__(self, prov, context):
        super(MockPostgresqlRole, self).__init__(prov, context)
        self.executed_scripts = []

    def execute_script_file(self, database, local_script_file):
        self.executed_scripts.append((database, local_script_file.read()))

    def get_password(self):
        return "bar"


class PostgreSQLRoleTestCase(ProvyTestCase):
    def setUp(self):
        self.role = MockPostgresqlRole(prov=None, context={})
        self.execute = MagicMock(side_effect=self.return_execution_result)
        self.execution_results = []
        self.execution_count = -1
        self.assertion_count = -1

    def successful_execution(self, query, user='postgres', regexp_matches = False):
        return self.execution(True, query, user, regexp_matches)

    def failed_execution(self, query, user='postgres', regexp_matches = False):
        return self.execution(False, query, user, regexp_matches)

    def return_execution_result(self, *args, **kwargs):
        self.execution_count += 1
        return self.execution_results[self.execution_count]

    @contextmanager
    def execution(self, return_value, query, user='postgres', regexp_matches = False):
        self.execution_results.append(return_value)
        with patch('provy.core.roles.Role.execute', self.execute):
            yield
            self.assert_executed(query, user, regexp_matches)

    def assert_executed(self, query, user, regexp_matches):
        name, e_args, e_kwargs = self.execute.mock_calls[self.assertion_count]
        self.assertion_count -= 1
        if not regexp_matches:
            self.assertEqual(e_args[0], query)
        else:
            self.assertRegexpMatches(e_args[0], query)
        self.assertEqual(e_kwargs.get('user'), user)

    def assert_query_count(self, count):
        self.assertEqual(len(self.role.executed_scripts), count)

    def assert_query_contents(self, content,  database = "postgres", query_no = 0):
        print self.role.executed_scripts[query_no]
        self.assertEquals(self.role.executed_scripts[query_no], (database, content))

class PostgreSQLRoleTest(PostgreSQLRoleTestCase):
    @istest
    def nested_test(self):
        """This test is to guarantee that the execution results go from the outer to the inner context managers."""
        with self.successful_execution("1"), self.failed_execution("2"):
            self.assertTrue(self.execute("1", stdout=False, user='postgres'))
            self.assertFalse(self.execute("2", stdout=False, user='postgres'))

#    @istest
#    def creates_a_user_prompting_for_password(self):
#        with self.successful_execution("psql -f .*", regexp_matches=True):
#            self.assertTrue(self.role.create_user("foo"))
#            name, e_args, e_kwargs = self.execute.mock_calls[0]
#            self.assertEqual(e_kwargs['stdout'], True)

    @istest
    def creates_a_user_without_password(self):
        self.role.create_user("foo", ask_password=False)
        self.assert_query_count(1)
        self.assert_query_contents(
            """CREATE USER "foo" WITH NOSUPERUSER NOCREATEDB NOCREATEROLE ;"""
        )

    @istest
    def creates_a_superuser(self):
        self.role.create_user("foo", is_superuser=True)
        self.assert_query_count(1)
        self.assert_query_contents(
            """CREATE USER "foo" WITH SUPERUSER PASSWORD 'bar' ;"""
        )

    @istest
    def creates_a_user_that_can_create_databases(self):
        self.role.create_user("foo", can_create_databases=True)
        self.assert_query_count(1)
        self.assert_query_contents(
            """CREATE USER "foo" WITH NOSUPERUSER CREATEDB NOCREATEROLE PASSWORD 'bar' ;"""
        )

    @istest
    def creates_a_user_that_can_create_roles(self):
        self.role.create_user("foo", can_create_roles=True)
        self.assert_query_count(1)
        self.assert_query_contents(
            """CREATE USER "foo" WITH NOSUPERUSER NOCREATEDB CREATEROLE PASSWORD 'bar' ;"""
        )

    @istest
    def drops_the_user(self):
        self.role.drop_user("foo", ignore_if_not_exists=False)
        self.assert_query_count(1)
        self.assert_query_contents(
            '''DROP USER "foo" ;'''
        )

    @istest
    def drops_the_user_if_exists(self):
        self.role.drop_user("foo", ignore_if_not_exists=True)
        self.assert_query_count(1)
        self.assert_query_contents(
            '''DROP USER IF EXISTS "foo" ;'''
        )

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
            self.role.ensure_user("bar", can_create_roles=True)
            self.assert_query_count(1)
            self.assert_query_contents(
                """CREATE USER "bar" WITH NOSUPERUSER NOCREATEDB CREATEROLE PASSWORD 'bar' ;"""
            )

    @istest
    def doesnt_create_user_if_it_already_exists(self):
        with self.successful_execution("psql -tAc \"SELECT 1 FROM pg_roles WHERE rolname='baz'\""):
            self.role.ensure_user("baz")
            self.assert_query_count(0)


    @istest
    def creates_a_database(self):
        self.role.create_database("foo")
        self.assert_query_count(1)
        self.assert_query_contents('CREATE DATABASE "foo" ;')

    @istest
    def creates_a_database_with_a_particular_owner(self):
        self.role.create_database("foo", "bar")
        self.assert_query_count(1)
        self.assert_query_contents('CREATE DATABASE "foo" OWNER "bar" ;')

    @istest
    def drops_the_database(self):
        self.role.drop_database("foo")
        self.assert_query_count(1)
        self.assert_query_contents('DROP DATABASE "foo" ;')

    @istest
    def drops_the_database_if_exists(self):
        self.role.drop_database("foo", ignore_if_not_exists=True)
        self.assert_query_count(1)
        self.assert_query_contents('DROP DATABASE IF EXISTS "foo" ;')

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
            self.role.ensure_database("bar")
            self.assert_query_count(1)
            self.assert_query_contents('CREATE DATABASE "bar" ;')

    @istest
    def creates_database_with_particular_owner_if_it_doesnt_exist_yet(self):
        with self.failed_execution('psql -tAc "SELECT 1 from pg_database WHERE datname=\'bar\'"'):
            self.role.ensure_database("bar", "foo")
            self.assert_query_count(1)
            self.assert_query_contents('CREATE DATABASE "bar" OWNER "foo" ;')

    @istest
    def doesnt_create_database_if_it_already_exists(self):
        with self.successful_execution('psql -tAc "SELECT 1 from pg_database WHERE datname=\'bar\'"'):
            self.assertTrue(self.role.ensure_database("bar"))

    @istest
    def provision_should_raise_not_implemented_error(self):
        self.assertRaises(NotImplementedError, self.role.provision)
