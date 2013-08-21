from datetime import datetime, timedelta
import sys
from base64 import b64encode

from mock import MagicMock, patch
from nose.tools import istest

from provy.more.debian import AptitudeRole, PackageNotFound
from provy.more.debian.package import aptitude
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
    def checks_that_a_package_is_installed(self):
        with self.execute_mock() as execute:
            execute.return_value = '''
            foo
            bar
            '''

            self.assertTrue(self.role.is_package_installed('foo'))
            execute.assert_called_once_with("dpkg -l | egrep 'ii[ ]*foo\\b'", stdout=False, sudo=True)

    @istest
    def checks_that_a_package_is_not_installed(self):
        with self.execute_mock() as execute:
            execute.return_value = '''
            foo
            bar
            '''

            self.assertFalse(self.role.is_package_installed('baz'))
            execute.assert_called_once_with("dpkg -l | egrep 'ii[ ]*baz\\b'", stdout=False, sudo=True)

    @istest
    def checks_if_a_package_exists_before_installing(self):
        with self.execute_mock() as execute, self.mock_role_method('package_exists') as package_exists:
            package_exists.return_value = True

            result = self.role.ensure_package_installed('python')

            self.assertTrue(result)
            self.assertTrue(package_exists.called)
            execute.assert_called_with('aptitude install -y python', stdout=False, sudo=True)

    @istest
    def fails_to_install_package_if_it_doesnt_exist(self):
        with self.execute_mock(), self.mock_role_method('package_exists') as package_exists:
            package_exists.return_value = False

            self.assertRaises(PackageNotFound, self.role.ensure_package_installed, 'phyton')
            self.assertTrue(package_exists.called)

    @istest
    def doesnt_install_package_if_already_installed(self):
        with self.mock_role_method('is_package_installed'):
            self.role.is_package_installed.return_value = True

            result = self.role.ensure_package_installed('python')

            self.assertFalse(result)

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
    def doesnt_add_source_if_it_already_exists(self):
        source_line = 'deb http://example.org/pub/ubuntu natty main restricted'
        with self.execute_mock() as execute, self.mock_role_method('has_source') as has_source:
            has_source.return_value = True

            self.assertFalse(self.role.ensure_aptitude_source(source_line))

            self.assertFalse(execute.called)

    @istest
    def installs_necessary_packages_to_provision(self):
        with self.mock_role_methods('execute', 'ensure_up_to_date', 'ensure_package_installed', 'is_package_installed'):
            self.role.is_package_installed.return_value = False

            self.role.provision()

            self.role.is_package_installed.assert_called_once_with('aptitude')
            self.role.execute.assert_called_once_with('apt-get install aptitude -y', stdout=False, sudo=True)
            self.role.ensure_up_to_date.assert_called_once_with()
            self.role.ensure_package_installed.assert_called_once_with('curl')

    @istest
    def doesnt_install_aptitude_if_already_installed_when_provisioning(self):
        with self.mock_role_methods('execute', 'ensure_up_to_date', 'ensure_package_installed', 'is_package_installed'):
            self.role.is_package_installed.return_value = True

            self.role.provision()

            self.role.is_package_installed.assert_called_once_with('aptitude')
            self.assertFalse(self.role.execute.called)
            self.role.ensure_up_to_date.assert_called_once_with()
            self.role.ensure_package_installed.assert_called_once_with('curl')

    @istest
    def ensures_gpg_key_is_added(self):
        with self.execute_mock():
            self.role.ensure_gpg_key('http://some.repo')

            self.role.execute.assert_called_once_with('curl http://some.repo | apt-key add -', stdout=False, sudo=True)

    @istest
    def checks_that_repository_exists_in_apt_source(self):
        with self.execute_mock() as execute:
            execute.return_value = '1'

            result = self.role.has_source('foo-bar')

            self.assertTrue(result)
            execute.assert_called_once_with("grep -ilR '^foo-bar' /etc/apt/sources.list /etc/apt/sources.list.d | wc -l", sudo=True, stdout=False)

    @istest
    def checks_that_repository_doesnt_exist_in_apt_source(self):
        with self.execute_mock() as execute:
            execute.return_value = '0'

            result = self.role.has_source('foo-bar')

            self.assertFalse(result)

    @istest
    def gets_update_date_file_as_a_property(self):
        with self.mock_role_method('remote_temp_dir'):
            self.role.remote_temp_dir.return_value = '/foo/bar'

            self.assertEqual(self.role.update_date_file, '/foo/bar/last_aptitude_update')

    @istest
    def stores_update_date(self):
        with self.mock_role_methods('update_date_file', 'execute'), patch.object(aptitude, 'datetime') as mock_datetime:
            self.role.update_date_file = '/foo/bar'
            when = datetime.strptime('2013-01-01', '%Y-%m-%d')
            mock_datetime.now.return_value = when

            self.role.store_update_date()

            self.role.execute.assert_called_once_with('echo "01-01-13 00:00:00" > /foo/bar', stdout=False)

    @istest
    def gets_last_update_date(self):
        with self.mock_role_methods('remote_exists', 'update_date_file', 'read_remote_file'):
            self.role.update_date_file = '/foo/bar'
            self.role.remote_exists.return_value = True
            self.role.read_remote_file.return_value = '01-01-13 00:00:00'

            result = self.role.get_last_update_date()

            self.assertEqual(result, datetime.strptime('2013-01-01', '%Y-%m-%d'))
            self.role.remote_exists.assert_called_once_with(self.role.update_date_file)
            self.role.read_remote_file.assert_called_once_with(self.role.update_date_file)

    @istest
    def gets_none_as_last_update_if_there_was_no_update_yet(self):
        with self.mock_role_methods('remote_exists', 'update_date_file', 'read_remote_file'):
            self.role.update_date_file = '/foo/bar'
            self.role.remote_exists.return_value = False

            result = self.role.get_last_update_date()

            self.assertIsNone(result)
            self.assertFalse(self.role.read_remote_file.called)

    @istest
    def updates_aptitude_when_passed_time_limit(self):
        with patch.object(aptitude, 'datetime') as mock_datetime, self.mock_role_methods('get_last_update_date', 'force_update'):
            now = datetime.strptime('2013-01-01', '%Y-%m-%d')
            then = now - timedelta(minutes=31)
            mock_datetime.now.return_value = now
            self.role.get_last_update_date.return_value = then

            self.role.ensure_up_to_date()

            self.role.get_last_update_date.assert_called_once_with()
            self.role.force_update.assert_called_once_with()

    @istest
    def doesnt_update_if_not_passed_from_time_limit(self):
        with patch.object(aptitude, 'datetime') as mock_datetime, self.mock_role_methods('get_last_update_date', 'force_update'):
            now = datetime.strptime('2013-01-01', '%Y-%m-%d')
            then = now - timedelta(minutes=29)
            mock_datetime.now.return_value = now
            self.role.get_last_update_date.return_value = then

            self.role.ensure_up_to_date()

            self.assertFalse(self.role.force_update.called)

    @istest
    def forces_an_update(self):
        with self.mock_role_methods('execute', 'store_update_date'):
            self.role.force_update()

            self.assertTrue(self.role.context['aptitude-up-to-date'])
            self.role.execute.assert_called_once_with('aptitude update', stdout=False, sudo=True)
            self.role.store_update_date.assert_called_once_with()
