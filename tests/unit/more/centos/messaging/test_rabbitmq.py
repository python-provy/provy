from mock import patch, call, DEFAULT
from nose.tools import istest

from provy.more.centos import RabbitMqRole, YumRole
from tests.unit.tools.helpers import ProvyTestCase


class RabbitMqRoleTest(ProvyTestCase):
    def setUp(self):
        self.role = RabbitMqRole(prov=None, context={})

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
        with self.using_stub(YumRole), self.mock_role_methods('is_process_running', 'user_exists', 'execute'):
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
