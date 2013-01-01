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

    @istest
    def puts_executables_to_audit_mode(self):
        with self.execute_mock() as execute:
            self.role.audit('/some/bin1', '/some/bin2')

            execute.assert_called_with('aa-audit /some/bin1 /some/bin2', stdout=False, sudo=True)

    @istest
    def creates_a_profile_for_an_executable(self):
        with self.execute_mock() as execute:
            self.role.create('/some/bin')

            execute.assert_called_with('aa-easyprof /some/bin', stdout=False, sudo=True)

    @istest
    def creates_a_profile_with_another_template(self):
        with self.execute_mock() as execute:
            self.role.create('/some/bin', template='another-template')

            execute.assert_called_with('aa-easyprof -t another-template /some/bin', stdout=False, sudo=True)

    @istest
    def creates_a_profile_with_policy_groups(self):
        with self.execute_mock() as execute:
            self.role.create('/some/bin', policy_groups=['networking', 'user-application'])

            execute.assert_called_with('aa-easyprof -p networking,user-application /some/bin', stdout=False, sudo=True)

    @istest
    def creates_a_profile_with_abstractions(self):
        with self.execute_mock() as execute:
            self.role.create('/some/bin', abstractions=['python', 'apache2-common'])

            execute.assert_called_with('aa-easyprof -a python,apache2-common /some/bin', stdout=False, sudo=True)

    @istest
    def creates_a_profile_with_read_permissions(self):
        with self.execute_mock() as execute:
            self.role.create('/some/bin', read=['/var/log/somebin.log', '/srv/somebin/'])

            execute.assert_called_with('aa-easyprof -r /var/log/somebin.log -r /srv/somebin/ /some/bin', stdout=False, sudo=True)

    @istest
    def creates_a_profile_with_read_and_write_permissions(self):
        with self.execute_mock() as execute:
            self.role.create('/some/bin', read_and_write=['/var/log/somebin.log', '/srv/somebin/'])

            execute.assert_called_with('aa-easyprof -w /var/log/somebin.log -w /srv/somebin/ /some/bin', stdout=False, sudo=True)
