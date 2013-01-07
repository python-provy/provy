from mock import call
from nose.tools import istest

from provy.more.debian import AptitudeRole, SELinuxRole
from tests.unit.tools.helpers import ProvyTestCase


class SELinuxRoleTest(ProvyTestCase):
    def setUp(self):
        self.role = SELinuxRole(prov=None, context={'cleanup': []})

    @istest
    def provisions_to_debian(self):
        with self.using_stub(AptitudeRole) as aptitude, self.execute_mock() as execute, self.provisioning_to('debian'):
            self.role.provision()

            expected_packages = [
                call('selinux-basics'),
                call('selinux-policy-default'),
                call('selinux-utils'),
                call('auditd'),
                call('audispd-plugins'),
            ]
            self.assertEqual(aptitude.ensure_package_installed.mock_calls, expected_packages)
            expected_calls = [
                call('selinux-activate', stdout=False, sudo=True),
            ]
            self.assertEqual(execute.mock_calls, expected_calls)

    @istest
    def provisions_to_ubuntu(self):
        with self.using_stub(AptitudeRole) as aptitude, self.execute_mock() as execute, self.provisioning_to('ubuntu'):
            self.role.provision()

            expected_packages = [
                call('selinux'),
                call('selinux-utils'),
                call('auditd'),
                call('audispd-plugins'),
            ]
            self.assertEqual(aptitude.ensure_package_installed.mock_calls, expected_packages)
            expected_calls = [
            ]
            self.assertEqual(execute.mock_calls, expected_calls)
