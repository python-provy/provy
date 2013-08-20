from mock import call, patch
from nose.tools import istest

from .fixtures import (
    FOO_DB_WITH_JOHN_GRANTS,
    FOO_DB_WITHOUT_JOHN_GRANTS,
    FOO_DB_WITH_JOHN_GRANTS_AND_GRANT_OPTION,
    HOSTS_FOR_USER,
    DATABASES,
)
from provy.more.debian import AptitudeRole, MySQLRole
from tests.unit.tools.helpers import ProvyTestCase


class MySQLRoleTest(ProvyTestCase):
    def setUp(self):
        super(MySQLRoleTest, self).setUp()
        self.role = MySQLRole(prov=None, context={})

    @istest
    def has_no_grant_if_not_granted(self):
        with self.execute_mock() as execute:
            execute.return_value = FOO_DB_WITHOUT_JOHN_GRANTS
            self.assertFalse(self.role.has_grant('ALL', 'foo', 'john', '%', False))
            execute.assert_called_with('''mysql -u root -E -e "SHOW GRANTS FOR 'john'@'%';" mysql''', sudo=True, stdout=False)

    @istest
    def has_grant_if_granted(self):
        with self.execute_mock() as execute:
            execute.return_value = FOO_DB_WITH_JOHN_GRANTS
            self.assertTrue(self.role.has_grant('ALL', 'foo', 'john', '%', False))
            execute.assert_called_with('''mysql -u root -E -e "SHOW GRANTS FOR 'john'@'%';" mysql''', sudo=True, stdout=False)

    @istest
    def has_grant_if_granted_with_grant_option(self):
        with self.execute_mock() as execute:
            execute.return_value = FOO_DB_WITH_JOHN_GRANTS_AND_GRANT_OPTION
            self.assertTrue(self.role.has_grant('ALL', 'foo', 'john', '%', True))
            execute.assert_called_with('''mysql -u root -E -e "SHOW GRANTS FOR 'john'@'%';" mysql''', sudo=True, stdout=False)

    @istest
    def has_grant_if_granted_even_if_provided_full(self):
        with self.execute_mock() as execute:
            execute.return_value = FOO_DB_WITH_JOHN_GRANTS
            self.assertTrue(self.role.has_grant('ALL PRIVILEGES', 'foo', 'john', '%', False))
            execute.assert_called_with('''mysql -u root -E -e "SHOW GRANTS FOR 'john'@'%';" mysql''', sudo=True, stdout=False)

    @istest
    def has_grant_if_granted_even_if_provided_as_lowercase_string(self):
        with self.execute_mock() as execute:
            execute.return_value = FOO_DB_WITH_JOHN_GRANTS
            self.assertTrue(self.role.has_grant('all', 'foo', 'john', '%', False))
            execute.assert_called_with('''mysql -u root -E -e "SHOW GRANTS FOR 'john'@'%';" mysql''', sudo=True, stdout=False)

    @istest
    def can_get_user_grants(self):
        with self.execute_mock() as execute:
            execute.return_value = FOO_DB_WITHOUT_JOHN_GRANTS
            expected = ["GRANT USAGE ON *.* TO 'john'@'%' IDENTIFIED BY PASSWORD '*B9EE00DF55E7C816911C6DA56F1E3A37BDB31093'"]
            self.assertEqual(expected, self.role.get_user_grants('john', '%'))
            execute.assert_called_with('''mysql -u root -E -e "SHOW GRANTS FOR 'john'@'%';" mysql''', sudo=True, stdout=False)

    @istest
    def installs_necessary_packages_to_provision(self):
        with self.using_stub(AptitudeRole) as mock_aptitude, self.execute_mock() as execute:
            mock_aptitude.ensure_package_installed.return_value = 'some result'

            self.role.provision()

            self.assertEqual(execute.mock_calls, [
                call('echo "mysql-server mysql-server/root_password select temppass" | debconf-set-selections',
                     stdout=False, sudo=True),
                call('echo "mysql-server mysql-server/root_password_again select temppass" | debconf-set-selections',
                     stdout=False, sudo=True),
                call("mysqladmin -u %s -p'temppass' password '%s'" % (self.role.mysql_root_user, self.role.mysql_root_pass),
                     stdout=False, sudo=True),
            ])
            self.assertEqual(mock_aptitude.ensure_package_installed.mock_calls, [
                call('mysql-server'),
                call('mysql-client'),
                call('libmysqlclient-dev'),
            ])

    @istest
    def installs_necessary_packages_to_provision_again(self):
        with self.using_stub(AptitudeRole) as mock_aptitude, self.execute_mock() as execute:
            mock_aptitude.ensure_package_installed.return_value = False

            self.role.provision()

            self.assertEqual(execute.mock_calls, [
                call('echo "mysql-server mysql-server/root_password select temppass" | debconf-set-selections',
                     stdout=False, sudo=True),
                call('echo "mysql-server mysql-server/root_password_again select temppass" | debconf-set-selections',
                     stdout=False, sudo=True),
            ])
            self.assertEqual(mock_aptitude.ensure_package_installed.mock_calls, [
                call('mysql-server'),
                call('mysql-client'),
                call('libmysqlclient-dev'),
            ])

    @istest
    def gets_user_hosts(self):
        with self.execute_mock() as execute:
            execute.return_value = HOSTS_FOR_USER

            hosts = self.role.get_user_hosts('root')

            self.assertEqual(hosts, [
                '127.0.0.1',
                '::1',
                'my-desktop',
                'localhost',
            ])
            execute.assert_called_with('''mysql -u root -E -e "select Host from mysql.user where LOWER(User)='root'" mysql''',
                                       sudo=True, stdout=False)

    @istest
    def gets_user_hosts_using_password(self):
        with self.execute_mock() as execute:
            execute.return_value = HOSTS_FOR_USER
            self.role.mysql_root_pass = 'mypass'

            hosts = self.role.get_user_hosts('root')

            self.assertEqual(hosts, [
                '127.0.0.1',
                '::1',
                'my-desktop',
                'localhost',
            ])
            execute.assert_called_with('''mysql -u root --password="mypass" -E -e "select Host from mysql.user where LOWER(User)='root'" mysql''',
                                       sudo=True, stdout=False)

    @istest
    def gets_empty_user_hosts(self):
        with self.execute_mock() as execute:
            execute.return_value = ''

            hosts = self.role.get_user_hosts('root')

            self.assertEqual(hosts, [])
            execute.assert_called_with('''mysql -u root -E -e "select Host from mysql.user where LOWER(User)='root'" mysql''',
                                       sudo=True, stdout=False)

    @istest
    def checks_that_a_user_exists(self):
        with patch.object(self.role, 'get_user_hosts') as get_user_hosts:
            get_user_hosts.return_value = ['localhost']

            self.assertTrue(self.role.user_exists('johndoe', 'localhost'))

            get_user_hosts.assert_called_with('johndoe')

    @istest
    def checks_that_a_user_doesnt_exist(self):
        with patch.object(self.role, 'get_user_hosts') as get_user_hosts:
            get_user_hosts.return_value = ['localhost']

            self.assertFalse(self.role.user_exists('johndoe', 'somewhere-else'))

            get_user_hosts.assert_called_with('johndoe')

    @istest
    def creates_a_user_if_it_doesnt_exist_yet(self):
        with patch.object(self.role, 'user_exists') as user_exists, self.execute_mock() as execute:
            user_exists.return_value = False

            result = self.role.ensure_user('johndoe', 'mypass', 'localhost')

            self.assertTrue(result)
            execute.assert_called_with("""mysql -u root -e "CREATE USER 'johndoe'@'localhost' IDENTIFIED BY 'mypass';" mysql""", sudo=True, stdout=False)

    @istest
    def doesnt_create_user_if_it_already_exists(self):
        with patch.object(self.role, 'user_exists') as user_exists, self.execute_mock() as execute:
            user_exists.return_value = True

            result = self.role.ensure_user('johndoe', 'mypass', 'localhost')

            self.assertFalse(result)
            self.assertFalse(execute.called)

    @istest
    def creates_a_user_with_mysql_password(self):
        with patch.object(self.role, 'user_exists') as user_exists, self.execute_mock() as execute:
            user_exists.return_value = False
            self.role.mysql_root_pass = 'otherpass'

            result = self.role.ensure_user('johndoe', 'mypass', 'localhost')

            self.assertTrue(result)
            execute.assert_called_with("""mysql -u root --password="otherpass" -e "CREATE USER 'johndoe'@'localhost' IDENTIFIED BY 'mypass';" mysql""",
                                       sudo=True, stdout=False)

    @istest
    def checks_that_a_database_is_present(self):
        with self.execute_mock() as execute:
            execute.return_value = DATABASES

            result = self.role.is_database_present('performance_schema')

            self.assertTrue(result)
            execute.assert_called_with('mysql -u root -E -e "SHOW DATABASES" mysql', stdout=False, sudo=True)

    @istest
    def checks_that_a_database_is_not_present(self):
        with self.execute_mock() as execute:
            execute.return_value = DATABASES

            result = self.role.is_database_present('bad_bad_database')

            self.assertFalse(result)
            execute.assert_called_with('mysql -u root -E -e "SHOW DATABASES" mysql', stdout=False, sudo=True)

    @istest
    def checks_that_a_database_is_not_present_when_there_is_none(self):
        with self.execute_mock() as execute:
            execute.return_value = ''

            result = self.role.is_database_present('performance_schema')

            self.assertFalse(result)
            execute.assert_called_with('mysql -u root -E -e "SHOW DATABASES" mysql', stdout=False, sudo=True)

    @istest
    def creates_a_database_if_it_doesnt_exist_yet(self):
        with patch.object(self.role, 'is_database_present') as is_database_present, self.execute_mock() as execute:
            is_database_present.return_value = False

            result = self.role.ensure_database('my_data')

            self.assertTrue(result)
            execute.assert_called_with('mysql -u root -e "CREATE DATABASE my_data" mysql', sudo=True, stdout=False)

    @istest
    def doesnt_create_a_database_if_it_already_exists(self):
        with patch.object(self.role, 'is_database_present') as is_database_present, self.execute_mock() as execute:
            is_database_present.return_value = True

            result = self.role.ensure_database('my_data')

            self.assertFalse(result)
            self.assertFalse(execute.called)

    @istest
    def grants_privilege_if_not_granted_yet(self):
        with patch.object(self.role, 'has_grant') as has_grant, self.execute_mock() as execute:
            has_grant.return_value = False

            result = self.role.ensure_grant('ALL PRIVILEGES', on='foo', username='john', login_from='%', with_grant_option=False)

            self.assertTrue(result)
            execute.assert_called_with('''mysql -u root -e "GRANT ALL PRIVILEGES ON foo.* TO 'john'@'%'" mysql''', stdout=False, sudo=True)

    @istest
    def grants_privilege_if_not_granted_yet_for_table(self):
        with patch.object(self.role, 'has_grant') as has_grant, self.execute_mock() as execute:
            has_grant.return_value = False

            result = self.role.ensure_grant('ALL PRIVILEGES', on='foo.bar', username='john', login_from='%', with_grant_option=False)

            self.assertTrue(result)
            execute.assert_called_with('''mysql -u root -e "GRANT ALL PRIVILEGES ON foo.bar TO 'john'@'%'" mysql''', stdout=False, sudo=True)

    @istest
    def grants_privilege_with_grant_option_if_not_granted_yet(self):
        with patch.object(self.role, 'has_grant') as has_grant, self.execute_mock() as execute:
            has_grant.return_value = False

            result = self.role.ensure_grant('ALL PRIVILEGES', on='foo', username='john', login_from='%', with_grant_option=True)

            self.assertTrue(result)
            execute.assert_called_with('''mysql -u root -e "GRANT ALL PRIVILEGES ON foo.* TO 'john'@'%' WITH GRANT OPTION" mysql''', stdout=False, sudo=True)

    @istest
    def doesnt_grant_privilege_if_already_granted(self):
        with patch.object(self.role, 'has_grant') as has_grant, self.execute_mock() as execute:
            has_grant.return_value = True

            result = self.role.ensure_grant('ALL PRIVILEGES', on='foo', username='john', login_from='%', with_grant_option=True)

            self.assertFalse(result)
            self.assertFalse(execute.called)
