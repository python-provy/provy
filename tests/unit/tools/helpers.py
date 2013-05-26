from contextlib import contextmanager
from os.path import abspath, dirname, join
from unittest import TestCase

from mock import MagicMock, patch, DEFAULT

from provy.core.roles import DistroInfo, Role


PROJECT_ROOT = abspath(join(dirname(__file__), '..', '..', '..'))


class ProvyTestCase(TestCase):
    def setUp(self):
        self.role = Role(prov=None, context={})
        self.using_mocks = {}

    @contextmanager
    def using_stub(self, role):
        mock_role = MagicMock(spec=role)
        self.using_mocks[role] = mock_role
        self.role.context.setdefault('roles_in_context', {})

        @contextmanager
        def stub_using(inner_self, klass):
            role_instance = self.using_mocks[klass]
            self.role.context['roles_in_context'][klass] = role_instance
            yield role_instance
            del self.role.context['roles_in_context'][klass]

        with patch('provy.core.roles.Role.using', stub_using):
            yield mock_role

    @contextmanager
    def execute_mock(self):
        with patch('provy.core.roles.Role.execute') as execute:
            yield execute

    @contextmanager
    def mock_role_method(self, method):
        '''
        Mocks a method in the current role instance's class - i.e., not necessarily provy.core.roles.Role, depends on the object that self.role holds.
        '''
        with patch.object(self.role.__class__, method) as mock:
            yield mock

    @contextmanager
    def mock_role_methods(self, *methods):
        '''
        Same as mock_role_method, except that several methods can be provided.
        '''
        methods_to_mock = dict((method, DEFAULT) for method in methods)
        with patch.multiple(self.role.__class__, **methods_to_mock) as mocks:
            yield tuple(mocks[method] for method in methods)

    def debian_info(self):
        distro_info = DistroInfo()
        distro_info.distributor_id = 'Debian'
        distro_info.description = 'Debian GNU/Linux 6.0.5 (squeeze)'
        distro_info.release = '6.0.5'
        distro_info.codename = 'squeeze'
        return distro_info

    def ubuntu_info(self):
        distro_info = DistroInfo()
        distro_info.distributor_id = 'Ubuntu'
        distro_info.description = 'Ubuntu 12.04.1 LTS'
        distro_info.release = '12.04'
        distro_info.codename = 'precise'
        return distro_info

    @contextmanager
    def provisioning_to(self, distro):
        with self.mock_role_method('get_distro_info') as get_distro_info:
            if distro == 'ubuntu':
                distro_info = self.ubuntu_info()
            else:
                distro_info = self.debian_info()
            get_distro_info.return_value = distro_info
            yield

    @contextmanager
    def warn_only(self):
        test_case = self

        @contextmanager
        def settings(warn_only):
            test_case.assertTrue(warn_only)
            yield

        with patch('fabric.api.settings', settings):
            yield
