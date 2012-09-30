from contextlib import contextmanager

from mock import MagicMock, patch, call
from nose.tools import istest

from provy.core.roles import DistroInfo
from provy.more.debian import ApacheRole, AptitudeRole
from tests.unit.tools.helpers import ProvyTestCase


class ApacheRoleTest(ProvyTestCase):
    def setUp(self):
        self.role = ApacheRole(prov=None, context={})

    @istest
    def installs_necessary_packages_to_provision(self):
        with self.using_stub(AptitudeRole) as aptitude:
            self.role.provision()

            aptitude.ensure_package_installed.assert_called_with('apache2')

    @istest
    def ensures_module_is_installed_and_enabled(self):
        with self.using_stub(AptitudeRole) as aptitude, self.execute_mock() as execute:
            self.role.ensure_mod('foo')

            aptitude.ensure_package_installed.assert_called_with('libapache2-mod-foo')
            execute.assert_called_with('a2enmod foo', sudo=True)
            self.assertTrue(self.role.must_restart)

    @istest
    def ensures_site_is_available_from_template(self):
        with self.execute_mock() as execute, self.mock_role_method('update_file') as update_file, self.mock_role_method('remote_symlink') as remote_symlink:
            self.role.create_site('bar-website', template='/local/path/to/bar-website')

            update_file.assert_called_with('/local/path/to/bar-website', '/etc/apache2/sites-available/bar-website', options={}, sudo=True)
            self.assertTrue(self.role.must_restart)

    @istest
    def ensures_site_is_available_from_template_and_options(self):
        with self.execute_mock() as execute, self.mock_role_method('update_file') as update_file, self.mock_role_method('remote_symlink') as remote_symlink:
            self.role.create_site('bar-website', template='/local/path/to/bar-website', options={'foo': 'Baz',})

            update_file.assert_called_with('/local/path/to/bar-website', '/etc/apache2/sites-available/bar-website', options={'foo': 'Baz',}, sudo=True)
            self.assertTrue(self.role.must_restart)

    @istest
    def ensures_that_a_website_is_enabled(self):
        with self.mock_role_method('remote_symlink') as remote_symlink:
            self.role.ensure_site_enabled('bar-website')

            remote_symlink.assert_called_with(from_file='/etc/apache2/sites-available/bar-website', to_file='/etc/apache2/sites-enabled/bar-website', sudo=True)
            self.assertTrue(self.role.must_restart)

    @istest
    def ensures_that_a_website_is_disabled(self):
        with self.mock_role_method('remove_file') as remove_file:
            self.role.ensure_site_disabled('bar-website')

            remove_file.assert_called_with('/etc/apache2/sites-enabled/bar-website', sudo=True)
            self.assertTrue(self.role.must_restart)

    @istest
    def can_be_restarted(self):
        with self.execute_mock() as execute:
            self.role.restart()

            execute.assert_called_with('service apache2 restart', sudo=True)

    @istest
    def ensures_that_it_must_be_restarted(self):

        self.assertFalse(self.role.must_restart)

        self.role.ensure_restart()

        self.assertTrue(self.role.must_restart)

    @istest
    def must_not_restart_again_if_already_restarted(self):
        with self.execute_mock() as execute:
            self.role.ensure_restart()
            self.role.restart()

            self.assertFalse(self.role.must_restart)

    @istest
    def restarts_on_cleanup_if_must_be_restarted(self):
        with patch('provy.more.debian.ApacheRole.restart') as restart:
            self.role.ensure_restart()
            self.role.cleanup()

            self.assertTrue(restart.called)

    @istest
    def doesnt_restart_on_cleanup_if_doesnt_need_to_be_restarted(self):
        with patch('provy.more.debian.ApacheRole.restart') as restart:
            self.role.cleanup()

            self.assertFalse(restart.called)
