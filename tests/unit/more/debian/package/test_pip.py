from contextlib import contextmanager
from unittest import TestCase

from mock import MagicMock, patch, call
from nose.tools import istest

from provy.more.debian import AptitudeRole, PipRole


NOTHING = None


class PipRoleTestCase(TestCase):
    @contextmanager
    def executing(self, command, returning=None):
        with patch('provy.core.roles.Role.execute') as execute:
            execute.return_value = returning
            yield execute
            if command is not None:
                execute.assert_called_with(command, sudo=True, stdout=False)
            else:
                self.assertFalse(execute.called)

    @contextmanager
    def checking_that_package(self, is_installed=True):
        with patch('provy.more.debian.PipRole.is_package_installed') as is_package_installed:
            is_package_installed.return_value = is_installed
            yield
            self.assertTrue(is_package_installed.called)

    @contextmanager
    def remote_version_as(self, version):
        with patch('provy.more.debian.PipRole.get_package_remote_version') as get_package_remote_version:
            get_package_remote_version.return_value = version
            yield

    @contextmanager
    def latest_version_as(self, version):
        with patch('provy.more.debian.PipRole.get_package_latest_version') as get_package_latest_version:
            get_package_latest_version.return_value = version
            yield


class PipRoleTest(PipRoleTestCase):
    def setUp(self):
        self.role = PipRole(prov=None, context={})

    @istest
    def extracts_package_name_as_data_from_input(self):
        self.assertEqual(self.role.extract_package_data_from_input('django'), {'name': 'django',})

    @istest
    def extracts_package_name_version_and_equal_to_as_data_from_input(self):
        self.assertEqual(self.role.extract_package_data_from_input('django==1.2.3'), {"name": "django", "version": "1.2.3", "version_constraint": "=="})

    @istest
    def extracts_package_name_version_and_greater_or_equal_to_as_data_from_input(self):
        self.assertEqual(self.role.extract_package_data_from_input("django>=1.2.3"), {"name": "django", "version": "1.2.3", "version_constraint": ">="})

    @istest
    def extracts_package_name_from_specific_repository_path(self):
        self.assertEqual(self.role.extract_package_data_from_input('-e hg+http://bitbucket.org/bkroeze/django-keyedcache/#egg=django-keyedcache'),
                         {"name": "django-keyedcache"})

    @istest
    def extracts_package_name_from_specific_repository_url(self):
        self.assertEqual(self.role.extract_package_data_from_input('http://www.satchmoproject.com/snapshots/trml2pdf-1.2.tar.gz'),
                         {"name": "http://www.satchmoproject.com/snapshots/trml2pdf-1.2.tar.gz"})

    @istest
    def checks_if_a_package_is_installed_by_name(self):
        with self.executing("pip freeze | tr '[A-Z]' '[a-z]' | grep django", returning="django==1.2.3"):
            self.assertTrue(self.role.is_package_installed("django"))

    @istest
    def checks_if_a_package_is_installed_by_name_and_version(self):
        with self.executing("pip freeze | tr '[A-Z]' '[a-z]' | grep django", returning="django==1.2.3"):
            self.assertTrue(self.role.is_package_installed("django==1.2.3"))

    @istest
    def fails_check_if_a_package_is_installed_by_greater_version(self):
        with self.executing("pip freeze | tr '[A-Z]' '[a-z]' | grep django", returning="django==1.2.3"):
            self.assertFalse(self.role.is_package_installed("django>=1.3.0"))

    @istest
    def fails_check_if_a_package_is_installed_by_greater_version_through_parameter(self):
        with self.executing("pip freeze | tr '[A-Z]' '[a-z]' | grep django", returning="django==1.2.3"):
            self.assertFalse(self.role.is_package_installed("django", version="1.3.0"))

    @istest
    def fails_check_if_a_package_is_installed_when_package_doesnt_exist(self):
        with self.executing("pip freeze | tr '[A-Z]' '[a-z]' | grep django", returning=""):
            self.assertFalse(self.role.is_package_installed("django"))

    @istest
    def ensures_requirements_are_installed(self):
        from os.path import abspath, join, dirname
        with patch('provy.more.debian.PipRole.ensure_package_installed') as ensure_package_installed:
            requeriments_file_name = abspath(join(dirname(__file__), "../../../fixtures/for_testing.txt"))
            self.role.ensure_requeriments_installed(requeriments_file_name)
            ensure_package_installed.assert_has_calls([
                call('Django'),
                call('yolk==0.4.1'),
                call('http://www.satchmoproject.com/snapshots/trml2pdf-1.2.tar.gz'),
                call('-e hg+http://bitbucket.org/bkroeze/django-threaded-multihost/#egg=django-threaded-multihost'),
            ])

    @istest
    def doesnt_install_a_package_if_its_already_installed_by_name(self):
        with self.checking_that_package(is_installed=True), self.executing(NOTHING):
            self.role.ensure_package_installed('django')

    @istest
    def doesnt_install_a_package_if_its_already_installed_by_name_and_version(self):
        with self.checking_that_package(is_installed=True), self.executing(NOTHING):
            self.role.ensure_package_installed('django', version='1.2.3')

    @istest
    def installs_a_package_by_name_if_its_not_installed(self):
        with self.checking_that_package(is_installed=False), self.executing('pip install django'):
            self.role.ensure_package_installed('django')

    @istest
    def installs_a_package_by_name_and_equal_version_if_its_not_installed(self):
        with self.checking_that_package(is_installed=False), self.executing('pip install django==1.2.3'):
            self.role.ensure_package_installed('django', version='1.2.3')

    @istest
    def installs_a_package_by_name_and_greater_equal_version_if_its_not_installed(self):
        with self.checking_that_package(is_installed=False), self.executing('pip install django>=1.2.3'):
            self.role.ensure_package_installed('django', version='>=1.2.3')

    @istest
    def installs_necessary_packages_to_provision(self):
        mock_aptitude = MagicMock(spec=AptitudeRole)

        @contextmanager
        def fake_using(self, klass):
            yield mock_aptitude

        with patch('provy.core.roles.Role.using', fake_using), self.executing('easy_install pip'):
            self.role.provision()
            install_calls = mock_aptitude.ensure_package_installed.mock_calls
            self.assertEqual(install_calls, [call('python-setuptools'), call('python-dev')])

    @istest
    def gets_none_as_version_if_remote_doesnt_have_it_installed(self):
        test_case = self
        @contextmanager
        def fake_settings(self, warn_only):
            test_case.assertTrue(warn_only)
            yield

        with patch('fabric.api.settings', fake_settings), self.executing("pip freeze | tr '[A-Z]' '[a-z]' | grep django", returning=''):
            self.assertIsNone(self.role.get_package_remote_version('django'))

    @istest
    def gets_version_if_remote_has_it_installed(self):
        test_case = self
        @contextmanager
        def fake_settings(self, warn_only):
            test_case.assertTrue(warn_only)
            yield

        with patch('fabric.api.settings', fake_settings), self.executing("pip freeze | tr '[A-Z]' '[a-z]' | grep django", returning='django==1.2.3'):
            self.assertEqual(self.role.get_package_remote_version('django'), '1.2.3')

    @istest
    def gets_none_as_package_latest_version_if_no_such_package_exists(self):
        with patch('xmlrpclib.ServerProxy') as MockServerProxy:
            mock_server_proxy = MockServerProxy.return_value
            mock_server_proxy.package_releases.return_value = None

            self.assertIsNone(self.role.get_package_latest_version('django'))

    @istest
    def gets_package_latest_version_by_same_provided_name(self):
        with patch('xmlrpclib.ServerProxy') as MockServerProxy:
            mock_server_proxy = MockServerProxy.return_value
            mock_server_proxy.package_releases.return_value = ['1.3.0', '1.2.3']

            self.assertEqual(self.role.get_package_latest_version('django'), '1.3.0')
            mock_server_proxy.package_releases.assert_called_with('django')

    @istest
    def gets_package_latest_version_by_capitalized_provided_name_when_plain_name_is_not_found(self):
        with patch('xmlrpclib.ServerProxy') as MockServerProxy:
            mock_server_proxy = MockServerProxy.return_value
            returned_values = [
                None,
                ['1.3.0', '1.2.3']
            ]
            mock_server_proxy.package_releases.side_effect = returned_values

            self.assertEqual(self.role.get_package_latest_version('django'), '1.3.0')
            mock_server_proxy.package_releases.assert_called_with('Django')

    @istest
    def says_that_package_can_be_updated_when_its_older_than_latest(self):
        with self.remote_version_as('1.2.3'), self.latest_version_as('1.3.0'):
            self.assertTrue(self.role.package_can_be_updated('django'))

    @istest
    def says_that_package_cant_be_updated_when_its_equal_latest(self):
        with self.remote_version_as('1.3.0'), self.latest_version_as('1.3.0'):
            self.assertFalse(self.role.package_can_be_updated('django'))

