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
