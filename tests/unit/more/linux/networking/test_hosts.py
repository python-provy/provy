from nose.tools import istest

from provy.more.linux.networking.hosts import HostsRole
from tests.unit.tools.helpers import ProvyTestCase


class HostsRoleTest(ProvyTestCase):
    def setUp(self):
        super(HostsRoleTest, self).setUp()
        self.role = HostsRole(prov=None, context={})

    @istest
    def ensures_a_host_line_exists_in_the_hosts_file(self):
        with self.mock_role_method('ensure_line') as ensure_line:
            self.role.ensure_host('my-server', '0.0.0.0')

            ensure_line.assert_called_once_with('0.0.0.0        my-server', '/etc/hosts', sudo=True)
