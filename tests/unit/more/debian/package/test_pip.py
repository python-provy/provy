from contextlib import contextmanager
from unittest import TestCase

from mock import MagicMock, patch, call
from nose.tools import istest

from provy.more.debian import PipRole


NOTHING = None


class PipRoleTest(TestCase):
    def setUp(self):
        self.role = PipRole(prov=None, context={})

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

