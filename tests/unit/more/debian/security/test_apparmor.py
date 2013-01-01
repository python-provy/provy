from mock import call
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

    @istest
    def enables_a_certain_profile(self):
        with self.execute_mock() as execute:
            self.role.enable('some.profile')

            self.assertEqual(execute.mock_calls, [
                call('rm -f /etc/apparmor.d/disable/some.profile', stdout=False, sudo=True),
                call('apparmor_parser -r /etc/apparmor.d/some.profile', stdout=False, sudo=True),
            ])

    @istest
    def disables_executables(self):
        with self.execute_mock() as execute:
            self.role.disable('/some/bin1', '/some/bin2')

            execute.assert_called_with('aa-disable /some/bin1 /some/bin2', stdout=False, sudo=True)

    @istest
    def puts_executables_to_complain_mode(self):
        with self.execute_mock() as execute:
            self.role.complain('/some/bin1', '/some/bin2')

            execute.assert_called_with('aa-complain /some/bin1 /some/bin2', stdout=False, sudo=True)

    @istest
    def puts_executables_to_enforce_mode(self):
        with self.execute_mock() as execute:
            self.role.enforce('/some/bin1', '/some/bin2')

            execute.assert_called_with('aa-enforce /some/bin1 /some/bin2', stdout=False, sudo=True)
