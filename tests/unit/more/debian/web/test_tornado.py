from nose.tools import istest

from provy.more.debian import TornadoRole, AptitudeRole, PipRole
from tests.unit.tools.helpers import ProvyTestCase


class TornadoRoleTest(ProvyTestCase):
    def setUp(self):
        super(TornadoRoleTest, self).setUp()
        self.role = TornadoRole(prov=None, context={})

    @istest
    def installs_necessary_packages_to_provision(self):
        with self.using_stub(AptitudeRole) as aptitude, self.using_stub(PipRole) as pip:
            self.role.provision()

            aptitude.ensure_up_to_date.assert_called_once_with()
            aptitude.ensure_package_installed.assert_called_once_with('python-pycurl')
            pip.ensure_package_installed.assert_called_once_with('tornado')
