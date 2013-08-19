from mock import call
from nose.tools import istest

from provy.more.centos import UserRole
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
        super(UserRoleTest, self).setUp()
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

    @istest
    def ensures_a_group_is_created(self):
        with self.mock_role_methods('group_exists', 'execute'):
            self.role.group_exists.return_value = False

            self.role.ensure_group('foo')

            self.role.group_exists.assert_called_once_with('foo')
            self.role.execute.assert_called_once_with('groupadd foo', sudo=True, stdout=False)

    @istest
    def ensures_a_group_is_created_with_group_id(self):
        with self.mock_role_methods('group_exists', 'execute'):
            self.role.group_exists.return_value = False

            self.role.ensure_group('foo', group_id=123)

            self.role.group_exists.assert_called_once_with('foo')
            self.role.execute.assert_called_once_with('groupadd --gid 123 foo', sudo=True, stdout=False)

    @istest
    def doesnt_create_group_if_it_already_exists(self):
        with self.mock_role_methods('group_exists', 'execute'):
            self.role.group_exists.return_value = True

            self.role.ensure_group('foo')

            self.assertFalse(self.role.execute.called)

    @istest
    def ensures_the_user_enters_the_provided_groups_when_not_there_already(self):
        with self.mock_role_methods('user_in_group', 'execute'):
            self.role.user_in_group.side_effect = [True, False]

            self.role.ensure_user_groups('foo', ['bar', 'baz'])

            self.assertEqual(self.role.user_in_group.mock_calls, [
                call('foo', 'bar'),
                call('foo', 'baz'),
            ])
            self.role.execute.assert_called_once_with('usermod -G baz foo', sudo=True, stdout=False)

    @istest
    def ensures_user_is_created_when_not_created_yet(self):
        with self.mock_role_methods('ensure_group', 'ensure_user_groups', 'user_exists', 'execute'):
            self.role.user_exists.return_value = False

            self.role.ensure_user(username='foo-user', identified_by='foo-pass', groups=['foo-group', 'bar-group'])

            self.assertEqual(self.role.ensure_group.mock_calls, [
                call('foo-group'),
                call('bar-group'),
            ])
            self.assertEqual(self.role.execute.mock_calls, [
                call('useradd -g foo-group -s /bin/bash -p foo-pass -d /home/foo-user -m foo-user', stdout=False, sudo=True),
                call('echo "foo-user:foo-pass" | chpasswd', stdout=False, sudo=True),
            ])
            self.role.ensure_user_groups.assert_called_once_with('foo-user', ['foo-group', 'bar-group'])

    @istest
    def ensures_user_is_created_with_irrelevant_password(self):
        with self.mock_role_methods('ensure_group', 'ensure_user_groups', 'user_exists', 'execute'):
            self.role.user_exists.return_value = False

            self.role.ensure_user(username='foo-user', groups=['foo-group', 'bar-group'])

            self.assertEqual(self.role.execute.mock_calls, [
                call('useradd -g foo-group -s /bin/bash -p none -d /home/foo-user -m foo-user', stdout=False, sudo=True),
            ])

    @istest
    def ensures_user_is_created_with_only_group_as_username(self):
        with self.mock_role_methods('ensure_group', 'ensure_user_groups', 'user_exists', 'execute'):
            self.role.user_exists.return_value = False

            self.role.ensure_user(username='foo-user')

            self.assertEqual(self.role.execute.mock_calls, [
                call('useradd -g foo-user -s /bin/bash -p none -d /home/foo-user -m foo-user', stdout=False, sudo=True),
            ])

    @istest
    def ensures_user_is_created_with_different_home(self):
        with self.mock_role_methods('ensure_group', 'ensure_user_groups', 'user_exists', 'execute'):
            self.role.user_exists.return_value = False

            self.role.ensure_user(username='foo-user', home_folder='/srv/bar')

            self.assertEqual(self.role.execute.mock_calls, [
                call('useradd -g foo-user -s /bin/bash -p none -d /srv/bar -m foo-user', stdout=False, sudo=True),
            ])

    @istest
    def doesnt_add_but_set_user_as_admin_when_it_already_exists_but_is_not_admin_yet(self):
        with self.mock_role_methods('ensure_group', 'ensure_user_groups', 'user_exists', 'user_in_group', 'execute'):
            self.role.user_exists.return_value = True
            self.role.user_in_group.return_value = False

            self.role.ensure_user(username='foo-user', is_admin=True)

            self.role.user_in_group.assert_called_once_with('foo-user', 'wheel')
            self.assertEqual(self.role.execute.mock_calls, [
                call('usermod -G wheel foo-user', sudo=True, stdout=False),
            ])
