from mock import call, patch
from nose.tools import istest

from provy.more.centos import YumRole, PostgreSQLRole
from tests.unit.more.base.database import test_postgresql


class PostgreSQLRoleTestCase(test_postgresql.PostgreSQLRoleTestCase):
    def setUp(self):
        super(PostgreSQLRoleTestCase, self).setUp()
        self.role = PostgreSQLRole(prov=None, context={})


class PostgreSQLRoleTest(PostgreSQLRoleTestCase):
    @istest
    def ensure_initialized(self):
         with self.failed_execution('ls -A /var/lib/pgsql/data', None):
             with self.successful_execution('service postgresql initdb', None):
                 self.assertTrue(self.role._ensure_initialized())

         with self.successful_execution('ls -A /var/lib/pgsql/data', None):
             self.assertTrue(self.role._ensure_initialized())

    @istest
    def verifies_db_is_initialized(self):
         with self.successful_execution('ls -A /var/lib/pgsql/data', None):
             self.assertTrue(self.role._is_db_initialized())

    @istest
    def verifies_db_is_not_initialized(self):
         with self.failed_execution('ls -A /var/lib/pgsql/data', None):
             self.assertFalse(self.role._is_db_initialized())

    @istest
    def verifies_is_running(self):
        with self.execution('..running..', 'service postgresql status', None):
            self.assertTrue(self.role._is_running())

    @istest
    def verifies_is_not_running(self):
        with self.execution('..stoped..', 'service postgresql status', None):
            self.assertFalse(self.role._is_running())

    @istest
    def ensures_postegres_running(self):
        with self.execution('..stoped..', 'service postgresql status', None):
            with self.successful_execution('service postgresql start', None):
                self.assertTrue(self.role._ensure_running())

        with self.execution('..running..', 'service postgresql status', None):
            self.assertTrue(self.role._ensure_running())

    @istest
    def verifies_if_will_boot_at_startup(self):
        with self.execution('..postgresql..', 'chkconfig --list', None):
            self.assertTrue(self.role._will_start_on_boot())

    @istest
    def verifies_if_will_not_boot_at_startup(self):
        with self.execution('......', 'chkconfig --list', None):
            self.assertFalse(self.role._will_start_on_boot())

    @istest
    @patch('provy.more.centos.postgresql.PostgreSQLRole._ensure_initialized')
    @patch('provy.more.centos.postgresql.PostgreSQLRole._ensure_running')
    @patch('provy.more.centos.postgresql.PostgreSQLRole._run_on_startup')
    def installs_necessary_packages_to_provision(self, *mocked_methods):
        with self.using_stub(YumRole) as mock_yum:
            self.role.provision()
            install_calls = mock_yum.ensure_package_installed.mock_calls
            self.assertEqual(
                install_calls,
                [call('postgresql-server'), call('postgresql-devel')],
            )
        for mock in mocked_methods:
            self.assertTrue(mock.called)
