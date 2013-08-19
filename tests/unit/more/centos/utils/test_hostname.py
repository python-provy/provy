from mock import patch, call
from nose.tools import istest

from provy.more.centos import HostNameRole
from provy.more.centos.utils import hostname
from tests.unit.tools.helpers import ProvyTestCase


class HostNameRoleTest(ProvyTestCase):
    def setUp(self):
        super(HostNameRoleTest, self).setUp()
        self.role = HostNameRole(None, {})

    @istest
    def ensures_a_hostname_is_configured_when_not_existing(self):
        new_hostname = 'new-hostname'
        with self.mock_role_methods('read_remote_file', 'execute', 'ensure_line'), patch.object(hostname, 'sed') as sed:
            self.role.execute.return_value = 'previous-hostname'
            self.role.read_remote_file.return_value = '''
            some config
            HOSTNAME={}
            some other config
            '''.format(new_hostname)

            result = self.role.ensure_hostname(new_hostname)

            self.assertTrue(result)
            self.role.read_remote_file.assert_called_once_with('/etc/sysconfig/network')
            self.assertEqual(self.role.execute.mock_calls, [
                call('hostname'),
                call('hostname "{}"'.format(new_hostname), sudo=True, stdout=False),
            ])
            self.assertFalse(self.role.ensure_line.called)
            sed.assert_called_once_with('/etc/sysconfig/network', 'HOSTNAME=.*', 'HOSTNAME=new-hostname', use_sudo=True)

    @istest
    def ensures_a_hostname_is_configured_when_another_one_already_exists(self):
        new_hostname = 'new-hostname'
        with self.mock_role_methods('read_remote_file', 'execute', 'ensure_line'), patch.object(hostname, 'sed') as sed:
            self.role.execute.return_value = 'previous-hostname'
            self.role.read_remote_file.return_value = '''
            some config
            some other config
            '''.format(new_hostname)

            result = self.role.ensure_hostname(new_hostname)

            self.assertTrue(result)
            self.role.read_remote_file.assert_called_once_with('/etc/sysconfig/network')
            self.assertEqual(self.role.execute.mock_calls, [
                call('hostname'),
                call('hostname "{}"'.format(new_hostname), sudo=True, stdout=False),
            ])
            self.assertFalse(sed.called)
            self.role.ensure_line.assert_called_once_with('HOSTNAME={}'.format(new_hostname), sudo=True, stdout=False)

    @istest
    def doesnt_configure_the_hostname_if_same_as_server(self):
        new_hostname = 'new-hostname'
        with self.mock_role_methods('execute'):
            self.role.execute.return_value = new_hostname

            result = self.role.ensure_hostname(new_hostname)

            self.assertFalse(result)
            self.assertEqual(self.role.execute.mock_calls, [
                call('hostname'),
            ])
