from mock import call, DEFAULT, patch
from nose.tools import istest

from provy.more.debian import AptitudeRole, SELinuxRole
from tests.unit.tools.helpers import ProvyTestCase


class SELinuxRoleTest(ProvyTestCase):
    def setUp(self):
        self.role = SELinuxRole(prov=None, context={'cleanup': []})

    @istest
    def provisions_correctly(self):
        with patch.multiple(self.role, install_packages=DEFAULT, activate=DEFAULT):
            self.role.provision()

            self.role.install_packages.assert_called_with()
            self.role.activate.assert_called_with()

    @istest
    def installs_packages_in_debian(self):
        with self.using_stub(AptitudeRole) as aptitude, self.provisioning_to('debian'):
            self.role.install_packages()

            expected_packages = [
                call('selinux-basics'),
                call('selinux-policy-default'),
                call('selinux-utils'),
                call('auditd'),
                call('audispd-plugins'),
            ]
            self.assertEqual(aptitude.ensure_package_installed.mock_calls, expected_packages)

    @istest
    def installs_packages_in_ubuntu(self):
        with self.using_stub(AptitudeRole) as aptitude, self.provisioning_to('ubuntu'):
            self.role.install_packages()

            expected_packages = [
                call('selinux'),
                call('selinux-utils'),
                call('auditd'),
                call('audispd-plugins'),
            ]
            self.assertEqual(aptitude.ensure_package_installed.mock_calls, expected_packages)

    @istest
    def activates_on_debian(self):
        with self.execute_mock() as execute, self.provisioning_to('debian'):
            self.role.activate()

            expected_calls = [
                call('selinux-activate', stdout=False, sudo=True),
            ]
            self.assertEqual(execute.mock_calls, expected_calls)

    @istest
    def activates_on_ubuntu(self):
        with self.execute_mock() as execute, self.provisioning_to('ubuntu'):
            self.role.activate()

            expected_calls = [
            ]
            self.assertEqual(execute.mock_calls, expected_calls)
