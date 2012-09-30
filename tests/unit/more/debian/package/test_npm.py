from contextlib import contextmanager

from mock import MagicMock, patch, call
from nose.tools import istest

from provy.core.roles import DistroInfo
from provy.more.debian import AptitudeRole, NodeJsRole, NPMRole
from tests.unit.tools.helpers import ProvyTestCase


class NPMRoleTest(ProvyTestCase):
    def setUp(self):
        self.role = NPMRole(prov=None, context={})

    @istest
    def provisions_node_js_as_dependency(self):
        with self.mock_role_method('provision_role') as provision_role:
            self.role.provision()

            provision_role.assert_called_with(NodeJsRole)

    @istest
    def checks_that_a_package_is_installed_by_name(self):
        with self.execute_mock() as execute:
            execute.return_value = 'socket.io'

            self.assertTrue(self.role.is_package_installed('socket.io'))

            execute.assert_called_with("npm --global list | egrep 'socket.io'", stdout=False, sudo=True)

    @istest
    def checks_that_a_package_is_not_installed_by_name(self):
        with self.execute_mock() as execute:
            execute.return_value = ''

            self.assertFalse(self.role.is_package_installed('socket.io'))

            execute.assert_called_with("npm --global list | egrep 'socket.io'", stdout=False, sudo=True)

    @istest
    def checks_that_a_package_is_installed_by_name_and_version(self):
        with self.execute_mock() as execute:
            execute.return_value = 'socket.io@0.6.17'

            self.assertTrue(self.role.is_package_installed('socket.io', '0.6.17'))

            execute.assert_called_with("npm --global list | egrep 'socket.io@0.6.17'", stdout=False, sudo=True)

    @istest
    def checks_that_a_package_is_not_installed_by_name_and_version(self):
        with self.execute_mock() as execute:
            execute.return_value = ''

            self.assertFalse(self.role.is_package_installed('socket.io', '0.6.17'))

            execute.assert_called_with("npm --global list | egrep 'socket.io@0.6.17'", stdout=False, sudo=True)

    @istest
    def installs_a_package_if_its_not_installed_yet_by_name(self):
        with self.execute_mock() as execute, patch('provy.more.debian.NPMRole.is_package_installed') as is_package_installed:
            is_package_installed.return_value = False
            self.role.ensure_package_installed('socket.io')

            execute.assert_called_with('npm install --global socket.io', stdout=False, sudo=True)

    @istest
    def doesnt_install_a_package_if_its_already_installed_yet_by_name(self):
        with self.execute_mock() as execute, patch('provy.more.debian.NPMRole.is_package_installed') as is_package_installed:
            is_package_installed.return_value = True
            self.role.ensure_package_installed('socket.io')

            self.assertFalse(execute.called)

    @istest
    def installs_a_package_if_its_not_installed_yet_by_name_and_version(self):
        with self.execute_mock() as execute, patch('provy.more.debian.NPMRole.is_package_installed') as is_package_installed:
            is_package_installed.return_value = False
            self.role.ensure_package_installed('socket.io', '0.6.17')

            execute.assert_called_with('npm install --global socket.io@0.6.17', stdout=False, sudo=True)

    @istest
    def installs_a_package_if_its_not_installed_yet_by_name_and_version_with_stdout(self):
        with self.execute_mock() as execute, patch('provy.more.debian.NPMRole.is_package_installed') as is_package_installed:
            is_package_installed.return_value = False
            self.role.ensure_package_installed('socket.io', '0.6.17', stdout=True)

            execute.assert_called_with('npm install --global socket.io@0.6.17', stdout=True, sudo=True)

    @istest
    def installs_a_package_if_its_not_installed_yet_by_name_and_version_without_sudo(self):
        with self.execute_mock() as execute, patch('provy.more.debian.NPMRole.is_package_installed') as is_package_installed:
            is_package_installed.return_value = False
            self.role.ensure_package_installed('socket.io', '0.6.17', sudo=False)

            execute.assert_called_with('npm install --global socket.io@0.6.17', stdout=False, sudo=False)
