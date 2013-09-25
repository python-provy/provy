from mock import call, ANY, patch
from nose.tools import istest

from provy.more.debian import UserRole
from tests.unit.tools.helpers import ProvyTestCase

from provy.more.debian.users.passwd_utils import hash_password_function, random_salt_function

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
        with self.mock_role_methods('ensure_group', 'ensure_user_groups', 'user_exists', 'execute', 'set_user_password'):
            with self.provisioning_to('debian'):
                self.role.user_exists.return_value = False

                self.role.ensure_user(username='foo-user', identified_by='foo-pass', groups=['foo-group', 'bar-group'])

                self.assertEqual(self.role.ensure_group.mock_calls, [
                    call('foo-group'),
                    call('bar-group'),
                ])
                self.assertEqual(self.role.execute.mock_calls, [
                    call('useradd -g foo-group -s /bin/bash -d /home/foo-user -m foo-user', stdout=False, sudo=True)
                ])
                self.role.set_user_password.assert_called_once_with(
                    'foo-user', 'foo-pass', False
                )
                self.role.ensure_user_groups.assert_called_once_with('foo-user', ['foo-group', 'bar-group'])


    @istest
    def ensures_user_is_created_with_only_group_as_username(self):
        with self.mock_role_methods('ensure_group', 'ensure_user_groups', 'user_exists', 'execute', 'set_user_password'):
            with self.provisioning_to('debian'):
                self.role.user_exists.return_value = False

                self.role.ensure_user(username='foo-user')

                self.assertEqual(self.role.execute.mock_calls, [
                    call('useradd -g foo-user -s /bin/bash -d /home/foo-user -m foo-user', stdout=False, sudo=True),
                ])

    @istest
    def ensures_user_is_created_with_different_home(self):
        with self.mock_role_methods('ensure_group', 'ensure_user_groups', 'user_exists', 'execute', 'set_user_password'):
            with self.provisioning_to('debian'):
                self.role.user_exists.return_value = False

                self.role.ensure_user(username='foo-user', home_folder='/srv/bar')

                self.assertEqual(self.role.execute.mock_calls, [
                    call('useradd -g foo-user -s /bin/bash -d /srv/bar -m foo-user', stdout=False, sudo=True),
                ])

    @istest
    def doesnt_add_but_set_user_as_admin_for_debian_when_it_already_exists_but_is_not_admin_yet(self):
        with self.mock_role_methods('ensure_group', 'ensure_user_groups', 'user_exists', 'user_in_group', 'execute', "set_user_password"):
            with self.provisioning_to('debian'):
                self.role.user_exists.return_value = True
                self.role.user_in_group.return_value = False

                self.role.ensure_user(username='foo-user', is_admin=True)

                self.role.user_in_group.assert_called_once_with('foo-user', 'admin')
                self.assertEqual(self.role.execute.mock_calls, [
                    call('usermod -G admin foo-user', sudo=True, stdout=False),
                ])

    @istest
    def doesnt_add_but_set_user_as_admin_for_ubuntu_when_it_already_exists_but_is_not_admin_yet(self):
        with self.mock_role_methods('ensure_group', 'ensure_user_groups', 'user_exists', 'user_in_group', 'execute', 'set_user_password'):
            with self.provisioning_to('ubuntu'):
                self.role.user_exists.return_value = True
                self.role.user_in_group.return_value = False

                self.role.ensure_user(username='foo-user', is_admin=True)

                self.role.user_in_group.assert_called_once_with('foo-user', 'sudo')
                self.assertEqual(self.role.execute.mock_calls, [
                    call('usermod -G sudo foo-user', sudo=True, stdout=False),
                ])

    @istest
    def just_add_user_to_groups_if_its_already_admin(self):
        with self.mock_role_methods('ensure_group', 'ensure_user_groups', 'user_exists', 'user_in_group', 'execute', 'set_user_password'):
            with self.provisioning_to('ubuntu'):
                self.role.user_exists.return_value = True
                self.role.user_in_group.return_value = True

                self.role.ensure_user(username='foo-user', is_admin=True, groups=['foo-group', 'bar-group'])

                self.assertFalse(self.role.execute.called)
                self.role.ensure_user_groups.assert_called_once_with('foo-user', ['foo-group', 'bar-group'])

    @istest
    def check_if_two_generated_salts_are_different(self):
        """
        Instead of checking if output is truly random, we'll just check if
        in two conseutive calls different functions will be returned
        """
        self.assertNotEqual(random_salt_function(), random_salt_function())

    @istest
    def check_random_add_function_output_is_as_specified(self):
        self.assertTrue(len(random_salt_function(salt_len=125)), 125)


    @istest
    def check_crypt_function_gives_expected_output_for_known_magic_and_salt(self):
        password = "foobarbaz"
        expected_hash = "$6$SqAoXRvk$spgLlL/WL/vcb16ZZ4cMdF5uN90IjH0PpYKdMhqyW.BxXJEVc5RyvnpWcT.OKKJO2vsp32.CWDEd45K6r05bL0"
        salt = "SqAoXRvk"

        self.assertEqual(expected_hash, hash_password_function(password, salt))

    @istest
    def check_crypt_function_uses_random_salt(self):
        password = "foobarbaz"
        expected_hash = "$6$SqAoXRvk$spgLlL/WL/vcb16ZZ4cMdF5uN90IjH0PpYKdMhqyW.BxXJEVc5RyvnpWcT.OKKJO2vsp32.CWDEd45K6r05bL0"
        salt = "SqAoXRvk"

        with patch("provy.more.debian.users.passwd_utils.random_salt_function") as rnd:
            rnd.return_value = salt
            self.assertEqual(expected_hash, hash_password_function(password))
            self.assertTrue(rnd.called)



    @istest
    def check_set_user_password_when_password_is_encrypted(self):
        encrypted_password = "$6$SqAoXRvk$spgLlL/WL/vcb16ZZ4cMdF5uN90IjH0PpYKdMhqyW.BxXJEVc5RyvnpWcT.OKKJO2vsp32.CWDEd45K6r05bL0"
        with self.mock_role_methods("create_remote_temp_file", 'put_file', 'execute', "remove_file"):
            self.role.create_remote_temp_file.return_value = "/tmp/random"
            self.role.set_user_password("foo",  encrypted_password, encrypted=True)
            self.role.put_file.assert_called_once_with(
                ANY,
                "/tmp/random",
                sudo=True,
                stdout=False
            )
            #self.role.execute.assert_called_with()
            self.assertIn(
                call('cat "/tmp/random" | chpasswd -e', sudo=True, stdout=False),
                self.role.execute.mock_calls
            )


    @istest
    def check_set_user_password_when_password_is_not_encrypted(self):
        with self.mock_role_methods("create_remote_temp_file", 'put_file', 'execute', "remove_file"):
            self.role.create_remote_temp_file.return_value = "/tmp/random"
            self.role.set_user_password("foo", "foo-pass")
            self.role.put_file.assert_called_once_with(
                ANY,
                "/tmp/random",
                sudo=True,
                stdout=False
            )
            #self.role.execute.assert_called_with()
            self.assertIn(
                call('cat "/tmp/random" | chpasswd ', sudo=True, stdout=False),
                self.role.execute.mock_calls
            )

