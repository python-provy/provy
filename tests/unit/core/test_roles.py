from contextlib import contextmanager
import os
import sys

from jinja2 import ChoiceLoader, FileSystemLoader
from mock import MagicMock, patch, call
from nose.tools import istest

from provy.core.roles import Role, UsingRole
from tests.unit.tools.helpers import PROJECT_ROOT, ProvyTestCase


class RoleTest(ProvyTestCase):
    def setUp(self):
        loader = ChoiceLoader([
            FileSystemLoader(os.path.join(PROJECT_ROOT, 'files'))
        ])
        context = {
            'owner': 'foo',
            'registered_loaders': [],
            'loader': loader,
            'cleanup': [],
        }
        self.role = Role(prov=None, context=context)

    @istest
    def checks_if_a_remote_directory_exists(self):
        with self.execute_mock() as execute:
            execute.return_value = '0'
            self.assertTrue(self.role.remote_exists_dir('/some_path'))

            execute.assert_called_with('test -d /some_path; echo $?', stdout=False, sudo=True)

    @istest
    def checks_if_a_remote_directory_doesnt_exist(self):
        with self.execute_mock() as execute:
            execute.return_value = '1'
            self.assertFalse(self.role.remote_exists_dir('/some_path'))

            execute.assert_called_with('test -d /some_path; echo $?', stdout=False, sudo=True)

    @istest
    def doesnt_create_directory_if_it_already_exists(self):
        with self.mock_role_method('remote_exists_dir') as remote_exists_dir, self.execute_mock() as execute:
            remote_exists_dir.return_value = True
            self.role.ensure_dir('/some_path')
            self.assertFalse(execute.called)

    @istest
    def creates_the_directory_if_it_doesnt_exist(self):
        with self.mock_role_method('remote_exists_dir') as remote_exists_dir, self.execute_mock() as execute:
            remote_exists_dir.return_value = False
            self.role.ensure_dir('/some_path')
            execute.assert_called_with('mkdir -p /some_path', stdout=False, sudo=False)

    @istest
    def gets_distro_info_for_debian(self):
        with self.execute_mock() as execute:
            execute.return_value = 'No LSB modules are available.\nDistributor ID:\tDebian\nDescription:\tDebian GNU/Linux 6.0.5 (squeeze)\nRelease:\t6.0.5\nCodename:\tsqueeze'
            distro_info = self.role.get_distro_info()
            execute.assert_called_with('lsb_release -a')
            self.assertEqual(distro_info.distributor_id, 'Debian')
            self.assertEqual(distro_info.description, 'Debian GNU/Linux 6.0.5 (squeeze)')
            self.assertEqual(distro_info.release, '6.0.5')
            self.assertEqual(distro_info.codename, 'squeeze')

    @istest
    def gets_distro_info_for_ubuntu(self):
        with self.execute_mock() as execute:
            execute.return_value = 'No LSB modules are available.\r\nDistributor ID:\tUbuntu\r\nDescription:\tUbuntu 12.04.1 LTS\r\nRelease:\t12.04\r\nCodename:\tprecise'
            distro_info = self.role.get_distro_info()
            execute.assert_called_with('lsb_release -a')
            self.assertEqual(distro_info.distributor_id, 'Ubuntu')
            self.assertEqual(distro_info.description, 'Ubuntu 12.04.1 LTS')
            self.assertEqual(distro_info.release, '12.04')
            self.assertEqual(distro_info.codename, 'precise')

    @istest
    def gets_distro_info_for_centos(self):
        with self.execute_mock() as execute:
            execute.return_value = 'LSB Version:\t:core-4.0-ia32:core-4.0-noarch:graphics-4.0-ia32:graphics-4.0-noarch:printing-4.0-ia32:printing-4.0-noarch\nDistributor ID:\tCentOS\nDescription:\tCentOS release 5.8 (Final)\nRelease:\t5.8\nCodename:\tFinal'
            distro_info = self.role.get_distro_info()
            execute.assert_called_with('lsb_release -a')
            self.assertEqual(distro_info.lsb_version, ':core-4.0-ia32:core-4.0-noarch:graphics-4.0-ia32:graphics-4.0-noarch:printing-4.0-ia32:printing-4.0-noarch')
            self.assertEqual(distro_info.distributor_id, 'CentOS')
            self.assertEqual(distro_info.description, 'CentOS release 5.8 (Final)')
            self.assertEqual(distro_info.release, '5.8')
            self.assertEqual(distro_info.codename, 'Final')

    @istest
    def ignores_line_if_already_exists_in_file(self):
        with self.mock_role_method('has_line') as has_line, self.execute_mock() as execute:
            has_line.return_value = True
            self.role.ensure_line('this line in', '/some/file')
            self.assertFalse(execute.called)

    @istest
    def inserts_line_if_it_doesnt_exist_yet(self):
        with self.mock_role_method('has_line') as has_line, self.execute_mock() as execute:
            has_line.return_value = False
            self.role.ensure_line('this line in', '/some/file')
            execute.assert_called_with('echo "this line in" >> /some/file', stdout=False, sudo=False, user=None)

    @istest
    def inserts_line_with_sudo(self):
        with self.mock_role_method('has_line') as has_line, self.execute_mock() as execute:
            has_line.return_value = False
            self.role.ensure_line('this line in', '/some/file', sudo=True)
            execute.assert_called_with('echo "this line in" >> /some/file', stdout=False, sudo=True, user=None)

    @istest
    def inserts_line_with_specific_user(self):
        with self.mock_role_method('has_line') as has_line, self.execute_mock() as execute:
            has_line.return_value = False
            self.role.ensure_line('this line in', '/some/file', owner='foo')
            execute.assert_called_with('echo "this line in" >> /some/file', stdout=False, sudo=False, user='foo')

    @istest
    def registers_a_template_loader(self):
        package_name = 'provy.more.debian.monitoring'

        self.assertNotIn(package_name, self.role.context['registered_loaders'])
        self.role.register_template_loader(package_name)
        self.assertIn(package_name, self.role.context['registered_loaders'])

        choice_loader = self.role.context['loader']
        package_loader = choice_loader.loaders[1]
        self.assertIn('monitoring', package_loader.provider.module_path)

    @istest
    def appends_role_instance_to_cleanup_list_when_scheduling_cleanup(self):
        self.assertEqual(self.role.context['cleanup'], [])
        self.role.schedule_cleanup()
        self.assertEqual(self.role.context['cleanup'], [self.role])

    @istest
    def doesnt_append_again_if_role_is_already_in_cleanup_list(self):
        same_class_instance = Role(None, {})
        self.role.context['cleanup'] = [same_class_instance]
        self.role.schedule_cleanup()
        self.assertEqual(self.role.context['cleanup'], [same_class_instance])

    @istest
    def provisions_role(self):
        role_instance = MagicMock()
        def StubRole(prov, context):
            return role_instance

        self.role.provision_role(StubRole)

        role_instance.provision.assert_called_with()

    @istest
    def schedules_cleanup_when_provisioning(self):
        role_instance = MagicMock()
        def StubRole(prov, context):
            return role_instance

        self.role.provision_role(StubRole)

        role_instance.schedule_cleanup.assert_called_with()

    @istest
    def can_call_cleanup_safely(self):
        self.role.cleanup()

    @istest
    def executes_command_with_stdout_and_same_user(self):
        with patch('fabric.api.run') as run:
            self.role.execute('some command', stdout=True)

            run.assert_called_with('some command')

    @istest
    def executes_command_with_stdout_and_sudo(self):
        with patch('fabric.api.sudo') as sudo:
            self.role.execute('some command', stdout=True, sudo=True)

            sudo.assert_called_with('some command', user=None)

    @istest
    def executes_command_with_stdout_and_another_user(self):
        with patch('fabric.api.sudo') as sudo:
            self.role.execute('some command', stdout=True, user='foo')

            sudo.assert_called_with('some command', user='foo')

    @istest
    def executes_command_without_stdout_but_same_user(self):
        with patch('fabric.api.run') as run, patch('fabric.api.hide') as hide:
            self.role.execute('some command', stdout=False)

            run.assert_called_with('some command')
            hide.assert_called_with('warnings', 'running', 'stdout', 'stderr')

    @istest
    def executes_command_without_stdout_but_sudo(self):
        with patch('fabric.api.sudo') as sudo, patch('fabric.api.hide') as hide:
            self.role.execute('some command', stdout=False, sudo=True)

            sudo.assert_called_with('some command', user=None)
            hide.assert_called_with('warnings', 'running', 'stdout', 'stderr')

    @istest
    def executes_command_without_stdout_but_another_user(self):
        with patch('fabric.api.sudo') as sudo, patch('fabric.api.hide') as hide:
            self.role.execute('some command', stdout=False, user='foo')

            sudo.assert_called_with('some command', user='foo')
            hide.assert_called_with('warnings', 'running', 'stdout', 'stderr')

    @istest
    def executes_a_python_command(self):
        with self.execute_mock() as execute:
            self.role.execute_python('some command', stdout='is stdout?', sudo='is sudo?')

            execute.assert_called_with('python -c "some command"', stdout='is stdout?', sudo='is sudo?')

    @istest
    def gets_logged_user(self):
        with self.execute_mock() as execute:
            execute.return_value = 'some user'
            user = self.role.get_logged_user()

            self.assertEqual(user, 'some user')
            execute.assert_called_with('whoami', stdout=False)

    @istest
    def verifies_that_remote_file_exists(self):
        with self.execute_mock() as execute:
            execute.return_value = '0'

            self.assertTrue(self.role.remote_exists('/some.path'))
            execute.assert_called_with('test -f /some.path; echo $?', stdout=False, sudo=True)

    @istest
    def verifies_that_remote_file_doesnt_exist(self):
        with self.execute_mock() as execute:
            execute.return_value = '1'

            self.assertFalse(self.role.remote_exists('/some.path'))
            execute.assert_called_with('test -f /some.path; echo $?', stdout=False, sudo=True)

    @istest
    def verifies_that_a_local_file_exists(self):
        file_to_verify = os.path.abspath(__file__)
        self.assertTrue(self.role.local_exists(file_to_verify))

    @istest
    def verifies_that_a_local_file_doesnt_exist(self):
        file_to_verify = '/some/sneaky.file'
        self.assertFalse(self.role.local_exists(file_to_verify))

    @istest
    def creates_a_local_temp_dir(self):
        self.assertTrue(self.role.local_temp_dir().startswith('/tmp'))

    @istest
    def creates_a_remote_temp_dir(self):
        with self.mock_role_method('execute_python') as execute_python:
            execute_python.return_value = '/some/remote/temp/dir'
            directory = self.role.remote_temp_dir()
            self.assertEqual(directory, '/some/remote/temp/dir')
            execute_python.assert_called_with('from tempfile import gettempdir; print gettempdir()', stdout=False)

    @istest
    def changes_the_owner_of_a_directory(self):
        with self.execute_mock() as execute:
            self.role.change_dir_owner('/some/dir', 'foo')

            execute.assert_called_with('chown -R foo /some/dir', stdout=False, sudo=True)

    @istest
    def changes_the_owner_of_a_file(self):
        with self.execute_mock() as execute:
            self.role.change_file_owner('/some/file.ext', 'foo')

            execute.assert_called_with('chown -R foo /some/file.ext', stdout=False, sudo=True)

    @istest
    def changes_the_owner_of_a_path(self):
        with self.execute_mock() as execute:
            self.role.change_path_owner('/some/path', 'foo')

            execute.assert_called_with('chown -R foo /some/path', stdout=False, sudo=True)

    @istest
    def creates_a_directory_when_it_doesnt_exist_yet(self):
        with self.execute_mock() as execute, self.mock_role_method('remote_exists_dir') as remote_exists_dir:
            remote_exists_dir.return_value = False

            self.role.ensure_dir('/some/dir')

            execute.assert_called_with('mkdir -p /some/dir', stdout=False, sudo=False)

    @istest
    def creates_a_directory_with_sudo_when_it_doesnt_exist_yet(self):
        with self.execute_mock() as execute, self.mock_role_method('remote_exists_dir') as remote_exists_dir:
            remote_exists_dir.return_value = False

            self.role.ensure_dir('/some/dir', sudo=True)

            execute.assert_called_with('mkdir -p /some/dir', stdout=False, sudo=True)

    @istest
    def creates_a_directory_with_specific_user_when_it_doesnt_exist_yet(self):
        with self.execute_mock() as execute, self.mock_role_method('remote_exists_dir') as remote_exists_dir, self.mock_role_method('change_path_owner') as change_path_owner:
            remote_exists_dir.return_value = False

            self.role.ensure_dir('/some/dir', owner='foo')

            execute.assert_called_with('mkdir -p /some/dir', stdout=False, sudo=True)
            change_path_owner.assert_called_with('/some/dir', 'foo')

    @istest
    def doesnt_create_directory_if_it_already_exists(self):
        with self.execute_mock() as execute, self.mock_role_method('remote_exists_dir') as remote_exists_dir:
            remote_exists_dir.return_value = True

            self.role.ensure_dir('/some/dir')

            self.assertFalse(execute.called)

    @istest
    def gets_object_mode_from_remote_file(self):
        with self.execute_mock() as execute, self.mock_role_method('remote_exists') as remote_exists:
            remote_exists.return_value = True
            execute.return_value = '755\n'

            self.assertEqual(self.role.get_object_mode('/some/file.ext'), 755)
            execute.assert_called_with('stat -c %a /some/file.ext', stdout=False, sudo=True)

    @istest
    def cannot_get_mode_if_file_doesnt_exist(self):
        with self.execute_mock() as execute, self.mock_role_method('remote_exists') as remote_exists, self.mock_role_method('remote_exists_dir') as remote_exists_dir:
            remote_exists.return_value = False
            remote_exists_dir.return_value = False

            self.assertRaises(IOError, self.role.get_object_mode, '/some/file.ext')


class UsingRoleTest(ProvyTestCase):
    def any_context(self):
        return {'used_roles': {},}

    @istest
    def returns_role_instance_for_with_block(self):
        class DummyRole(Role):
            def schedule_cleanup(self):
                pass

        with UsingRole(DummyRole, None, self.any_context()) as role:
            self.assertIsInstance(role, DummyRole)

    @istest
    def provisions_role_when_entering_with_block(self):
        sentinel = MagicMock()

        class DummyRole(Role):
            def schedule_cleanup(self):
                pass

            def provision(self):
                sentinel()

        with UsingRole(DummyRole, None, self.any_context()) as role:
            self.assertTrue(sentinel.called)

    @istest
    def triggers_schedule_cleanup_when_exiting_with_block(self):
        sentinel = MagicMock()

        class DummyRole(Role):
            def schedule_cleanup(self):
                sentinel()

        with UsingRole(DummyRole, None, self.any_context()) as role:
            self.assertFalse(sentinel.called)
        self.assertTrue(sentinel.called)

    @istest
    def reuses_role_if_already_in_use(self):
        class DummyRole(Role):
            def schedule_cleanup(self):
                pass
        context = self.any_context()
        instance = DummyRole(None, context)
        context['used_roles'][DummyRole] = instance

        using = UsingRole(DummyRole, None, context)

        with using as role:
            self.assertEqual(using.role_instance, instance)
