from mock import call
from nose.tools import istest

from provy.more.debian import AptitudeRole, SELinuxRole
from tests.unit.tools.helpers import ProvyTestCase


class SELinuxRoleTest(ProvyTestCase):
    def setUp(self):
        self.role = SELinuxRole(prov=None, context={'cleanup': []})

    def assert_packages_installed(self, aptitude):
        aptitude.ensure_package_installed.assert_any_call('selinux-basics')
        aptitude.ensure_package_installed.assert_any_call('selinux-policy-default')
        aptitude.ensure_package_installed.assert_any_call('selinux-utils')

    @istest
    def provisions_to_debian(self):
        with self.using_stub(AptitudeRole) as aptitude, self.execute_mock() as execute, self.provisioning_to('debian'):
            self.role.provision()

            self.assert_packages_installed(aptitude)
            expected_calls = [
                call('selinux-activate', stdout=False, sudo=True),
            ]
            self.assertEqual(execute.mock_calls, expected_calls)

    @istest
    def provisions_to_ubuntu(self):
        with self.using_stub(AptitudeRole) as aptitude, self.mock_role_method('put_file') as put_file, self.execute_mock() as execute, self.provisioning_to('ubuntu'):
            self.role.provision()

            self.assert_packages_installed(aptitude)
            put_file.assert_called_with(self.role.LOAD_SCRIPT, '/usr/share/initramfs-tools/scripts/init-bottom/_load_selinux_policy', sudo=True)
            expected_calls = [
                call('update-initramfs -u', stdout=False, sudo=True),
                call('selinux-activate', stdout=False, sudo=True),
            ]
            self.assertEqual(execute.mock_calls, expected_calls)
