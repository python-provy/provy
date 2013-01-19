from mock import call
from nose.tools import istest

from provy.more.debian import AptitudeRole, PostgreSQLRole
from tests.unit.more.base.database import test_postgresql


class PostgreSQLRoleTestCase(test_postgresql.PostgreSQLRoleTestCase):
    def setUp(self):
        super(PostgreSQLRoleTestCase, self).setUp()
        self.role = PostgreSQLRole(prov=None, context={})


class PostgreSQLRoleTest(PostgreSQLRoleTestCase):
    @istest
    def installs_necessary_packages_to_provision_to_ubuntu(self):
        with self.using_stub(AptitudeRole) as mock_aptitude, self.provisioning_to('ubuntu'):
            self.role.provision()
            install_calls = mock_aptitude.ensure_package_installed.mock_calls
            self.assertEqual(install_calls, [call('postgresql'), call('postgresql-server-dev-9.1')])

    @istest
    def installs_necessary_packages_to_provision_to_debian(self):
        with self.using_stub(AptitudeRole) as mock_aptitude, self.provisioning_to('debian'):
            self.role.provision()
            install_calls = mock_aptitude.ensure_package_installed.mock_calls
            self.assertEqual(install_calls, [call('postgresql'), call('postgresql-server-dev-8.4')])
