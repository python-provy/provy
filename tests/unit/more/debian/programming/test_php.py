from contextlib import contextmanager
from unittest import TestCase

from mock import MagicMock, patch, call
from nose.tools import istest

from provy.core.roles import DistroInfo
from provy.more.debian import AptitudeRole, PHPRole
from tests.unit.tools.helpers import ProvyTestCase


class PHPRoleTest(ProvyTestCase):
    def setUp(self):
        self.role = PHPRole(prov=None, context={})

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

    @istest
    def adds_repositories_and_installs_necessary_packages_to_provision_to_debian(self):
        with self.using_stub(AptitudeRole) as mock_aptitude, self.provisioning_to('debian'):
            self.role.provision()

            source_calls = mock_aptitude.ensure_aptitude_source.mock_calls
            self.assertEqual(source_calls, [
                call('deb http://packages.dotdeb.org squeeze all'),
                call('deb-src http://packages.dotdeb.org squeeze all'),
            ])

            mock_aptitude.ensure_gpg_key.assert_called_with('http://www.dotdeb.org/dotdeb.gpg')
            self.assertTrue(mock_aptitude.force_update.called)

            install_calls = mock_aptitude.ensure_package_installed.mock_calls
            self.assertEqual(install_calls, [call('php5-dev'), call('php5-fpm'), call('php-pear')])

    @istest
    def provisions_to_ubuntu_without_adding_repositories(self):
        with self.using_stub(AptitudeRole) as mock_aptitude, self.provisioning_to('ubuntu'):
            self.role.provision()

            self.assertFalse(mock_aptitude.ensure_aptitude_source.called)
            self.assertFalse(mock_aptitude.ensure_gpg_key.called)
            self.assertFalse(mock_aptitude.force_update.called)

            install_calls = mock_aptitude.ensure_package_installed.mock_calls
            self.assertEqual(install_calls, [call('php5-dev'), call('php5-fpm'), call('php-pear')])
