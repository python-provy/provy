from mock import call, patch
from nose.tools import istest

from provy.more.centos import RabbitMqRole, YumRole
from provy.more.centos.messaging.rabbitmq import GUEST_USER_WARNING
from tests.unit.tools.helpers import ProvyTestCase


class RabbitMqRoleTest(ProvyTestCase):
    def setUp(self):
        super(RabbitMqRoleTest, self).setUp()
        self.role = RabbitMqRole(prov=None, context={})

    def output_list_vhosts(self, vhosts):
        all_strings = ['Listing vhosts ...'] + vhosts + ['...done.']
        return '\r\n'.join(all_strings)

    @istest
    def checks_that_a_user_exists(self):
        with self.execute_mock() as execute:
            execute.return_value = ['john', 'jack']

            result = self.role.user_exists('john')

            self.assertTrue(result)
            execute.assert_called_with('rabbitmqctl list_users', sudo=True, stdout=False)

    @istest
    def checks_that_a_user_doesnt_exist(self):
        with self.execute_mock() as execute:
            execute.return_value = ['john', 'jack']

            result = self.role.user_exists('brian')

            self.assertFalse(result)
            execute.assert_called_with('rabbitmqctl list_users', sudo=True, stdout=False)

    @istest
    def installs_necessary_packages_to_provision(self, **mocks):
        with self.using_stub(YumRole) as mock_yum, self.mock_role_methods('is_process_running', 'user_exists', 'execute'):
            self.role.is_process_running.return_value = True
            self.role.user_exists.return_value = False

            self.role.provision()

            mock_yum.ensure_up_to_date.assert_called_with()
            mock_yum.ensure_package_installed.assert_called_with('rabbitmq-server')

    @istest
    def executes_the_correct_commands_to_provision(self, **mocks):
        with self.using_stub(YumRole), self.mock_role_methods('is_process_running', 'user_exists', 'execute'):
            self.role.is_process_running.return_value = False
            self.role.user_exists.return_value = False

            self.role.provision()

            self.assertEqual(self.role.execute.mock_calls, [
                call('chkconfig --add rabbitmq-server', stdout=False, sudo=True),
                call('chkconfig rabbitmq-server on', stdout=False, sudo=True),
                call('service rabbitmq-server start', stdout=False, sudo=True),
            ])

    @istest
    def doesnt_start_rabbit_if_already_started_during_provisioning(self, **mocks):
        with self.using_stub(YumRole), self.mock_role_methods('is_process_running', 'user_exists', 'execute'):
            self.role.is_process_running.return_value = True
            self.role.user_exists.return_value = False

            self.role.provision()

            self.assertEqual(self.role.execute.mock_calls, [
                call('chkconfig --add rabbitmq-server', stdout=False, sudo=True),
                call('chkconfig rabbitmq-server on', stdout=False, sudo=True),
            ])

    @istest
    def warns_about_guest_user(self, **mocks):
        with self.using_stub(YumRole), self.mock_role_methods('is_process_running', 'user_exists', 'execute'), patch('provy.more.centos.messaging.rabbitmq.warn') as warn:
            self.role.is_process_running.return_value = True
            self.role.user_exists.return_value = True

            self.role.provision()

            warn.assert_called_once_with(GUEST_USER_WARNING)

    @istest
    def checks_that_a_vhost_exists(self):
        with self.execute_mock() as execute:
            execute.return_value = self.output_list_vhosts([
                'foo',
                'bar',
            ])

            self.assertTrue(self.role.vhost_exists('foo'))
            execute.assert_called_once_with('rabbitmqctl list_vhosts', stdout=False, sudo=True)

    @istest
    def checks_that_a_vhost_doesnt_exist(self):
        with self.execute_mock() as execute:
            execute.return_value = self.output_list_vhosts([
                'foo',
                'bar',
            ])

            self.assertFalse(self.role.vhost_exists('baz'))
            execute.assert_called_once_with('rabbitmqctl list_vhosts', stdout=False, sudo=True)

    @istest
    def ensures_user_is_created_if_it_doesnt_exist_yet(self):
        with self.mock_role_methods('user_exists', 'execute'):
            self.role.user_exists.return_value = False

            result = self.role.ensure_user('foo-user', 'foo-pass')

            self.assertTrue(result)
            self.role.user_exists.assert_called_once_with('foo-user')
            self.role.execute.assert_called_once_with('rabbitmqctl add_user foo-user foo-pass', sudo=True)

    @istest
    def doesnt_create_user_if_it_already_exists(self):
        with self.mock_role_methods('user_exists', 'execute'):
            self.role.user_exists.return_value = True

            result = self.role.ensure_user('foo-user', 'foo-pass')

            self.assertFalse(result)
            self.role.user_exists.assert_called_once_with('foo-user')
            self.assertFalse(self.role.execute.called)
