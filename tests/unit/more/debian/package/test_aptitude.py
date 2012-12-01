import sys
from base64 import b64encode

from mock import MagicMock, patch
from nose.tools import istest

from provy.more.debian import AptitudeRole, PackageNotFound
from tests.unit.tools.helpers import ProvyTestCase


class AptitudeRoleTest(ProvyTestCase):
    @istest
    def checks_that_a_package_exists(self):
        role = AptitudeRole(prov=None, context={})

        with self.execute_mock() as execute:
            self.assertTrue(role.package_exists('python'))
            execute.assert_called_with('aptitude show python', stdout=False)

    @istest
    def checks_that_a_package_doesnt_exist(self):
        role = AptitudeRole(prov=None, context={})

        with self.execute_mock() as execute:
            execute.return_value = False
            self.assertFalse(role.package_exists('phyton'))
            execute.assert_called_with('aptitude show phyton', stdout=False)

    @istest
    def traps_sys_exit_when_checking_if_a_package_exists(self):
        role = AptitudeRole(prov=None, context={})

        def exit(*args, **kwargs):
            sys.exit(1)

        execute = MagicMock(side_effect=exit)

        with patch('provy.core.roles.Role.execute', execute):
            self.assertFalse(role.package_exists('phyton'))

    @istest
    def checks_if_a_package_exists_before_installing(self):
        role = AptitudeRole(prov=None, context={})

        with self.execute_mock() as execute, patch('provy.more.debian.AptitudeRole.package_exists') as package_exists:
            package_exists.return_value = True
            role.ensure_package_installed('python')
            self.assertTrue(package_exists.called)
            execute.assert_called_with('aptitude install -y python', stdout=False, sudo=True)

    @istest
    def fails_to_install_package_if_it_doesnt_exist(self):
        role = AptitudeRole(prov=None, context={})

        with self.execute_mock(), patch('provy.more.debian.AptitudeRole.package_exists') as package_exists:
            package_exists.return_value = False
            self.assertRaises(PackageNotFound, role.ensure_package_installed, 'phyton')
            self.assertTrue(package_exists.called)

    @istest
    def ensure_source_must_generate_correct_source_file(self):
        role = AptitudeRole(prov=None, context={})

        source_line = 'deb http://example.org/pub/ubuntu natty main restricted'
        expected_file = '%s_%s' % (b64encode(source_line)[:12], 'example.org')
        with self.execute_mock() as execute, patch('provy.more.debian.AptitudeRole.has_source') as has_source:
            has_source.return_value = False
            role.ensure_aptitude_source(source_line)
            self.assertTrue(has_source.called)
            execute.assert_called_with('echo "%s" >> /etc/apt/sources.list.d/%s.list' % (source_line, expected_file), stdout=False, sudo=True)
