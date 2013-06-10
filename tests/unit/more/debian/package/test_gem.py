from mock import call
from nose.tools import istest

from provy.more.debian import GemRole, RubyRole
from provy.more.debian.package.gem import UPDATE_ALTERNATIVES_COMMAND
from tests.unit.tools.helpers import ProvyTestCase


class GemRoleTest(ProvyTestCase):
    def setUp(self):
        super(GemRoleTest, self).setUp()
        self.role = GemRole(prov=None, context={})

    @istest
    def installs_necessary_packages_to_provision(self):
        with self.mock_role_method('provision_role'), self.execute_mock() as execute:
            self.role.provision()

            update_alternatives_command = UPDATE_ALTERNATIVES_COMMAND.format(
                version=RubyRole.version,
                priority=RubyRole.priority,
            )
            completion_command = 'ln - sf /etc/bash_completion.d/gem{version} /etc/alternatives/bash_completion_gem'.format(version=RubyRole.version)

            self.role.provision_role.assert_called_once_with(RubyRole)
            self.assertEqual(execute.mock_calls, [
                call(update_alternatives_command, sudo=True),
                call(completion_command, sudo=True),
            ])

    @istest
    def checks_that_a_package_is_installed(self):
        with self.execute_mock() as execute:
            execute.return_value = 'some foo is installed'

            result = self.role.is_package_installed('foo')

            self.assertTrue(result)
            execute.assert_called_once_with("gem list --local | tr '[A-Z]' '[a-z]' | grep foo", stdout=False, sudo=True)

    @istest
    def checks_that_a_package_is_not_installed(self):
        with self.execute_mock() as execute:
            execute.return_value = 'some bar is installed'

            result = self.role.is_package_installed('foo')

            self.assertFalse(result)

    @istest
    def checks_that_a_package_is_installed_with_version(self):
        with self.execute_mock() as execute:
            execute.return_value = 'some foo is installed'

            result = self.role.is_package_installed('foo', '1.8')

            self.assertTrue(result)
            execute.assert_called_once_with("gem list --local | tr '[A-Z]' '[a-z]' | grep foo(1.8)", stdout=False, sudo=True)

    @istest
    def installs_a_package_if_its_not_installed_yet_by_name(self):
        with self.execute_mock() as execute, self.mock_role_method('is_package_installed') as is_package_installed:
            is_package_installed.return_value = False

            result = self.role.ensure_package_installed('runit')

            self.assertTrue(result)
            execute.assert_called_with('gem install runit', stdout=False, sudo=True)

    @istest
    def doesnt_install_a_package_if_its_already_installed_yet_by_name(self):
        with self.execute_mock() as execute, self.mock_role_method('is_package_installed') as is_package_installed:
            is_package_installed.return_value = True

            result = self.role.ensure_package_installed('runit')

            self.assertFalse(result)
            self.assertFalse(execute.called)

    @istest
    def installs_a_package_if_its_not_installed_yet_by_name_and_version(self):
        with self.execute_mock() as execute, self.mock_role_method('is_package_installed') as is_package_installed:
            is_package_installed.return_value = False

            self.role.ensure_package_installed('runit', '123')

            execute.assert_called_with('gem install runit(123)', sudo=True, stdout=False)
