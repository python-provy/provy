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

    @istest
    def enables_when_finishing_provisioning(self):
        with self.execute_mock() as execute:
            self.role.schedule_cleanup()

            execute.assert_any_call("ufw --force enable", stdout=False, sudo=True)

    @istest
    def allows_a_certain_port_by_application_name(self):
        with self.execute_mock() as execute:
            self.role.allow('http')

            execute.assert_called_with('ufw allow http', stdout=False, sudo=True)

    @istest
    def allows_a_certain_port_by_number(self):
        with self.execute_mock() as execute:
            self.role.allow(8000)

            execute.assert_called_with('ufw allow 8000', stdout=False, sudo=True)

    @istest
    def allows_a_certain_port_by_number_and_protocol(self):
        with self.execute_mock() as execute:
            self.role.allow(8000, protocol='tcp')

            execute.assert_called_with('ufw allow 8000/tcp', stdout=False, sudo=True)

    @istest
    def allows_a_certain_port_by_number_and_direction(self):
        with self.execute_mock() as execute:
            self.role.allow(8000, direction='in')

            execute.assert_called_with('ufw allow in 8000', stdout=False, sudo=True)

    @istest
    def allows_a_certain_port_by_number_and_protocol_and_direction(self):
        with self.execute_mock() as execute:
            self.role.allow(8000, protocol='tcp', direction='in')

            execute.assert_called_with('ufw allow in 8000/tcp', stdout=False, sudo=True)

    @istest
    def drops_a_certain_port_by_number_and_protocol_and_direction(self):
        with self.execute_mock() as execute:
            self.role.drop(8000, protocol='tcp', direction='in')

            execute.assert_called_with('ufw deny in 8000/tcp', stdout=False, sudo=True)

    @istest
    def rejects_a_certain_port_by_number_and_protocol_and_direction(self):
        with self.execute_mock() as execute:
            self.role.reject(8000, protocol='tcp', direction='in')

            execute.assert_called_with('ufw reject in 8000/tcp', stdout=False, sudo=True)

    @istest
    def allows_with_a_custom_query(self):
        with self.execute_mock() as execute:
            self.role.allow('proto tcp to any port 80')

            execute.assert_called_with('ufw allow proto tcp to any port 80', stdout=False, sudo=True)
