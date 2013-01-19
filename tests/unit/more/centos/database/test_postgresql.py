from mock import call, patch, DEFAULT
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
    def ensures_postegres_is_running(self):
        with self.execution('..stopped..', 'service postgresql status', None):
            with self.successful_execution('service postgresql start', None):
                self.assertTrue(self.role._ensure_running())

    @istest
    def ensures_postegres_is_not_running(self):
        with self.execution('..running..', 'service postgresql status', None):
            self.assertTrue(self.role._ensure_running())

    @istest
    def ensures_postgres_on_startup(self):
        with self.execution('......', 'chkconfig --list', None):
            with self.execution('', 'chkconfig --add postgresql', None):
                with self.execution('', 'chkconfig postgresql on', None):
                    self.assertTrue(self.role._run_on_startup())

    @istest
    def ensures_postgres_not_on_startup(self):
        with self.execution('..\r\npostgresql     \t0:off\t1:off\t2:on\t3:on\t4:on\t5:on\t6:off\r\n..', 'chkconfig --list', None):
            self.assertFalse(self.role._run_on_startup())

    @istest
    def change_directory_to_postgres_data_dir(self):
        with patch('fabric.api.cd') as cd_mock, self.execute_mock() as execute:
            self.role._execute('ls')
            self.assertEqual(cd_mock.call_args, call('/var/lib/pgsql'))
            self.assertEqual(
                execute.call_args, call('ls', sudo=True, stdout=True, user='postgres')
            )

    @istest
    @patch.multiple(
        'provy.more.centos.postgresql.PostgreSQLRole', _run_on_startup=DEFAULT,
        _ensure_running=DEFAULT, _ensure_initialized=DEFAULT,
    )
    def installs_necessary_packages_to_provision(self, **mocked_methods):
        with self.using_stub(YumRole) as mock_yum:
            self.role.provision()
            install_calls = mock_yum.ensure_package_installed.mock_calls
            self.assertEqual(
                install_calls,
                [call('postgresql-server'), call('postgresql-devel')],
            )

        for mock in mocked_methods.values():
            self.assertTrue(mock.called)
