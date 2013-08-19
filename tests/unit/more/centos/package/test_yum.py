from nose.tools import istest

from provy.more.centos import YumRole
from tests.unit.tools.helpers import ProvyTestCase


class YumRoleTest(ProvyTestCase):
    def setUp(self):
        super(YumRoleTest, self).setUp()
        self.role = YumRole(prov=None, context={})

    @istest
    def installs_necessary_packages_to_provision(self):
        with self.mock_role_methods('ensure_up_to_date', 'ensure_package_installed'):
            self.role.provision()

            self.role.ensure_up_to_date.assert_called_once_with()
            self.role.ensure_package_installed.assert_called_once_with('curl')

    @istest
    def ensures_gpg_key_is_added(self):
        with self.execute_mock():
            self.role.ensure_gpg_key('http://some.repo')

            self.role.execute.assert_called_once_with('curl http://some.repo | rpm --import -', sudo=True, stdout=False)
