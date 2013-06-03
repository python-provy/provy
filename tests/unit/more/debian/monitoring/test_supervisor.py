from copy import deepcopy
import os

from mock import call
from nose.tools import istest

from provy.more.debian import PipRole, SupervisorRole
from provy.more.debian.monitoring.supervisor import MUST_UPDATE_CONFIG_KEY, CONFIG_KEY, PROGRAMS_KEY
from tests.unit.tools.helpers import ProvyTestCase


class SupervisorRoleTest(ProvyTestCase):
    def setUp(self):
        super(SupervisorRoleTest, self).setUp()
        self.role = SupervisorRole(prov=None, context={'owner': 'some-owner'})

    @istest
    def installs_necessary_packages_to_provision(self):
        with self.using_stub(PipRole) as mock_pip, self.mock_role_method('register_template_loader'):
            self.role.provision()

            self.role.register_template_loader.assert_called_once_with('provy.more.debian.monitoring')
            mock_pip.ensure_package_installed.assert_called_once_with('supervisor')
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

    @istest
    def ensures_config_will_be_updated(self):
        self.role.context[MUST_UPDATE_CONFIG_KEY] = False

        self.role.ensure_config_update()

        self.assertTrue(self.role.context[MUST_UPDATE_CONFIG_KEY])

    @istest
    def configures_supervisor(self):
        self.role.context[CONFIG_KEY] = None

        self.role.config()

        self.assertEqual(self.role.context[CONFIG_KEY], {
            'config_file_directory': '/home/some-owner',
            'log_file': '/var/log/supervisord.log',
            'log_file_backups': 10,
            'log_file_max_mb': 50,
            'log_level': 'info',
            'pidfile': '/var/run/supervisord.pid',
            'user': 'some-owner',
        })

    @istest
    def enters_a_new_program_context(self):
        with self.role.with_program('foo-program') as program:
            program.directory = '/foo/bar'
            program.command = 'baz.sh'
            program.environment['FOO1'] = 'BAR1'
            program.environment['FOO2'] = 'BAR2'

        self.assertEqual(program.name, 'foo-program')
        self.assertEqual(program.supervisor, self.role)
        self.role.context[PROGRAMS_KEY][0]['environment'] = 'FOO1="BAR1",FOO2="BAR2"'

    @istest
    def requires_directory_and_command_to_create_program(self):

        def create_program():
            with self.role.with_program('foo-program'):
                '''Forgot directory or command...'''

        self.assertRaises(RuntimeError, create_program)

    @istest
    def updates_config_file(self):
        with self.mock_role_methods('update_file', 'ensure_restart'):
            with self.role.with_program('foo-program') as program:
                program.directory = '/foo/bar'
                program.command = 'baz.sh'

            self.role.config()
            options = deepcopy(self.role.context[CONFIG_KEY])
            options['programs'] = self.role.context[PROGRAMS_KEY]
            conf_path = os.path.join(options['config_file_directory'], 'supervisord.conf')

            self.role.update_config_file()

            self.role.update_file.assert_called_once_with('supervisord.conf.template', conf_path, options=options, owner=self.role.context['owner'], sudo=True)
            self.role.ensure_restart.assert_called_once_with()
