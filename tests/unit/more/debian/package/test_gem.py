from nose.tools import istest

from provy.more.debian import AptitudeRole, RubyRole
from provy.more.debian.package.gem import GemRole
from tests.unit.tools.helpers import ProvyTestCase


class GemRoleTest(ProvyTestCase):
    def setUp(self):
        super(GemRoleTest, self).setUp()
        self.role = GemRole(prov=None, context={})

    @istest
    def installs_necessary_packages_to_provision(self):
        with self.using_stub(AptitudeRole) as aptitude, self.mock_role_method('provision_role'):
            self.role.provision()

            self.role.provision_role.assert_called_once_with(RubyRole)
            aptitude.ensure_package_installed.assert_called_once_with('rubygems')

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
