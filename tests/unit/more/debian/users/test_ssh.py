import os

from nose.tools import istest
from mock import patch, call, DEFAULT
from jinja2 import FileSystemLoader

from provy.more.debian import SSHRole
from tests.unit.tools.helpers import ProvyTestCase, PROJECT_ROOT


class SSHRoleTest(ProvyTestCase):
    def setUp(self):
        self.role = SSHRole(None, {})

        template_dir = os.path.join(PROJECT_ROOT, 'tests', 'unit', 'fixtures')
        self.role.context['loader'] = FileSystemLoader(template_dir)

        self.test_pub_key = open(os.path.join(template_dir, 'test_public_key')).read()
        self.test_private_key = self.role.render('test_private_key.pem')

    @istest
    @patch('provy.core.Role.ensure_dir')
    def ensure_ssh_key(self, mock_ensure_dir):
        with patch('provy.more.debian.SSHRole._SSHRole__write_keys') as mock_write:
            self.role.ensure_ssh_key('user', 'test_private_key.pem')

            self.assertEqual(
                mock_ensure_dir.call_args,
                call('/home/user/.ssh', owner='user', sudo=True),
            )
            self.assertEqual(
                mock_write.call_args,
                call('user', self.test_private_key, self.test_pub_key),
            )

    @istest
    @patch.multiple(
        'provy.core.Role', execute_python=DEFAULT, write_to_temp_file=DEFAULT,
        update_file=DEFAULT,
    )
    def write_keys(self, execute_python, write_to_temp_file,
                   update_file):
        self.role._SSHRole__write_keys('user', '..private..', '..public..')

        self.assertEqual(
            execute_python.call_args,
            call('import os; print os.uname()[1]', stdout=False)
        )

        self.assertEqual(
            write_to_temp_file.call_args_list,
            [
                call('..public.. user@' + str(execute_python.return_value)),
                call('..private..'),
            ]
        )

        self.assertEqual(
            update_file.call_args_list,
            [call(write_to_temp_file.return_value, '/home/user/.ssh/id_rsa.pub', sudo=True, owner='user'),
             call(write_to_temp_file.return_value, '/home/user/.ssh/id_rsa', sudo=True, owner='user')]
        )
