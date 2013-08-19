from nose.tools import istest

from provy.more.centos import YumRole
from tests.unit.tools.helpers import ProvyTestCase


class YumRoleTest(ProvyTestCase):
    def setUp(self):
        super(YumRoleTest, self).setUp()
        self.role = YumRole(prov=None, context={})

    @istest
    def installs_necessary_packages_to_provision(self):
        with self.mock_role_methods('ensure_up_to_date', 'ensure_package_installed'):
            self.role.provision()

            self.role.ensure_up_to_date.assert_called_once_with()
            self.role.ensure_package_installed.assert_called_once_with('curl')

    @istest
    def ensures_gpg_key_is_added(self):
        with self.execute_mock():
            self.role.ensure_gpg_key('http://some.repo')

            self.role.execute.assert_called_once_with('curl http://some.repo | rpm --import -', sudo=True, stdout=False)

    @istest
    def checks_that_repository_exists_in_yum_repos(self):
        with self.execute_mock() as execute:
            execute.return_value = '''
            some
            repo
            foo-bar
            '''

            result = self.role.has_source('foo-bar')

            self.assertTrue(result)
            execute.assert_called_once_with("cat /etc/yum.repos.d/CentOS-Base.repo", sudo=True, stdout=False)

    @istest
    def checks_that_repository_doesnt_exist_in_apt_source(self):
        with self.execute_mock() as execute:
            execute.return_value = 'some repo'

            result = self.role.has_source('foo-bar')

            self.assertFalse(result)

    @istest
    def ensures_a_source_string_is_added_to_the_repos(self):
        source_line = 'foo-bar-repo'
        with self.execute_mock() as execute, self.mock_role_method('has_source') as has_source:
            has_source.return_value = False

            self.assertTrue(self.role.ensure_yum_source(source_line))

            self.assertTrue(has_source.called)
            execute.assert_called_once_with('echo "{}" >> /etc/yum.repos.d/CentOS-Base.repo'.format(source_line), sudo=True, stdout=False)

    @istest
    def doesnt_add_source_if_it_already_exists(self):
        source_line = 'foo-bar-repo'
        with self.execute_mock() as execute, self.mock_role_method('has_source') as has_source:
            has_source.return_value = True

            self.assertFalse(self.role.ensure_yum_source(source_line))

            self.assertFalse(execute.called)
