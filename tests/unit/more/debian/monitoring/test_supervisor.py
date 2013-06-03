import os

from mock import patch, call
from nose.tools import istest

from provy.more.debian import PipRole, SupervisorRole
from tests.unit.tools.helpers import ProvyTestCase


class SupervisorRoleTest(ProvyTestCase):
    def setUp(self):
        super(SupervisorRoleTest, self).setUp()
        self.role = SupervisorRole(prov=None, context={'owner': 'some-owner'})

    @istest
    def installs_necessary_packages_to_provision(self):
        with self.using_stub(PipRole) as mock_pip, patch('provy.core.roles.Role.register_template_loader'):
            self.role.provision()

            mock_pip.ensure_package_installed.assert_called_with('supervisor')

    @istest
    def forces_as_sudo_to_install(self):
        with self.using_stub(PipRole) as mock_pip, patch('provy.core.roles.Role.register_template_loader'):
            self.role.provision()
            self.assertTrue(mock_pip.set_sudo.called)

    @istest
    def updates_init_script(self):
        config_file_path = '/foo/bar.conf'
        options = {'config_file': os.path.join(config_file_path, 'supervisord.conf')}

        with self.mock_role_methods('update_file', 'execute', 'ensure_restart'):
            self.role.update_file.return_value = True

            self.role.update_init_script(config_file_path)

            self.role.update_file.assert_called_once_with('supervisord.init.template', '/etc/init.d/supervisord', owner='some-owner', options=options, sudo=True)
            self.assertEqual(self.role.execute.mock_calls, [
                call('chmod +x /etc/init.d/supervisord', sudo=True, stdout=False),
                call('update-rc.d supervisord defaults', sudo=True, stdout=False),
            ])
            self.role.ensure_restart.assert_called_once_with()

    @istest
    def doesnt_update_init_script_if_file_not_updated(self):
        config_file_path = '/foo/bar.conf'

        with self.mock_role_methods('update_file', 'execute', 'ensure_restart'):
            self.role.update_file.return_value = False

            self.role.update_init_script(config_file_path)

            self.assertFalse(self.role.execute.called)
            self.assertFalse(self.role.ensure_restart.called)
