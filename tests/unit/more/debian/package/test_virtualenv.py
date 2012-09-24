from contextlib import contextmanager
import os
import sys

from mock import MagicMock, patch, call
from nose.tools import istest

from provy.more.debian import PipRole, VirtualenvRole
from tests.unit.tools.helpers import ProvyTestCase


class VirtualenvRoleTest(ProvyTestCase):
    def setUp(self):
        self.role = VirtualenvRole(prov=None, context={'user': 'johndoe',})

    @contextmanager
    def env_exists(self, env_name):
        with patch('provy.more.debian.VirtualenvRole.env_exists') as env_exists:
            yield env_exists

    @istest
    def refers_to_specific_subdir_at_user_home(self):
        role = VirtualenvRole(prov=None, context={'user': 'johndoe',})

        self.assertEqual(role.base_directory, '/home/johndoe/.virtualenvs')

    @istest
    def refers_to_specific_subdir_at_root_home(self):
        role = VirtualenvRole(prov=None, context={'user': 'root',})

        self.assertEqual(role.base_directory, '/root/.virtualenvs')

    @istest
    def installs_virtualenv_harness_when_provisioned(self):
        with self.using_stub(PipRole) as mock_role:
            self.role.provision()
            install_calls = mock_role.ensure_package_installed.mock_calls
            self.assertEqual(install_calls, [call('virtualenv'), call('virtualenvwrapper')])

    @istest
    def creates_a_virtual_environment(self):
        with self.execute_mock() as execute:
            env_dir = self.role.create_env('foo_env')
            self.assertEqual(env_dir, '/home/johndoe/.virtualenvs/foo_env')
            execute.assert_called_with('virtualenv /home/johndoe/.virtualenvs/foo_env', user='johndoe')

    @istest
    def creates_a_virtual_environment_with_system_site_packages(self):
        with self.execute_mock() as execute:
            env_dir = self.role.create_env('foo_env', system_site_packages=True)
            execute.assert_called_with('virtualenv --system-site-packages /home/johndoe/.virtualenvs/foo_env', user='johndoe')

    @istest
    def checks_that_a_virtual_env_exists(self):
        with self.mock_role_method('remote_exists_dir') as remote_exists_dir:
            remote_exists_dir.return_value = True
            self.assertTrue(self.role.env_exists('fancylib'))
            virtual_env_dir = os.path.join(self.role.base_directory, 'fancylib')
            remote_exists_dir.assert_called_with(virtual_env_dir)

    @istest
    def checks_that_a_virtual_env_doesnt_exist(self):
        with self.mock_role_method('remote_exists_dir') as remote_exists_dir:
            remote_exists_dir.return_value = False
            self.assertFalse(self.role.env_exists('fancylib'))
            virtual_env_dir = os.path.join(self.role.base_directory, 'fancylib')
            remote_exists_dir.assert_called_with(virtual_env_dir)

    @istest
    def wraps_the_env_usage_with_creation_activation_and_deactivation(self):
        execute = MagicMock()

        @contextmanager
        def prefix(command):
            execute('called before prefix')
            execute('prefix: "%s"' % command)
            yield
            execute('called after prefix')

        with patch('provy.core.roles.Role.execute', execute), patch('fabric.api.prefix', prefix), self.env_exists('fancylib') as env_exists:
            venv = VirtualenvRole(prov=None, context={'user': 'johndoe',})
            env_exists.return_value = False

            with venv('fancylib'):
                execute('some command')
                execute('some command 2')

            env_exists.assert_called_with('fancylib')

            env_creation_call = call('virtualenv %s/fancylib' % venv.base_directory, user='johndoe')
            activation_prefix_call = call('prefix: "source %s/fancylib/bin/activate"' % venv.base_directory)

            expected_executes = [
                env_creation_call,
                call('called before prefix'),
                activation_prefix_call,
                call('some command'),
                call('some command 2'),
                call('called after prefix'),
            ]
            execute.assert_has_calls(expected_executes)

    @istest
    def doesnt_create_env_if_it_already_exists(self):
        execute = MagicMock()

        @contextmanager
        def prefix(command):
            execute('called before prefix')
            execute('prefix: "%s"' % command)
            yield
            execute('called after prefix')

        with patch('provy.core.roles.Role.execute', execute), patch('fabric.api.prefix', prefix), self.env_exists('fancylib') as env_exists:
            venv = VirtualenvRole(prov=None, context={'user': 'johndoe',})
            env_exists.return_value = True

            with venv('fancylib'):
                execute('some command')
                execute('some command 2')

            env_exists.assert_called_with('fancylib')

            activation_prefix_call = call('prefix: "source %s/fancylib/bin/activate"' % venv.base_directory)

            expected_executes = [
                call('called before prefix'),
                activation_prefix_call,
                call('some command'),
                call('some command 2'),
                call('called after prefix'),
            ]
            self.assertEqual(execute.mock_calls, expected_executes)

    @istest
    def wraps_the_env_usage_creating_system_site_packages(self):
        with self.execute_mock() as execute:
            with self.role('fancylib', system_site_packages=True):
                pass
            execute.assert_any_call('virtualenv --system-site-packages %s/fancylib' % self.role.base_directory, user='johndoe')