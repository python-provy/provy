from nose.tools import istest

from provy.more.debian import AptitudeRole, VarnishRole
from tests.unit.tools.helpers import ProvyTestCase


class VarnishRoleTest(ProvyTestCase):
    def setUp(self):
        super(VarnishRoleTest, self).setUp()
        self.role = VarnishRole(prov=None, context={'owner': 'some-owner'})

    @istest
    def installs_necessary_packages_to_provision(self):
        with self.using_stub(AptitudeRole) as aptitude:
            self.role.provision()

            aptitude.ensure_package_installed.assert_called_once_with('varnish')

    @istest
    def updates_vcl_and_restarts(self):
        template = 'some-template'
        varnish_vcl_path = 'some-conf-path'
        options = {'foo': 'bar'}
        owner = 'some-owner'

        with self.mock_role_methods('update_file', 'ensure_restart'):
            self.role.update_file.return_value = True

            self.role.ensure_vcl(template, varnish_vcl_path=varnish_vcl_path, options=options, owner=owner)

            self.role.update_file.assert_called_once_with(template, varnish_vcl_path, options=options, owner=owner, sudo=True)
            self.role.ensure_restart.assert_called_once_with()

    @istest
    def doesnt_restart_if_vcl_wasnt_updated(self):
        template = 'some-template'
        varnish_vcl_path = 'some-conf-path'
        options = {'foo': 'bar'}
        owner = 'some-owner'

        with self.mock_role_methods('update_file', 'ensure_restart'):
            self.role.update_file.return_value = False

            self.role.ensure_vcl(template, varnish_vcl_path=varnish_vcl_path, options=options, owner=owner)

            self.assertFalse(self.role.ensure_restart.called)

    @istest
    def updates_configuration_and_restarts(self):
        template = 'some-template'
        varnish_conf_path = 'some-conf-path'
        options = {'foo': 'bar'}
        owner = 'some-owner'

        with self.mock_role_methods('update_file', 'ensure_restart'):
            self.role.update_file.return_value = True

            self.role.ensure_conf(template, varnish_conf_path=varnish_conf_path, options=options, owner=owner)

            self.role.update_file.assert_called_once_with(template, varnish_conf_path, options=options, owner=owner, sudo=True)
            self.role.ensure_restart.assert_called_once_with()

    @istest
    def doesnt_restart_if_configuration_wasnt_updated(self):
        template = 'some-template'
        varnish_conf_path = 'some-conf-path'
        options = {'foo': 'bar'}
        owner = 'some-owner'

        with self.mock_role_methods('update_file', 'ensure_restart'):
            self.role.update_file.return_value = False

            self.role.ensure_conf(template, varnish_conf_path=varnish_conf_path, options=options, owner=owner)

            self.assertFalse(self.role.ensure_restart.called)

    @istest
    def doesnt_restart_if_not_necessary_upon_cleanup(self):
        with self.mock_role_method('restart'):
            self.role.cleanup()

            self.assertFalse(self.role.restart.called)

    @istest
    def restart_if_necessary_upon_cleanup(self):
        self.role.context['must-restart-varnish'] = True

        with self.mock_role_method('restart'):
            self.role.cleanup()

            self.assertTrue(self.role.restart.called)

    @istest
    def ensures_varnish_is_restarted(self):
        self.role.context['must-restart-varnish'] = False

        self.role.ensure_restart()

        self.assertTrue(self.role.context['must-restart-varnish'])

    @istest
    def restarts_varnish(self):
        with self.execute_mock():
            self.role.restart()

            self.role.execute.assert_called_once_with('START=yes /etc/init.d/varnish restart', sudo=True)
