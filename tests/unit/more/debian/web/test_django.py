from mock import patch, call
from nose.tools import istest

from provy.more.debian import DjangoRole, AptitudeRole, PipRole
from tests.unit.tools.helpers import ProvyTestCase


class DjangoRoleTest(ProvyTestCase):
    def setUp(self):
        super(DjangoRoleTest, self).setUp()
        self.role = DjangoRole(prov=None, context={})

    @istest
    def installs_necessary_packages_to_provision(self):
        with self.using_stub(AptitudeRole) as aptitude, self.mock_role_method('register_template_loader'), self.using_stub(PipRole) as pip:
            self.role.provision()

            self.role.register_template_loader.assert_called_with('provy.more.debian.web')
            aptitude.ensure_package_installed.assert_called_with('python-mysqldb')
            self.assertEqual(pip.ensure_package_installed.mock_calls, [
                call('django'),
                call('gunicorn'),
            ])

    @istest
    def installs_necessary_packages_to_provision_with_version(self):
        with self.using_stub(AptitudeRole) as aptitude, self.mock_role_method('register_template_loader'), self.using_stub(PipRole) as pip:
            self.role.context['django-version'] = '1.5.1'
            self.role.provision()

            self.role.register_template_loader.assert_called_with('provy.more.debian.web')
            aptitude.ensure_package_installed.assert_called_with('python-mysqldb')
            self.assertEqual(pip.ensure_package_installed.mock_calls, [
                call('django', version=self.role.context['django-version']),
                call('gunicorn'),
            ])
