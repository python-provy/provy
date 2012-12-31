from mock import call
from nose.tools import istest

from provy.more.debian import AptitudeRole, IPTablesRole
from tests.unit.tools.helpers import ProvyTestCase


class IPTablesRoleTest(ProvyTestCase):
    def setUp(self):
        self.role = IPTablesRole(prov=None, context={'cleanup': []})

    @istest
    def installs_necessary_packages_to_provision(self):
        with self.using_stub(AptitudeRole) as aptitude, self.execute_mock():
            self.role.provision()

            aptitude.ensure_package_installed.assert_any_call('iptables')

    @istest
    def allows_ssh_connection_during_provisioning(self):
        with self.using_stub(AptitudeRole), self.execute_mock() as execute:
            self.role.provision()

            execute.assert_any_call('iptables -A INPUT -j ACCEPT -p tcp --dport ssh', stdout=False, sudo=True)

    @istest
    def lists_all_available_chains_and_rules(self):
        with self.execute_mock() as execute:
            execute.return_value = "some rules"

            result = self.role.list_rules()

            execute.assert_called_with('iptables -L', stdout=True, sudo=True)
            self.assertEqual(result, "some rules")

    @istest
    def lists_all_available_chains_and_rules_with_commands(self):
        with self.execute_mock() as execute:
            execute.return_value = "some rules"

            result = self.role.list_rules_with_commands()

            execute.assert_called_with('iptables-save', stdout=True, sudo=True)
            self.assertEqual(result, "some rules")

    @istest
    def saves_configurations_when_finishing_provisioning(self):
        with self.execute_mock() as execute:
            self.role.schedule_cleanup()

            execute.assert_any_call("iptables-save > /etc/iptables.rules", stdout=False, sudo=True)

    @istest
    def blocks_all_other_ports_when_finishing_provisioning(self):
        with self.execute_mock() as execute:
            self.role.schedule_cleanup()

            execute.assert_any_call("iptables -A INPUT -j REJECT -p all", stdout=False, sudo=True)

    @istest
    def leaves_others_unblocked_when_finishing_provisioning_if_desired(self):
        with self.execute_mock() as execute:
            self.role.block_on_finish = False
            self.role.schedule_cleanup()

            call_to_avoid = call("iptables -A INPUT -j REJECT -p all", stdout=False, sudo=True)
            self.assertNotIn(call_to_avoid, execute.mock_calls)

    @istest
    def allows_incoming_tcp_in_all_ports(self):
        with self.execute_mock() as execute:
            self.role.allow()

            execute.assert_called_with('iptables -A INPUT -j ACCEPT -p tcp', stdout=False, sudo=True)

    @istest
    def allows_incoming_tcp_in_a_specific_port(self):
        with self.execute_mock() as execute:
            self.role.allow(port=80)

            execute.assert_called_with('iptables -A INPUT -j ACCEPT -p tcp --dport 80', stdout=False, sudo=True)

    @istest
    def allows_incoming_tcp_in_a_specific_port_by_name(self):
        with self.execute_mock() as execute:
            self.role.allow(port='ssh')

            execute.assert_called_with('iptables -A INPUT -j ACCEPT -p tcp --dport ssh', stdout=False, sudo=True)

    @istest
    def allows_incoming_tcp_in_a_specific_interface(self):
        with self.execute_mock() as execute:
            self.role.allow(interface='eth0')

            execute.assert_called_with('iptables -A INPUT -j ACCEPT -p tcp -i eth0', stdout=False, sudo=True)

    @istest
    def allows_outgoing_tcp_in_all_ports(self):
        with self.execute_mock() as execute:
            self.role.allow(direction="out")

            execute.assert_called_with('iptables -A OUTPUT -j ACCEPT -p tcp', stdout=False, sudo=True)

    @istest
    def allows_forward_tcp_in_all_ports(self):
        with self.execute_mock() as execute:
            self.role.allow(direction="forward")

            execute.assert_called_with('iptables -A FORWARD -j ACCEPT -p tcp', stdout=False, sudo=True)

    @istest
    def allows_incoming_udp_in_all_ports(self):
        with self.execute_mock() as execute:
            self.role.allow(protocol="udp")

            execute.assert_called_with('iptables -A INPUT -j ACCEPT -p udp', stdout=False, sudo=True)

    @istest
    def allows_incoming_tcp_in_all_ports_with_a_match_filter(self):
        with self.execute_mock() as execute:
            self.role.allow(match="state", state="ESTABLISHED,RELATED")

            execute.assert_called_with('iptables -A INPUT -j ACCEPT -p tcp -m state --state ESTABLISHED,RELATED', stdout=False, sudo=True)

    @istest
    def rejects_incoming_connections_in_all_ports_and_protocols(self):
        with self.execute_mock() as execute:
            self.role.reject()

            execute.assert_called_with('iptables -A INPUT -j REJECT -p all', stdout=False, sudo=True)

    @istest
    def rejects_tcp_connections_in_all_ports(self):
        with self.execute_mock() as execute:
            self.role.reject(protocol="tcp")

            execute.assert_called_with('iptables -A INPUT -j REJECT -p tcp', stdout=False, sudo=True)

    @istest
    def rejects_tcp_connections_in_a_specific_port(self):
        with self.execute_mock() as execute:
            self.role.reject(port=80, protocol="tcp")

            execute.assert_called_with('iptables -A INPUT -j REJECT -p tcp --dport 80', stdout=False, sudo=True)

    @istest
    def rejects_outgoing_connections(self):
        with self.execute_mock() as execute:
            self.role.reject(direction="out")

            execute.assert_called_with('iptables -A OUTPUT -j REJECT -p all', stdout=False, sudo=True)

    @istest
    def rejects_incoming_connections_in_all_ports_with_a_match_filter(self):
        with self.execute_mock() as execute:
            self.role.reject(match="state", state="ESTABLISHED,RELATED")

            execute.assert_called_with('iptables -A INPUT -j REJECT -p all -m state --state ESTABLISHED,RELATED', stdout=False, sudo=True)

    @istest
    def drops_incoming_connections_in_all_ports_and_protocols(self):
        with self.execute_mock() as execute:
            self.role.drop()

            execute.assert_called_with('iptables -A INPUT -j DROP -p all', stdout=False, sudo=True)

    @istest
    def drops_tcp_connections_in_a_specific_port(self):
        with self.execute_mock() as execute:
            self.role.drop(port=80, protocol="tcp")

            execute.assert_called_with('iptables -A INPUT -j DROP -p tcp --dport 80', stdout=False, sudo=True)
