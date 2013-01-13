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
        with self.execute_mock() as execute, self.provisioning_to('debian'), patch.object(self.role, 'enforce'):
            self.role.activate()

            expected_calls = [
                call('selinux-activate', stdout=False, sudo=True),
                call("semanage login -m -s 'user_u' -r s0 __default__", stdout=False, sudo=True),
            ]
            self.assertEqual(execute.mock_calls, expected_calls)
            self.role.enforce.assert_called_with()

    @istest
    def activates_on_ubuntu(self):
        with self.execute_mock() as execute, self.provisioning_to('ubuntu'), patch.object(self.role, 'enforce'):
            self.role.activate()

            expected_calls = [
                call("semanage login -m -s 'user_u' -r s0 __default__", stdout=False, sudo=True),
            ]
            self.assertEqual(execute.mock_calls, expected_calls)
            self.role.enforce.assert_called_with()

    @istest
    def puts_environment_in_enforce_mode(self):
        with self.execute_mock(), self.mock_role_method('ensure_line'), self.warn_only():
            self.role.enforce()

            self.role.execute.assert_called_with('setenforce 1', stdout=False, sudo=True)
            self.role.ensure_line.assert_called_with('SELINUX=enforcing', '/etc/selinux/config', sudo=True)

    @istest
    def ensures_that_a_login_mapping_exists(self):
        with self.execute_mock() as execute, self.warn_only():
            self.role.ensure_login_mapping('foo')

            execute.assert_called_with('semanage login -a foo', stdout=False, sudo=True)

    @istest
    def maps_a_login_user_to_an_selinux_user(self):
        with self.execute_mock() as execute, patch.object(self.role, 'ensure_login_mapping'):
            self.role.map_login('foo', 'staff_u')

            self.role.ensure_login_mapping.assert_called_with('foo')
            execute.assert_called_with('semanage login -m -s staff_u foo', stdout=False, sudo=True)

    @istest
    def maps_a_login_user_to_selinux_roles(self):
        with self.execute_mock() as execute, patch.object(self.role, 'ensure_login_mapping'):
            self.role.map_role('foo', ['staff_r', 'sysadm_r'])

            self.role.ensure_login_mapping.assert_called_with('foo')
            execute.assert_called_with("semanage user -m -R 'staff_r sysadm_r' foo", stdout=False, sudo=True)
