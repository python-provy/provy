from nose.tools import istest

from provy.more.debian import AptitudeRole, AppArmorRole
from tests.unit.tools.helpers import ProvyTestCase


class AppArmorRoleTest(ProvyTestCase):
    def setUp(self):
        self.role = AppArmorRole(prov=None, context={'cleanup': []})

    @istest
    def installs_necessary_packages_to_provision(self):
        with self.using_stub(AptitudeRole) as aptitude, self.execute_mock():
            self.role.provision()

            aptitude.ensure_package_installed.assert_any_call('apparmor-profiles')
            aptitude.ensure_package_installed.assert_any_call('apparmor-utils')
