from contextlib import contextmanager

from mock import MagicMock, patch, call, ANY
from nose.tools import istest

from provy.more.debian import AptitudeRole, PipRole, SupervisorRole
from tests.unit.tools.helpers import ProvyTestCase


class SupervisorRoleTest(ProvyTestCase):
    def setUp(self):
        self.role = SupervisorRole(prov=None, context={})

    @istest
    def installs_necessary_packages_to_provision(self):
        with self.using_stub(PipRole) as mock_pip, patch('provy.core.roles.Role.register_template_loader'):
            self.role.provision()

            mock_pip.ensure_package_installed.assert_called_with('supervisor')

    @istest
    def forces_as_sudo_to_install(self):
        with self.using_stub(PipRole) as mock_pip, patch('provy.core.roles.Role.register_template_loader'):
            self.role.provision()
            self.assertTrue(mock_pip.set_sudo.called)
