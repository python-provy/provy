from contextlib import contextmanager
from unittest import TestCase

from mock import MagicMock, patch, call, ANY
from nose.tools import istest

from provy.more.debian import AptitudeRole, PipRole, SupervisorRole


class SupervisorRoleTest(TestCase):
    def setUp(self):
        self.role = SupervisorRole(prov=None, context={})

    @istest
    def installs_necessary_packages_to_provision(self):
        mock_pip = MagicMock(spec=PipRole)

        @contextmanager
        def stub_using(self, klass):
            yield mock_pip

        with patch('provy.core.roles.Role.using', stub_using), patch('provy.core.roles.Role.register_template_loader'):
            self.role.provision()

            mock_pip.ensure_package_installed.assert_called_with('supervisor')

    @istest
    def forces_as_sudo_to_install(self):
        mock_pip = MagicMock(spec=PipRole)

        @contextmanager
        def stub_using(self, klass):
            yield mock_pip

        with patch('provy.core.roles.Role.using', stub_using), patch('provy.core.roles.Role.register_template_loader'):
            mock_pip.use_sudo = False
            mock_pip.user = 'johndoe'
            self.role.provision()

            self.assertTrue(mock_pip.use_sudo)
            self.assertIsNone(mock_pip.user)
