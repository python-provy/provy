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
