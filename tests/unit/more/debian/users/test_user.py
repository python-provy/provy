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
example_users = """
root
daemon
bin
sys
sync
games
man
lp
mail
"""
example_groups_for_user = """
foo : foo adm cdrom sudo dip plugdev lpadmin sambashare
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

    @istest
    def checks_group_by_exact_name(self):
        with self.execute_mock() as execute:
            execute.return_value = example_groups

            self.assertFalse(self.role.group_exists('roo'))
            self.assertFalse(self.role.group_exists('roots'))

    @istest
    def checks_that_a_user_exists(self):
        with self.execute_mock() as execute:
            execute.return_value = example_users

            self.assertTrue(self.role.user_exists('daemon'))
            execute.assert_called_with("cat /etc/passwd | cut -d ':' -f 1", stdout=False, sudo=True)

    @istest
    def checks_that_a_user_doesnt_exist(self):
        with self.execute_mock() as execute:
            execute.return_value = example_users

            self.assertFalse(self.role.user_exists('iis'))

    @istest
    def checks_user_by_exact_name(self):
        with self.execute_mock() as execute:
            execute.return_value = example_users

            self.assertFalse(self.role.user_exists('roo'))
            self.assertFalse(self.role.user_exists('roots'))

    @istest
    def checks_that_a_user_is_in_a_certain_group(self):
        with self.execute_mock() as execute:
            execute.return_value = example_groups_for_user

            self.assertTrue(self.role.user_in_group('foo', 'sudo'))
            execute.assert_called_with("groups foo", stdout=False, sudo=True)

    @istest
    def checks_that_a_user_is_not_in_a_certain_group(self):
        with self.execute_mock() as execute:
            execute.return_value = example_groups_for_user

            self.assertFalse(self.role.user_in_group('foo', 'root'))

    @istest
    def checks_that_a_user_is_in_a_certain_group_by_exact_name(self):
        with self.execute_mock() as execute:
            execute.return_value = example_groups_for_user

            self.assertFalse(self.role.user_in_group('foo', 'sud'))
            self.assertFalse(self.role.user_in_group('foo', 'sudoer'))

    @istest
    def cannot_check_user_in_groups_if_username_doesnt_exist(self):
        with self.execute_mock() as execute:
            execute.return_value = 'groups: foo: User unexistant'

            self.assertRaises(ValueError, self.role.user_in_group, 'foo', 'bar')
