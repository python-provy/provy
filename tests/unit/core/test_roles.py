# -*- coding: utf-8 -*-
from StringIO import StringIO

from contextlib import contextmanager
import os
import tempfile

from jinja2 import ChoiceLoader, FileSystemLoader
from mock import MagicMock, patch, call, ANY, Mock, DEFAULT
from nose.tools import istest

from provy.core.roles import Role, UsingRole, UpdateData
from tests.unit.tools.helpers import PROJECT_ROOT, ProvyTestCase

import uuid


class CoreRoleTest(ProvyTestCase):

    def setUp(self):
        loader = ChoiceLoader([
            FileSystemLoader(os.path.join(PROJECT_ROOT, 'files'))
        ])
        context = {
            'owner': 'foo',
            'registered_loaders': [],
            'loader': loader,
            'cleanup': [],
            'host': 'localhost',
        }
        self.role = Role(prov=None, context=context)
        self.update_data = UpdateData('/tmp/some-file.ext', 'some local md5', 'some remote md5')


class RoleTest(CoreRoleTest):

    @contextmanager
    def mock_update_data(self):
        with self.mock_role_method('_build_update_data'):
            self.role._build_update_data.return_value = self.update_data
            yield

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
    def proper_file_is_put_to_remote_server(self):
        with self.mock_role_method("execute_python_script"), \
                self.mock_role_method("put_file") as put_file, \
                self.mock_role_method("create_remote_temp_file") as tmp_file:
            tmp_file.return_value = "/tmp/foo"
            self.role.ensure_line("foo_bar", "/tmp/bar_baz")
        put_file.assert_called_once_with(ANY, "/tmp/foo", sudo=False, stdout=False)

    @istest
    def proper_file_is_put_to_remote_server_sudo(self):
        with self.mock_role_method("execute_python_script"), \
                self.mock_role_method("put_file") as put_file, \
                self.mock_role_method("create_remote_temp_file") as tmp_file:
            tmp_file.return_value = "/tmp/foo"
            self.role.ensure_line("foo_bar", "/tmp/bar_baz", sudo=True)
        put_file.assert_called_once_with(ANY, "/tmp/foo", sudo=True, stdout=False)

    @istest
    def proper_content_in_line_file(self):
        with self.mock_role_method("execute_python_script") as execute, \
                self.mock_role_method("put_file"), \
                self.mock_role_method("create_remote_temp_file") as tmp_file:
            tmp_file.return_value = "/tmp/foo"
            self.role.ensure_line("foo bar", "/etc/baz")
        # self.assertTrue(isinstance(put_file.mock_calls[0][1][0], StringIO))
        content = execute.mock_calls[0][1][0]
        self.assertIn('''LINE = """ /tmp/foo """''', content)
        self.assertIn('''TARGET = """/etc/baz"""''', content)

    @istest
    def registers_a_template_loader(self):
        package_name = 'provy.more.debian.monitoring'

        self.assertNotIn(package_name, self.role.context['registered_loaders'])
        self.role.register_template_loader(package_name)
        self.assertIn(package_name, self.role.context['registered_loaders'])

        choice_loader = self.role.context['loader']
        found = False
        for loader in choice_loader.loaders:
            if hasattr(loader, 'provider') and 'monitoring' in loader.provider.module_path:
                found = True
                break

        self.assertTrue(found, "Couldnt find added loader in path")

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
    def execute_command_check_cd_called_if_cwd_arg(self):
        with patch('fabric.api.run'):
            with patch('fabric.api.cd') as cd:
                self.role.execute("some command", cwd="/some/dir")
        cd.assert_called_once_with("/some/dir")

    @istest
    def execute_command_check_cd_called_if_no_cwd_arg(self):
        with patch('fabric.api.run'):
            with patch('fabric.api.cd') as cd:
                self.role.execute("some command")
        self.assertFalse(cd.called)

    @istest
    def executes_a_local_command_with_stdout_and_same_user(self):
        with patch('fabric.api.local') as local:
            local.return_value = 'some result'
            self.assertEqual(self.role.execute_local('some command', stdout=True), 'some result')

            local.assert_called_with('some command', capture=True)

    @istest
    def executes_a_local_command_with_stdout_and_sudo(self):
        with patch('fabric.api.local') as local:
            local.return_value = 'some result'
            self.assertEqual(self.role.execute_local('some command', stdout=True, sudo=True), 'some result')

            local.assert_called_with('sudo some command', capture=True)

    @istest
    def executes_a_local_command_with_stdout_and_another_user(self):
        with patch('fabric.api.local') as local:
            local.return_value = 'some result'
            self.assertEqual(self.role.execute_local('some command', stdout=True, user='foo'), 'some result')

            local.assert_called_with('sudo -u foo some command', capture=True)

    @istest
    def executes_a_local_command_without_stdout_and_another_user(self):
        with patch('fabric.api.local') as local, patch('fabric.api.hide') as hide:
            local.return_value = 'some result'
            self.assertEqual(self.role.execute_local('some command', stdout=False, user='foo'), 'some result')

            local.assert_called_with('sudo -u foo some command', capture=True)
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
    def gets_object_mode_from_remote_file(self):
        with self.execute_mock() as execute, self.mock_role_method('remote_exists') as remote_exists:
            remote_exists.return_value = True
            execute.return_value = '755\n'

            self.assertEqual(self.role.get_object_mode('/some/file.ext'), 755)
            execute.assert_called_with('stat -c %a /some/file.ext', stdout=False, sudo=True)

    @istest
    def cannot_get_mode_if_file_doesnt_exist(self):
        with self.execute_mock(), self.mock_role_method('remote_exists') as remote_exists, self.mock_role_method('remote_exists_dir') as remote_exists_dir:
            remote_exists.return_value = False
            remote_exists_dir.return_value = False

            self.assertRaises(IOError, self.role.get_object_mode, '/some/file.ext')

    @istest
    def changes_the_mode_of_a_path_if_its_different(self):
        with self.execute_mock() as execute, self.mock_role_method('get_object_mode') as get_object_mode:
            get_object_mode.return_value = 644

            self.role.change_path_mode('/some/path', 755)

            execute.assert_called_with('chmod 755 /some/path', stdout=False, sudo=True)

    @istest
    def recursively_changes_the_mode_of_a_path_if_its_different(self):
        with self.execute_mock() as execute, self.mock_role_method('get_object_mode') as get_object_mode:
            get_object_mode.return_value = 644

            self.role.change_path_mode('/some/path', 755, recursive=True)

            execute.assert_called_with('chmod -R 755 /some/path', stdout=False, sudo=True)

    @istest
    def doesnt_change_path_mode_if_its_the_same(self):
        with self.execute_mock() as execute, self.mock_role_method('get_object_mode') as get_object_mode:
            get_object_mode.return_value = 755

            self.role.change_path_mode('/some/path', 755)

            self.assertFalse(execute.called)

    @istest
    def recursively_changes_the_mode_of_a_path_even_if_the_mode_of_the_parent_path_is_the_same(self):
        with self.execute_mock() as execute, self.mock_role_method('get_object_mode') as get_object_mode:
            get_object_mode.return_value = 755

            self.role.change_path_mode('/some/path', 755, recursive=True)

            execute.assert_called_with('chmod -R 755 /some/path', stdout=False, sudo=True)

    @istest
    def changes_the_mode_of_a_directory(self):
        with self.mock_role_method('change_path_mode') as change_path_mode:
            self.role.change_dir_mode('/some/dir', 755, recursive='is it recursive?')

            change_path_mode.assert_called_with('/some/dir', 755, recursive='is it recursive?')

    @istest
    def changes_the_mode_of_a_file(self):
        with self.mock_role_method('change_path_mode') as change_path_mode:
            self.role.change_file_mode('/some/file.ext', 755)

            change_path_mode.assert_called_with('/some/file.ext', 755)

    @istest
    def gets_the_md5_hash_of_a_local_file(self):
        with self.mock_role_method('execute_local') as execute_local, self.mock_role_method('local_exists') as local_exists:
            local_exists.return_value = True
            execute_local.return_value = 'some-hash\n'

            self.assertEqual(self.role.md5_local('/some/path'), 'some-hash')
            execute_local.assert_called_with('md5sum /some/path | cut -d " " -f 1', stdout=False, sudo=True)

    @istest
    def returns_none_if_local_file_doesnt_exist_for_md5_hash(self):
        with self.mock_role_method('execute_local') as execute_local, self.mock_role_method('local_exists') as local_exists:
            local_exists.return_value = False

            self.assertIsNone(self.role.md5_local('/some/path'))
            self.assertFalse(execute_local.called)

    @istest
    def gets_the_md5_hash_of_a_remote_file(self):
        with self.execute_mock() as execute, self.mock_role_method('remote_exists') as remote_exists:
            remote_exists.return_value = True
            execute.return_value = 'some-hash\n'

            self.assertEqual(self.role.md5_remote('/some/path'), 'some-hash')
            execute.assert_called_with('md5sum /some/path | cut -d " " -f 1', stdout=False, sudo=True)

    @istest
    def returns_none_if_remote_file_doesnt_exist_for_md5_hash(self):
        with self.execute_mock() as execute, self.mock_role_method('remote_exists') as remote_exists:
            remote_exists.return_value = False

            self.assertIsNone(self.role.md5_remote('/some/path'))
            self.assertFalse(execute.called)

    @istest
    def removes_a_directory_if_it_exists(self):
        with self.execute_mock() as execute, self.mock_role_method('remote_exists_dir') as remote_exists_dir:
            remote_exists_dir.return_value = True

            self.assertTrue(self.role.remove_dir('/some/dir'))
            execute.assert_called_with('rmdir /some/dir', stdout=False, sudo=False)

    @istest
    def doesnt_remove_a_directory_if_it_doesnt_exist(self):
        with self.execute_mock() as execute, self.mock_role_method('remote_exists_dir') as remote_exists_dir:
            remote_exists_dir.return_value = False

            self.assertFalse(self.role.remove_dir('/some/dir'))
            self.assertFalse(execute.called)

    @istest
    def removes_a_directory_recursively_if_it_exists(self):
        with self.execute_mock() as execute, self.mock_role_method('remote_exists_dir') as remote_exists_dir:
            remote_exists_dir.return_value = True

            self.assertTrue(self.role.remove_dir('/some/dir', recursive=True))
            execute.assert_called_with('rm -rf /some/dir', stdout=False, sudo=False)

    @istest
    def removes_a_directory_as_sudo_if_it_exists(self):
        with self.execute_mock() as execute, self.mock_role_method('remote_exists_dir') as remote_exists_dir:
            remote_exists_dir.return_value = True

            self.assertTrue(self.role.remove_dir('/some/dir', sudo=True))
            execute.assert_called_with('rmdir /some/dir', stdout=False, sudo=True)

    @istest
    def removes_dir_silently_if_requested(self):
        with self.execute_mock():
            with self.mock_role_method('log') as log:
                with self.mock_role_method('remote_exists_dir') as exists:
                    exists.return_value = True
                    self.role.remove_dir('/some/dir', sudo=True, stdout=False)
        self.assertFalse(log.called)

    @istest
    def removes_dir_logging_if_requested(self):
        with self.execute_mock():
            with self.mock_role_method('log') as log:
                with self.mock_role_method('remote_exists_dir') as exists:
                    exists.return_value = True
                    self.role.remove_dir('/some/dir', sudo=True, stdout=True)
        self.assertEqual(len(log.mock_calls), 1)

    @istest
    def puts_file_silently_if_requested(self):
        with patch("fabric.api.put"):
            with self.mock_role_method("_Role__showing_command_output") as showing:
                self.role.put_file("foo", "bar", stdout=False)
        showing.assert_called_once_with(False)

    @istest
    def puts_file_chatting_if_requested(self):
        with patch("fabric.api.put"):
            with self.mock_role_method("_Role__showing_command_output") as showing:
                self.role.put_file("foo", "bar", stdout=True)
        showing.assert_called_once_with(True)

    @istest
    def removes_a_file_if_it_exists(self):
        with self.execute_mock() as execute, self.mock_role_method('remote_exists') as remote_exists:
            remote_exists.return_value = True

            self.assertTrue(self.role.remove_file('/some/file.ext'))
            execute.assert_called_with('rm -f /some/file.ext', stdout=False, sudo=False)

    @istest
    def doesnt_remove_a_file_if_it_doesnt_exist(self):
        with self.execute_mock() as execute, self.mock_role_method('remote_exists') as remote_exists:
            remote_exists.return_value = False

            self.assertFalse(self.role.remove_file('/some/dir'))
            self.assertFalse(execute.called)

    @istest
    def removes_a_file_as_sudo_if_it_exists(self):
        with self.execute_mock() as execute, self.mock_role_method('remote_exists') as remote_exists:
            remote_exists.return_value = True

            self.assertTrue(self.role.remove_file('/some/file.ext', sudo=True))
            execute.assert_called_with('rm -f /some/file.ext', stdout=False, sudo=True)

    @istest
    def puts_a_file_in_the_remote_path(self):
        with patch('fabric.api.put') as put:
            self.role.put_file('/from/file', '/to/file')

            put.assert_called_with('/from/file', '/to/file', use_sudo=False)

    @istest
    def puts_a_file_as_sudo_in_the_remote_path(self):
        with patch('fabric.api.put') as put:
            self.role.put_file('/from/file', '/to/file', sudo=True)

            put.assert_called_with('/from/file', '/to/file', use_sudo=True)

    @istest
    def replaces_a_file(self):
        with self.mock_role_method('put_file') as put_file:
            self.role.replace_file('/from/file', '/to/file')

            put_file.assert_called_with('/from/file', '/to/file')

    @istest
    def creates_a_remote_symbolic_link_if_it_doesnt_exist_yet(self):
        with self.execute_mock() as execute, self.mock_role_method('remote_exists') as remote_exists:
            from_file = '/from/file'
            to_file = '/to/file'
            remote_from_exists = True
            remote_to_exists = False
            sudo = 'is it sudo?'
            remote_exists.side_effect = (remote_from_exists, remote_to_exists)

            self.role.remote_symlink(from_file, to_file, sudo=sudo)

            self.assertEqual(remote_exists.mock_calls, [
                call(from_file),
                call(to_file),
            ])
            execute.assert_called_with('ln -sf %s %s' % (from_file, to_file), sudo=sudo, stdout=False)

    @istest
    def creates_a_remote_symbolic_link_if_it_exists_but_with_different_path(self):
        with self.execute_mock() as execute, self.mock_role_method('remote_exists') as remote_exists:
            from_file = '/from/file'
            to_file = '/to/file'
            another_from_file = '/another/from/file'
            remote_from_exists = True
            remote_to_exists = True
            sudo = 'is it sudo?'
            remote_exists.side_effect = (remote_from_exists, remote_to_exists)
            execute.side_effect = ('-rw-rw-r-- 1 foo foo 4490 Dez 11 22:24 %s -> %s' % (to_file, another_from_file), None)

            self.role.remote_symlink(from_file, to_file, sudo=sudo)

            self.assertEqual(remote_exists.mock_calls, [
                call(from_file),
                call(to_file),
            ])
            self.assertEqual(execute.mock_calls, [
                call('ls -la %s' % to_file, stdout=False, sudo=sudo),
                call('ln -sf %s %s' % (from_file, to_file), sudo=sudo, stdout=False),
            ])

    @istest
    def raises_exception_if_remote_file_doesnt_exist(self):
        with self.mock_role_method('remote_exists') as remote_exists:
            from_file = '/from/file'
            to_file = '/to/file'
            remote_from_exists = False
            remote_exists.side_effect = (remote_from_exists, )

            self.assertRaises(RuntimeError, self.role.remote_symlink, from_file, to_file)

    @istest
    def renders_a_template_based_on_absolute_path(self):
        template_file = os.path.join(PROJECT_ROOT, 'tests', 'unit', 'fixtures', 'some_template.txt')
        options = {'foo': 'FOO!'}

        content = self.role.render(template_file, options)

        self.assertIn('foo=FOO!', content)

    @istest
    def renders_a_template_based_on_filename(self):
        template_dir = os.path.join(PROJECT_ROOT, 'tests', 'unit', 'fixtures')
        self.role.context['loader'] = FileSystemLoader(template_dir)
        template_file = 'some_template.txt'
        options = {'foo': 'FOO!'}

        content = self.role.render(template_file, options)

        self.assertIn('foo=FOO!', content)

    @istest
    def writes_ascii_content_to_a_temp_file(self):
        content = 'some content'

        temp_file = self.role.write_to_temp_file(content)
        try:
            self.assertRegexpMatches(temp_file, r'%s/.+' % tempfile.gettempdir())

            with open(temp_file) as f:
                saved_content = f.read().strip()
                self.assertEqual(saved_content, content)
        finally:
            os.remove(temp_file)

    @istest
    def writes_utf8_content_to_a_temp_file(self):
        content = u'Tarek Ziadé'

        temp_file = self.role.write_to_temp_file(content)

        try:
            self.assertRegexpMatches(temp_file, r'%s/.+' % tempfile.gettempdir())

            with open(temp_file) as f:
                saved_content = f.read().decode('utf-8').strip()
                self.assertEqual(saved_content, content)
        finally:
            os.remove(temp_file)

    @istest
    def creates_a_new_file_when_remote_doesnt_exist_during_update(self):
        to_file = '/etc/foo.conf'
        sudo = 'is it sudo?'
        owner = 'foo'

        with self.mock_update_data(), self.mock_role_method('_force_update_file'), self.mock_role_method('remote_exists'):
            self.role.remote_exists.return_value = False

            self.assertTrue(self.role.update_file('some template', to_file, options='some options', sudo=sudo, owner=owner))
            self.role._force_update_file.assert_called_with(to_file, sudo, self.update_data.local_temp_path, owner)

    @istest
    def updates_file_with_sudo_when_user_is_passed_but_sudo_not(self):
        to_file = '/etc/foo.conf'
        owner = 'foo'

        with self.mock_update_data(), self.mock_role_method('put_file'), self.mock_role_method('change_file_owner'), self.mock_role_method('remote_exists'):
            self.role.remote_exists.return_value = False

            self.assertTrue(self.role.update_file('some template', to_file, options='some options', owner=owner))
            self.role.put_file.assert_called_with(self.update_data.local_temp_path, to_file, True)

    @istest
    def doesnt_use_sudo_implicitly_if_owner_not_passed(self):
        to_file = '/etc/foo.conf'

        with self.mock_update_data(), self.mock_role_method('put_file'), self.mock_role_method('change_file_owner'), self.mock_role_method('remote_exists'):
            self.role.remote_exists.return_value = False

            self.assertTrue(self.role.update_file('some template', to_file, options='some options'))
            self.role.put_file.assert_called_with(self.update_data.local_temp_path, to_file, False)

    @istest
    def updates_file_when_remote_exists_but_is_different(self):
        to_file = '/etc/foo.conf'
        sudo = 'is it sudo?'
        owner = 'foo'

        with self.mock_update_data(), self.mock_role_method('_force_update_file'), self.mock_role_method('remote_exists'):
            self.role.remote_exists.return_value = True
            self.update_data.from_md5 = 'some local md5'
            self.update_data.to_md5 = 'some remote md5'

            self.assertTrue(self.role.update_file('some template', to_file, options='some options', sudo=sudo, owner=owner))
            self.role._force_update_file.assert_called_with(to_file, sudo, self.update_data.local_temp_path, owner)

    @istest
    def cleans_temp_file_after_updating(self):
        to_file = '/etc/foo.conf'
        sudo = 'is it sudo?'
        owner = 'foo'

        with open(self.update_data.local_temp_path, 'w') as f:
            f.write('foo')

        with self.mock_update_data(), self.mock_role_method('_force_update_file'), self.mock_role_method('remote_exists'):
            self.role.remote_exists.return_value = True

            self.role.update_file('some template', to_file, options='some options', sudo=sudo, owner=owner)

            self.assertFalse(os.path.exists(self.update_data.local_temp_path))

    @istest
    def doesnt_update_file_when_content_is_the_same(self):
        to_file = '/etc/foo.conf'
        sudo = 'is it sudo?'
        owner = 'foo'

        with self.mock_update_data(), self.mock_role_method('_force_update_file'), self.mock_role_method('remote_exists'):
            self.role.remote_exists.return_value = True
            self.update_data.from_md5 = 'same md5'
            self.update_data.to_md5 = 'same md5'

            self.assertFalse(self.role.update_file('some template', to_file, options='some options', sudo=sudo, owner=owner))
            self.assertFalse(self.role._force_update_file.called)

    @istest
    def builds_update_data(self):
        from_file = os.path.join(PROJECT_ROOT, 'tests', 'unit', 'fixtures', 'some_template.txt')
        to_file = '/etc/foo.conf'
        options = {'foo': 'FOO!'}
        local_temp_path = '/tmp/template-to-update'
        md5_local = 'some local md5'
        md5_remote = 'some remote md5'

        with self.mock_role_method('write_to_temp_file'), self.mock_role_method('md5_local'), self.mock_role_method('md5_remote'):
            self.role.write_to_temp_file.return_value = local_temp_path
            self.role.md5_local.return_value = md5_local
            self.role.md5_remote.return_value = md5_remote

            update_data = self.role._build_update_data(from_file, options, to_file)

            self.assertEqual(update_data.local_temp_path, local_temp_path)
            self.assertEqual(update_data.from_md5, md5_local)
            self.assertEqual(update_data.to_md5, md5_remote)

    @istest
    def really_updates_file_without_owner(self):
        to_file = '/etc/foo.conf'
        local_temp_path = '/tmp/template-to-update'
        sudo = 'is it sudo?'
        owner = None

        with self.mock_role_method('put_file'):
            self.role._force_update_file(to_file, sudo, local_temp_path, owner)

            self.role.put_file.assert_called_with(local_temp_path, to_file, sudo)

    @istest
    def really_updates_file_with_owner(self):
        to_file = '/etc/foo.conf'
        local_temp_path = '/tmp/template-to-update'
        sudo = 'is it sudo?'
        owner = 'foo'

        with self.mock_role_method('put_file'), self.mock_role_method('change_file_owner'):
            self.role._force_update_file(to_file, sudo, local_temp_path, owner)

            self.role.put_file.assert_called_with(local_temp_path, to_file, sudo)
            self.role.change_file_owner.assert_called_with(to_file, owner)

    @istest
    def checks_that_content_differs_when_md5_is_different(self):
        self.assertTrue(self.role._contents_differ('some local md5', 'some remote md5'))

    @istest
    def checks_that_content_doesnt_differ_when_md5_is_the_same(self):
        self.assertFalse(self.role._contents_differ('same md5', 'same md5'))

    @istest
    def checks_that_content_doesnt_differ_when_md5_is_the_same_even_with_spaces(self):
        self.assertFalse(self.role._contents_differ('same md5      ', '  same md5'))

    @istest
    def checks_that_content_differs_when_a_md5_is_none(self):
        self.assertTrue(self.role._contents_differ(None, 'some md5'))
        self.assertTrue(self.role._contents_differ('some md5', None))
        self.assertFalse(self.role._contents_differ(None, None))

    @istest
    def reads_a_remote_file(self):
        path = '/some/path'
        sudo = 'is it sudo?'
        content = 'some content'
        with self.mock_role_method('execute_python') as execute_python:
            execute_python.return_value = content

            self.assertEqual(self.role.read_remote_file(path, sudo), content)

            execute_python.assert_called_with("import codecs; print codecs.open('%s', 'r', 'utf-8').read()" % path, stdout=False, sudo=sudo)

    @istest
    def checks_that_a_process_is_running(self):
        process = 'nginx'
        sudo = 'is it sudo?'

        with self.execute_mock() as execute:
            execute.return_value = '0'

            self.assertTrue(self.role.is_process_running(process, sudo=sudo))
            execute.assert_called_with('ps aux | egrep %s | egrep -v egrep > /dev/null;echo $?' % process, stdout=False, sudo=sudo)

    @istest
    def checks_that_a_process_is_not_running(self):
        process = 'nginx'
        sudo = 'is it sudo?'

        with self.execute_mock() as execute:
            execute.return_value = '1'

            self.assertFalse(self.role.is_process_running(process, sudo=sudo))
            execute.assert_called_with('ps aux | egrep %s | egrep -v egrep > /dev/null;echo $?' % process, stdout=False, sudo=sudo)

    @istest
    def checks_that_a_file_has_a_certain_line(self):
        content = """
        some content
        127.0.0.1    localhost
        some other content
        """
        file_path = '/some/path'
        line = '127.0.0.1 localhost'

        with self.mock_role_method('remote_exists'), self.mock_role_method('read_remote_file'):
            self.role.remote_exists.return_value = True
            self.role.read_remote_file.return_value = content

            self.assertTrue(self.role.has_line(line, file_path))

            self.role.remote_exists.assert_called_with(file_path)
            self.role.read_remote_file.assert_called_with(file_path)

    @istest
    def checks_that_a_file_doesnt_have_a_certain_line(self):
        content = """
        some content
        127.0.0.1    localhost
        some other content
        """
        file_path = '/some/path'
        line = '192.168.0.1 my-gateway'

        with self.mock_role_method('remote_exists'), self.mock_role_method('read_remote_file'):
            self.role.remote_exists.return_value = True
            self.role.read_remote_file.return_value = content

            self.assertFalse(self.role.has_line(line, file_path))

            self.role.remote_exists.assert_called_with(file_path)
            self.role.read_remote_file.assert_called_with(file_path)

    @istest
    def checks_that_a_file_doesnt_have_a_certain_line_when_file_doesnt_exist(self):
        file_path = '/some/path'
        line = '192.168.0.1 my-gateway'

        with self.mock_role_method('remote_exists'), self.mock_role_method('read_remote_file'):
            self.role.remote_exists.return_value = False

            self.assertFalse(self.role.has_line(line, file_path))

            self.role.remote_exists.assert_called_with(file_path)
            self.assertFalse(self.role.read_remote_file.called)

    @istest
    def uses_role_context_manager(self):
        manager = self.role.using('some role')
        self.assertEqual(manager.role, 'some role')
        self.assertEqual(manager.context, self.role.context)
        self.assertEqual(manager.prov, self.role.prov)

    @istest
    def test_roles_in_context(self):
        dir = {}
        self.role.context["roles_in_context"] = dir
        self.assertIs(self.role.roles_in_context, dir)

    @istest
    def removes_paths_if_in_paths_to_remove(self):

        self.role._paths_to_remove.add("foo")
        with self.mock_role_method("remove_dir") as remove:
            self.role.cleanup()
        remove.assert_called_once_with("foo", True, True)

    @istest
    def assert_paths_to_remove_empty_on_creation(self):
        self.assertEqual(len(self.role._paths_to_remove), 0)

    @istest
    def assert_no_exception_on_error_while_deleting(self):
        self.role._paths_to_remove.add("foo")
        with patch("provy.core.roles.Role.remove_dir", Mock(side_effect=IOError)):
            self.role.cleanup()

    @istest
    def assert_error_logged_on_deleting(self):
        self.role._paths_to_remove.add("foo")
        with patch("provy.core.roles.Role.remove_dir", Mock(side_effect=IOError)):
            with self.mock_role_method("log") as log:
                self.role.cleanup()
        self.assertEqual(len(log.mock_calls), 1)

    @istest
    def test_remote_list_dir(self):
        with self.mock_role_method("execute_python") as execute:
            execute.return_value = "{}"
            self.role.remote_list_directory("/some/path")
        execute.assert_called_once_with('''import os, json; print json.dumps(os.listdir('/some/path'))''', False, True)

    @istest
    def puts_file_when_executing_python_script(self):
        sudo = 'is it sudo?'
        stdout = 'should it stdout?'
        with self.mock_role_methods('execute', 'create_remote_temp_file', 'put_file') as (execute, create_remote_temp_file, put_file):
            create_remote_temp_file.return_value = "/tmp/scriptfoo.py"

            self.role.execute_python_script("script", stdout, sudo)

            put_file.assert_called_once_with(ANY, "/tmp/scriptfoo.py", sudo, False)
            execute.assert_called_once_with(
                'python "{}"'.format("/tmp/scriptfoo.py"),
                stdout,
                sudo
            )

    @istest
    def test_script_converted(self):
        with patch.multiple("provy.core.roles.Role", execute=DEFAULT,
                            create_remote_temp_file=DEFAULT,
                            put_file=DEFAULT) as values:
            values['create_remote_temp_file'].return_value = "/tmp/scriptfoo.py"
            self.role.execute_python_script("script", False, False)

        self.assertTrue(isinstance(values['put_file'].mock_calls[0][1][0], StringIO))

    @istest
    def test_script_file_not_converted(self):
        script = Mock(spec=file)
        with patch.multiple("provy.core.roles.Role", execute=DEFAULT,
                            create_remote_temp_file=DEFAULT,
                            put_file=DEFAULT) as values:
            values['create_remote_temp_file'].return_value = "/tmp/scriptfoo.py"
            self.role.execute_python_script(script, False, False)

        self.assertIs(values['put_file'].mock_calls[0][1][0], script)


class TestEnsureLine(CoreRoleTest):
    def setUp(self):
        super(TestEnsureLine, self).setUp()
        self.tested_file = os.path.join(tempfile.gettempdir(), "res" + str(uuid.uuid4()))
        self.line_file = os.path.join(tempfile.gettempdir(), "line" + str(uuid.uuid4()))

    def tearDown(self):
        super(TestEnsureLine, self).tearDown()
        # os.remove(self.tested_file)
        # os.remove(self.line_file)

    def _write(self, file_name, content):
        """
            Writes content to a file. Helper/
        """
        with open(file_name, "w") as f:
            f.write(content.strip())

    def execute_script(self):
        """
        Executes tested script
        """
        script = self.role.render("base_ensure_line.py", options={
            "line": self.line_file,
            "target": self.tested_file
        })
        exec(script)

    def _assert_content(self, content):
        """
            Checks content of tested file
        """
        with open(self.tested_file) as f:
            self.assertEquals(content.strip(), f.read().strip())

    @istest
    def writes_line_if_there_is_none(self):
        TESTED_FILE = """
foo bar
bar baz
baz foo
        """
        DESIRED_CONTENT = """
foo bar
bar baz
baz foo
foo foo
        """
        self._write(self.tested_file, TESTED_FILE)
        self._write(self.line_file, "foo foo")
        self.execute_script()
        self._assert_content(DESIRED_CONTENT)

    @istest
    def doesnt_touch_file_if_there_is_line(self):
        TESTED_FILE = """
foo bar
bar baz
baz foo
        """
        self._write(self.tested_file, TESTED_FILE)
        self._write(self.line_file, "bar baz")
        self.execute_script()
        self._assert_content(TESTED_FILE)


class UsingRoleTest(ProvyTestCase):
    def any_context(self):
        return {'used_roles': {}}

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

        with UsingRole(DummyRole, None, self.any_context()):
            self.assertTrue(sentinel.called)

    @istest
    def triggers_schedule_cleanup_when_exiting_with_block(self):
        sentinel = MagicMock()

        class DummyRole(Role):
            def schedule_cleanup(self):
                sentinel()

        with UsingRole(DummyRole, None, self.any_context()):
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

        with using:
            self.assertEqual(using.role_instance, instance)


class RemoteTempFileTests(ProvyTestCase):

    def any_context(self):
        return {'used_roles': {}}

    def setUp(self):
        super(RemoteTempFileTests, self).setUp()
        self.instance = Role(None, self.any_context())
        self.patcher = patch("provy.core.roles.Role.remote_temp_dir", Mock(return_value="/tmp"))
        self.patcher.start()
        self.ensure_dir_patcher = patch("provy.core.roles.Role.ensure_dir", Mock(return_value="/tmp"))
        self.ensure_dir_patcher.start()

    def tearDown(self):
        self.patcher.stop()
        self.ensure_dir_patcher.stop()

    @istest
    def file_created_in_tempdir(self):
        file = self.instance.create_remote_temp_file("foo")
        self.assertTrue(file.startswith("/tmp"))

    @istest
    def directory_created_in_tempdir(self):
        folder = self.instance.create_remote_temp_dir("foo")
        self.assertTrue(folder.startswith("/tmp"))

    @istest
    def file_created_with_proper_prefix(self):
        file = self.instance.create_remote_temp_dir("foo")
        self.assertTrue(file.startswith("/tmp/foo"))

    @istest
    def directory_created_with_proper_name(self):
        dir = self.instance.create_remote_temp_dir("foobar")
        self.assertEqual("/tmp/foobar", dir)

    @istest
    def file_created_with_proper_suffix(self):
        file = self.instance.create_remote_temp_file(suffix="sql")
        self.assertEqual(file[-3:], "sql")

    @istest
    def files_will_be_deleted_on_cleanup_if_requested(self):
        file = self.instance.create_remote_temp_file(cleanup=True)
        self.assertIn(file, self.instance._paths_to_remove)

    @istest
    def directories_will_be_deleted_on_cleanup_if_requested(self):
        directory = self.instance.create_remote_temp_dir(cleanup=True)
        self.assertIn(directory, self.instance._paths_to_remove)

    @istest
    def files_will_not_be_deleted_on_cleanup_if_requested(self):
        file = self.instance.create_remote_temp_file(cleanup=False)
        self.assertNotIn(file, self.instance._paths_to_remove)

    @istest
    def directories_will_not_be_deleted_on_cleanup_if_requested(self):
        dirs = self.instance.create_remote_temp_file(cleanup=False)
        self.assertNotIn(dirs, self.instance._paths_to_remove)

    @istest
    def check_if_random_files_have_different_names(self):
        dirs = set()
        for _ in range(100):
            dirs.add(self.instance.create_remote_temp_file())
        self.assertEqual(len(dirs), 100)

    @istest
    def check_if_random_directories_have_different_names(self):
        dirs = set()
        for _ in range(100):
            dirs.add(self.instance.create_remote_temp_dir())
        self.assertEqual(len(dirs), 100)

    @istest
    def check_if_directories_have_proper_mode(self):
        mode = "666"
        with self.mock_role_method("change_dir_mode") as change_dir_mode:
            dir = self.instance.create_remote_temp_dir(chmod=mode)
        change_dir_mode.assert_called_once_with(dir, mode)

    @istest
    def check_if_directories_have_proper_owner(self):
        owner = "user"
        self.instance.create_remote_temp_dir(owner=owner)
        self.instance.ensure_dir.assert_called_once_with(ANY, owner, ANY)
