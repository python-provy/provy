import os

from nose.tools import istest
from mock import call
from jinja2 import FileSystemLoader

from provy.more.debian import SSHRole
from tests.unit.tools.helpers import ProvyTestCase, PROJECT_ROOT


class SSHRoleTest(ProvyTestCase):
    def setUp(self):
        super(SSHRoleTest, self).setUp()
        self.role = SSHRole(None, {})

        template_dir = os.path.join(PROJECT_ROOT, 'tests', 'unit', 'fixtures')
        self.role.context['loader'] = FileSystemLoader(template_dir)

        self.test_pub_key = open(os.path.join(template_dir, 'test_public_key')).read()
        self.test_private_key = self.role.render('test_private_key.pem')

    @istest
    def ensures_ssh_key(self):
        with self.mock_role_methods('_SSHRole__write_keys', 'ensure_dir') as (mock_write, ensure_dir):
            self.role.ensure_ssh_key('user', 'test_private_key.pem')

            ensure_dir.assert_called_with(
                '/home/user/.ssh', owner='user', sudo=True,
            )
            mock_write.assert_called_with(
                'user', self.test_private_key, self.test_pub_key,
            )

    @istest
    def writes_keys(self):
        with self.mock_role_methods('execute_python', 'write_to_temp_file', 'update_file') as (execute_python, write_to_temp_file, update_file):
            self.role._SSHRole__write_keys('user', '..private..', '..public..')

            self.assertEqual(
                execute_python.call_args,
                call('import os; print os.uname()[1]', stdout=False)
            )

            write_to_temp_file.assert_has_calls([
                call('..public.. user@' + str(execute_python.return_value)),
                call('..private..'),
            ])

            update_file.assert_has_calls([
                call(
                    write_to_temp_file.return_value,
                    '/home/user/.ssh/id_rsa.pub', sudo=True, owner='user',
                ),
                call(
                    write_to_temp_file.return_value,
                    '/home/user/.ssh/id_rsa', sudo=True, owner='user',
                ),
            ])

    @istest
    def doesnt_log_if_updating_keys_files_fails(self):
        with self.mock_role_methods('execute_python', 'write_to_temp_file', 'update_file', 'log') as (execute_python, write_to_temp_file, update_file, log):
            update_file.return_value = False

            self.role._SSHRole__write_keys('user', '..private..', '..public..')

            self.assertFalse(log.called)
