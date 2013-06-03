import sys
from base64 import b64encode

from mock import MagicMock, patch
from nose.tools import istest

from provy.more.debian import AptitudeRole, PackageNotFound
from tests.unit.tools.helpers import ProvyTestCase


class AptitudeRoleTest(ProvyTestCase):
    def setUp(self):
        super(AptitudeRoleTest, self).setUp()
        self.role = AptitudeRole(prov=None, context={})

    @istest
    def checks_that_a_package_exists(self):
        with self.execute_mock() as execute:
            self.assertTrue(self.role.package_exists('python'))
            execute.assert_called_with('aptitude show python', stdout=False)

    @istest
    def checks_that_a_package_doesnt_exist(self):
        with self.execute_mock() as execute:
            execute.return_value = False
            self.assertFalse(self.role.package_exists('phyton'))
            execute.assert_called_with('aptitude show phyton', stdout=False)

    @istest
    def traps_sys_exit_when_checking_if_a_package_exists(self):
        def exit(*args, **kwargs):
            sys.exit(1)

        execute = MagicMock(side_effect=exit)

        with patch('provy.core.roles.Role.execute', execute):
            self.assertFalse(self.role.package_exists('phyton'))

    @istest
    def checks_if_a_package_exists_before_installing(self):
        with self.execute_mock() as execute, self.mock_role_method('package_exists') as package_exists:
            package_exists.return_value = True
            self.role.ensure_package_installed('python')
            self.assertTrue(package_exists.called)
            execute.assert_called_with('aptitude install -y python', stdout=False, sudo=True)

    @istest
    def fails_to_install_package_if_it_doesnt_exist(self):
        with self.execute_mock(), self.mock_role_method('package_exists') as package_exists:
            package_exists.return_value = False
            self.assertRaises(PackageNotFound, self.role.ensure_package_installed, 'phyton')
            self.assertTrue(package_exists.called)

    @istest
    def ensure_source_must_generate_correct_source_file(self):
        source_line = 'deb http://example.org/pub/ubuntu natty main restricted'
        expected_file = '%s_%s' % (b64encode(source_line)[:12], 'example.org')
        with self.execute_mock() as execute, self.mock_role_method('has_source') as has_source:
            has_source.return_value = False
            self.role.ensure_aptitude_source(source_line)
            self.assertTrue(has_source.called)
            execute.assert_called_with('echo "%s" >> /etc/apt/sources.list.d/%s.list' % (source_line, expected_file), stdout=False, sudo=True)

    @istest
    def installs_necessary_packages_to_provision(self):
        with self.mock_role_methods('execute', 'ensure_up_to_date', 'ensure_package_installed', 'is_package_installed'):
            self.role.is_package_installed.return_value = False

            self.role.provision()

            self.role.is_package_installed.assert_called_once_with('aptitude')
            self.role.execute.assert_called_once_with('apt-get install aptitude', stdout=False, sudo=True)
            self.role.ensure_up_to_date.assert_called_once_with()
            self.role.ensure_package_installed.assert_called_once_with('curl')
