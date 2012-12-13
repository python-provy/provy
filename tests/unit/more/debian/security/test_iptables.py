from contextlib import contextmanager

from mock import MagicMock, patch, call
from nose.tools import istest

from provy.more.debian import AptitudeRole, IPTablesRole
from tests.unit.tools.helpers import ProvyTestCase


class IPTablesRoleTest(ProvyTestCase):
    def setUp(self):
        self.role = IPTablesRole(prov=None, context={})

    @istest
    def installs_necessary_packages_to_provision(self):
        with self.using_stub(AptitudeRole) as aptitude, self.execute_mock() as execute:
            self.role.provision()

            aptitude.ensure_package_installed.assert_any_call('iptables')

    @istest
    def allows_ssh_connection_during_provisioning(self):
        with self.using_stub(AptitudeRole) as aptitude, self.execute_mock() as execute:
            self.role.provision()

            execute.assert_any_call('iptables -A INPUT -p tcp -m tcp --dport 22 -j ACCEPT', stdout=False, sudo=True)

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
