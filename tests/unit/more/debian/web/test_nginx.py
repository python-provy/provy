from nose.tools import istest

from provy.more.debian import AptitudeRole, NginxRole
from tests.unit.tools.helpers import ProvyTestCase


class NginxRoleTest(ProvyTestCase):
    def setUp(self):
        super(NginxRoleTest, self).setUp()
        self.role = NginxRole(prov=None, context={'owner': 'some-owner'})

    @istest
    def installs_necessary_packages_to_provision(self):
        with self.using_stub(AptitudeRole) as aptitude:
            self.role.provision()

            aptitude.ensure_up_to_date.assert_called_once_with()
            aptitude.ensure_package_installed.assert_called_once_with('nginx')

    @istest
    def doesnt_restart_if_not_necessary_upon_cleanup(self):
        with self.mock_role_method('restart'):
            self.role.cleanup()

            self.assertFalse(self.role.restart.called)

    @istest
    def restart_if_necessary_upon_cleanup(self):
        self.role.context['must-restart-nginx'] = True

        with self.mock_role_method('restart'):
            self.role.cleanup()

            self.assertTrue(self.role.restart.called)

    @istest
    def updates_configuration_and_restarts(self):
        conf_template = 'some-template'
        nginx_conf_path = 'some-conf-path'
        options = {'foo': 'bar'}

        with self.mock_role_methods('update_file', 'ensure_restart'):
            self.role.update_file.return_value = True

            self.role.ensure_conf(conf_template, options, nginx_conf_path)

            self.role.update_file.assert_called_once_with(conf_template, nginx_conf_path, options=options, sudo=True)
            self.role.ensure_restart.assert_called_once_with()

    @istest
    def doesnt_restart_if_configuration_wasnt_updated(self):
        conf_template = 'some-template'
        nginx_conf_path = 'some-conf-path'
        options = {'foo': 'bar'}

        with self.mock_role_methods('update_file', 'ensure_restart'):
            self.role.update_file.return_value = False

            self.role.ensure_conf(conf_template, options, nginx_conf_path)

            self.assertFalse(self.role.ensure_restart.called)

    @istest
    def ensures_site_is_disabled_and_restarted(self):
        site = 'some-site'

        with self.mock_role_methods('remove_file', 'ensure_restart'):
            self.role.remove_file.return_value = True

            self.role.ensure_site_disabled(site)

            self.role.remove_file.assert_called_once_with('/etc/nginx/sites-enabled/some-site', sudo=True)
            self.role.ensure_restart.assert_called_once_with()

    @istest
    def doesnt_restart_if_site_wasnt_disabled(self):
        site = 'some-site'

        with self.mock_role_methods('remove_file', 'ensure_restart'):
            self.role.remove_file.return_value = False

            self.role.ensure_site_disabled(site)

            self.assertFalse(self.role.ensure_restart.called)

    @istest
    def ensures_site_is_enabled_and_restarted(self):
        site = 'some-site'

        with self.mock_role_methods('remote_symlink', 'ensure_restart'):
            self.role.remote_symlink.return_value = True

            self.role.ensure_site_enabled(site)

            self.role.remote_symlink.assert_called_once_with('/etc/nginx/sites-available/some-site', '/etc/nginx/sites-enabled/some-site', sudo=True)
            self.role.ensure_restart.assert_called_once_with()

    @istest
    def doesnt_restart_if_site_wasnt_enabled(self):
        site = 'some-site'

        with self.mock_role_methods('remote_symlink', 'ensure_restart'):
            self.role.remote_symlink.return_value = False

            self.role.ensure_site_enabled(site)

            self.assertFalse(self.role.ensure_restart.called)

    @istest
    def ensures_site_is_created_and_restarted(self):
        site = 'some-site'
        template = 'some-template'
        options = {'foo': 'bar'}

        with self.mock_role_methods('update_file', 'ensure_restart'):
            self.role.update_file.return_value = True

            self.role.create_site(site, template, options=options)

            self.role.update_file.assert_called_once_with('some-template', '/etc/nginx/sites-available/some-site', options={'foo': 'bar'}, sudo=True)
            self.role.ensure_restart.assert_called_once_with()

    @istest
    def doesnt_restart_if_site_wasnt_created(self):
        site = 'some-site'
        template = 'some-template'
        options = {'foo': 'bar'}

        with self.mock_role_methods('update_file', 'ensure_restart'):
            self.role.update_file.return_value = False

            self.role.create_site(site, template, options=options)

            self.role.update_file.assert_called_once_with('some-template', '/etc/nginx/sites-available/some-site', options={'foo': 'bar'}, sudo=True)
            self.assertFalse(self.role.ensure_restart.called)

    @istest
    def ensures_nginx_is_restarted(self):
        self.role.context['must-restart-nginx'] = False

        self.role.ensure_restart()

        self.assertTrue(self.role.context['must-restart-nginx'])

    @istest
    def restarts_nginx(self):
        with self.execute_mock():
            self.role.restart()

            self.role.execute.assert_called_once_with('/etc/init.d/nginx restart', sudo=True)
