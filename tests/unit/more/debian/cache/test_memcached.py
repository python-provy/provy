from mock import call
from nose.tools import istest

from provy.more.debian import AptitudeRole, MemcachedRole
from tests.unit.tools.helpers import ProvyTestCase


class MemcachedRoleTest(ProvyTestCase):
    def setUp(self):
        super(MemcachedRoleTest, self).setUp()
        self.role = MemcachedRole(prov=None, context={'owner': 'some-owner'})

    @istest
    def installs_necessary_packages_to_provision(self):
        with self.using_stub(AptitudeRole) as aptitude, self.mock_role_method('register_template_loader'):
            self.role.provision()

            self.role.register_template_loader.assert_called_once_with('provy.more.debian.cache')
            self.assertEqual(aptitude.ensure_package_installed.mock_calls, [
                call('memcached'),
                call('libmemcached-dev'),
            ])

    @istest
    def ensures_configuration_with_defaults(self):
        with self.mock_role_methods('update_file', 'ensure_restart'):
            self.role.update_file.return_value = True

            self.role.ensure_conf()

            self.role.update_file.assert_called_once_with('memcached.conf.template', '/etc/memcached.conf', sudo=True, owner='some-owner',
                                                          options={
                                                              'host': '127.0.0.1',
                                                              'memory_in_mb': 64,
                                                              'verbose_level': 0,
                                                              'log_folder': '/var/log/memcached',
                                                              'simultaneous_connections': 1024,
                                                              'port': 11211,
                                                              'lock_down': False,
                                                              'user': 'nobody',
                                                              'maximize_core_file_limit': False,
                                                              'error_when_memory_exhausted': False
                                                          })
            self.role.ensure_restart.assert_called_once_with()

    @istest
    def ensures_configuration_with_custom_config(self):
        with self.mock_role_methods('update_file', 'ensure_restart'):
            self.role.update_file.return_value = True

            self.role.ensure_conf(owner='root',
                                  log_folder='/foo/bar',
                                  verbose_level=123,
                                  memory_in_mb=234,
                                  host='192.168.1.1',
                                  port=12345,
                                  user='somebody',
                                  simultaneous_connections=65432,
                                  lock_down=True,
                                  error_when_memory_exhausted=True,
                                  maximize_core_file_limit=True,
                                  conf_path='/bar/foo.conf')

            self.role.update_file.assert_called_once_with('memcached.conf.template', '/bar/foo.conf', sudo=True, owner='root',
                                                          options={
                                                              'host': '192.168.1.1',
                                                              'memory_in_mb': 234,
                                                              'verbose_level': 123,
                                                              'log_folder': '/foo/bar',
                                                              'simultaneous_connections': 65432,
                                                              'port': 12345,
                                                              'lock_down': True,
                                                              'user': 'somebody',
                                                              'maximize_core_file_limit': True,
                                                              'error_when_memory_exhausted': True,
                                                          })
            self.role.ensure_restart.assert_called_once_with()

    @istest
    def doesnt_restart_if_configuration_update_fails(self):
        with self.mock_role_methods('update_file', 'ensure_restart'):
            self.role.update_file.return_value = False

            self.role.ensure_conf()

            self.assertFalse(self.role.ensure_restart.called)

    @istest
    def doesnt_restart_if_not_necessary_upon_cleanup(self):
        with self.mock_role_method('restart'):
            self.role.cleanup()

            self.assertFalse(self.role.restart.called)

    @istest
    def restart_if_necessary_upon_cleanup(self):
        self.role.context['must-restart-memcached'] = True

        with self.mock_role_method('restart'):
            self.role.cleanup()

            self.assertTrue(self.role.restart.called)

    @istest
    def ensures_memcached_is_restarted(self):
        self.role.context['must-restart-memcached'] = False

        self.role.ensure_restart()

        self.assertTrue(self.role.context['must-restart-memcached'])

    @istest
    def restarts_memcached(self):
        with self.execute_mock():
            self.role.restart()

            self.role.execute.assert_called_once_with('/etc/init.d/memcached restart', sudo=True)
