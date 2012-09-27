from contextlib import contextmanager
from unittest import TestCase

from mock import MagicMock, patch

from provy.core.roles import DistroInfo


class ProvyTestCase(TestCase):
    @contextmanager
    def using_stub(self, role):
        mock_role = MagicMock(spec=role)

        @contextmanager
        def stub_using(self, klass):
            yield mock_role

        with patch('provy.core.roles.Role.using', stub_using):
            yield mock_role

    @contextmanager
    def execute_mock(self):
        with patch('provy.core.roles.Role.execute') as execute:
            yield execute

    @contextmanager
    def mock_role_method(self, method):
        with patch('provy.core.roles.Role.%s' % method) as mock:
            yield mock

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
