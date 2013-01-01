from nose.tools import istest

from provy.more.debian import AptitudeRole, SELinuxRole
from tests.unit.tools.helpers import ProvyTestCase


class SELinuxRoleTest(ProvyTestCase):
    def setUp(self):
        self.role = SELinuxRole(prov=None, context={'cleanup': []})

    @istest
    def installs_necessary_packages_to_provision(self):
        with self.using_stub(AptitudeRole) as aptitude, self.execute_mock():
            self.role.provision()

            aptitude.ensure_package_installed.assert_any_call('selinux-basics')
            aptitude.ensure_package_installed.assert_any_call('selinux-policy-default')
            aptitude.ensure_package_installed.assert_any_call('selinux-utils')
