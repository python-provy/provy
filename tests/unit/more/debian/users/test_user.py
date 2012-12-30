from contextlib import contextmanager

from mock import MagicMock, patch, call
from nose.tools import istest

from provy.more.debian import UserRole
from tests.unit.tools.helpers import ProvyTestCase


example_groups = """
root
daemon
bin
sys
adm
tty
disk
lp
mail
"""


class UserRoleTest(ProvyTestCase):
    def setUp(self):
        self.role = UserRole(None, {})

    @istest
    def checks_that_a_group_exists(self):
        with self.execute_mock() as execute:
            execute.return_value = example_groups

            self.assertTrue(self.role.group_exists('daemon'))
            execute.assert_called_with("cat /etc/group | cut -d ':' -f 1", stdout=False, sudo=True)

    @istest
    def checks_that_a_group_doesnt_exist(self):
        with self.execute_mock() as execute:
            execute.return_value = example_groups

            self.assertFalse(self.role.group_exists('iis'))
