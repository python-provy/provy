from mock import call, patch
from nose.tools import istest

from provy.more.debian import RailsRole, AptitudeRole, GemRole, SupervisorRole, NginxRole
from provy.more.debian.web.rails import PACKAGES_TO_INSTALL
from tests.unit.tools.helpers import ProvyTestCase


class RailsRoleTest(ProvyTestCase):
    def setUp(self):
        super(RailsRoleTest, self).setUp()
        self.role = RailsRole(prov=None, context={'owner': 'some-owner'})
        self.supervisor_role = SupervisorRole(prov=None, context=self.role.context)

    @istest
    def installs_necessary_packages_to_provision(self):
        methods_to_mock = (
            'execute',
            'register_template_loader',
            'remote_exists_dir',
            'update_file',
            'change_path_mode',
            'ensure_dir',
        )
        with self.using_stub(AptitudeRole) as aptitude, self.using_stub(GemRole) as gem, self.mock_role_methods(*methods_to_mock):
            self.role.remote_exists_dir.return_value = False

            self.role.provision()

            self.role.register_template_loader.assert_called_once_with('provy.more.debian.web')
            self.assertEqual(aptitude.ensure_package_installed.mock_calls, [call(package) for package in PACKAGES_TO_INSTALL])
            self.assertEqual(gem.ensure_package_installed.mock_calls, [call('bundler'), call('passenger')])
            self.role.remote_exists_dir.assert_called_once_with('/etc/nginx')
            self.assertEqual(self.role.ensure_dir.mock_calls, [
                call('/var/log/nginx', sudo=True),
                call('/etc/nginx/sites-available', sudo=True),
                call('/etc/nginx/sites-enabled', sudo=True),
                call('/etc/nginx/conf.d', sudo=True),
            ])
            self.role.execute.assert_called_once_with('passenger-install-nginx-module --auto --auto-download --prefix=/etc/nginx', sudo=True, stdout=False)
            self.assertEqual(self.role.update_file.mock_calls, [
                call('rails.nginx.conf.template', '/etc/nginx/conf/nginx.conf', sudo=True),
                call('rails.nginx.init.template', '/etc/init.d/nginx', sudo=True),
            ])
            self.role.change_path_mode.assert_called_once_with('/etc/init.d/nginx', 755)

    @istest
    def provisions_even_if_nginx_already_exists(self):
        methods_to_mock = (
            'register_template_loader',
            'remote_exists_dir',
            'update_file',
            'change_path_mode',
            'ensure_dir',
        )
        with self.using_stub(AptitudeRole), self.using_stub(GemRole), self.mock_role_methods(*methods_to_mock):
            self.role.remote_exists_dir.return_value = True

            self.role.provision()

            self.assertEqual(self.role.ensure_dir.mock_calls, [
                call('/etc/nginx/sites-available', sudo=True),
                call('/etc/nginx/sites-enabled', sudo=True),
                call('/etc/nginx/conf.d', sudo=True),
            ])

    @istest
    def restarts_on_cleanup_if_must_be_restarted(self):
        with patch('provy.more.debian.RailsRole.restart') as restart:
            self.role.ensure_restart()
            self.role.cleanup()

            self.assertTrue(restart.called)

    @istest
    def doesnt_restart_on_cleanup_if_doesnt_need_to_be_restarted(self):
        with patch('provy.more.debian.RailsRole.restart') as restart:
            self.role.cleanup()

            self.assertFalse(restart.called)

    @istest
    def ensures_site_is_disabled(self):
        site = 'some-site'

        with self.using_stub(NginxRole) as nginx:
            self.role.ensure_site_disabled(site)

            nginx.ensure_site_disabled.assert_called_once_with(site)

    @istest
    def ensures_site_is_enabled(self):
        site = 'some-site'

        with self.using_stub(NginxRole) as nginx:
            self.role.ensure_site_enabled(site)

            nginx.ensure_site_enabled.assert_called_once_with(site)

    @istest
    def ensures_site_is_created_and_restarted(self):
        owner = self.role.context['owner']
        site = 'some-site'
        host = 'some-host'
        path = 'some-path'
        options = {'foo': 'bar'}
        expected_options = {'foo': 'bar', 'host': host, 'path': path}

        with self.mock_role_methods('update_file', 'ensure_restart', 'execute'):
            self.role.update_file.return_value = True

            self.role.create_site(site, host, path, options=options)

            self.role.update_file.assert_called_once_with('rails-nginx.template', '/etc/nginx/sites-available/some-site', options=expected_options, sudo=True)
            self.role.ensure_restart.assert_called_once_with()
            self.role.execute.assert_called_once_with('cd some-path && bundle install --without development test --deployment', stdout=True, user=owner)

    @istest
    def ensures_site_is_created_without_restart_when_already_existant(self):
        owner = self.role.context['owner']
        site = 'some-site'
        host = 'some-host'
        path = 'some-path'
        options = {'foo': 'bar'}
        expected_options = {'foo': 'bar', 'host': host, 'path': path}

        with self.mock_role_methods('update_file', 'ensure_restart', 'execute'):
            self.role.update_file.return_value = False

            self.role.create_site(site, host, path, options=options)

            self.role.update_file.assert_called_once_with('rails-nginx.template', '/etc/nginx/sites-available/some-site', options=expected_options, sudo=True)
            self.assertFalse(self.role.ensure_restart.called)
            self.role.execute.assert_called_once_with('cd some-path && bundle install --without development test --deployment', stdout=True, user=owner)

    @istest
    def restarts_nginx(self):
        with self.using_stub(NginxRole) as nginx:
            self.role.restart()

            nginx.restart.assert_called_once_with()
