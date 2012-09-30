from contextlib import contextmanager

from mock import MagicMock, patch, call
from nose.tools import istest

from provy.core.roles import DistroInfo
from provy.more.debian import ApacheRole, AptitudeRole
from tests.unit.tools.helpers import ProvyTestCase


class ApacheRoleTest(ProvyTestCase):
    def setUp(self):
        self.role = ApacheRole(prov=None, context={})

    @istest
    def installs_necessary_packages_to_provision(self):
        with self.using_stub(AptitudeRole) as aptitude:
            self.role.provision()

            aptitude.ensure_package_installed.assert_called_with('apache2')
