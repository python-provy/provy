from mock import patch
from nose.tools import istest

from provy.more.debian import AptitudeRole, NginxRole
from tests.unit.tools.helpers import ProvyTestCase


class NginxRoleTest(ProvyTestCase):
    def setUp(self):
        super(NginxRoleTest, self).setUp()
        self.role = NginxRole(prov=None, context={'owner': 'some-owner'})

    @istest
    def installs_necessary_packages_to_provision(self):
        with self.using_stub(AptitudeRole) as aptitude:
            self.role.provision()

            aptitude.ensure_up_to_date.assert_called_once_with()
            aptitude.ensure_package_installed.assert_called_once_with('nginx')

    @istest
    def doesnt_restart_if_not_necessary_upon_cleanup(self):
        with patch.object(self.role, 'restart'):
            self.role.cleanup()

            self.assertFalse(self.role.restart.called)

    @istest
    def restart_if_necessary_upon_cleanup(self):
        self.role.context['must-restart-nginx'] = True
        with patch.object(self.role, 'restart'):
            self.role.cleanup()

            self.assertTrue(self.role.restart.called)
