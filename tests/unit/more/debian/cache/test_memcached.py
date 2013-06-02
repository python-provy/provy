from mock import call
from nose.tools import istest

from provy.more.debian import AptitudeRole, MemcachedRole
from tests.unit.tools.helpers import ProvyTestCase


class MemcachedRoleTest(ProvyTestCase):
    def setUp(self):
        super(MemcachedRoleTest, self).setUp()
        self.role = MemcachedRole(prov=None, context={})

    @istest
    def installs_necessary_packages_to_provision(self):
        with self.using_stub(AptitudeRole) as aptitude, self.mock_role_method('register_template_loader'):
            self.role.provision()

            self.role.register_template_loader.assert_called_once_with('provy.more.debian.cache')
            self.assertEqual(aptitude.ensure_package_installed.mock_calls, [
                call('memcached'),
                call('libmemcached-dev'),
            ])
