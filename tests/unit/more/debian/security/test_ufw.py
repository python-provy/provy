from nose.tools import istest

from provy.more.debian import AptitudeRole, UFWRole
from tests.unit.tools.helpers import ProvyTestCase


class UFWRoleTest(ProvyTestCase):
    def setUp(self):
        self.role = UFWRole(prov=None, context={'cleanup': []})

    @istest
    def installs_necessary_packages_to_provision(self):
        with self.using_stub(AptitudeRole) as aptitude, self.execute_mock():
            self.role.provision()

            aptitude.ensure_package_installed.assert_any_call('ufw')

    @istest
    def allows_ssh_connection_during_provisioning(self):
        with self.using_stub(AptitudeRole), self.execute_mock() as execute:
            self.role.provision()

            execute.assert_any_call('ufw allow ssh', stdout=False, sudo=True)
