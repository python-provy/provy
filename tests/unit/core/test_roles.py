from contextlib import contextmanager
import os
import sys

from mock import MagicMock, patch, call
from nose.tools import istest

from provy.core.roles import Role
from tests.unit.tools.helpers import ProvyTestCase


class RoleTest(ProvyTestCase):
    def setUp(self):
        self.role = Role(prov=None, context={})

    @istest
    def checks_if_a_remote_directory_exists(self):
        with self.execute_mock() as execute:
            execute.return_value = '0'
            self.assertTrue(self.role.remote_exists_dir('/some_path'))

            execute.assert_called_with('test -d /some_path; echo $?', stdout=False, sudo=True)

    @istest
    def checks_if_a_remote_directory_doesnt_exist(self):
        with self.execute_mock() as execute:
            execute.return_value = '1'
            self.assertFalse(self.role.remote_exists_dir('/some_path'))

            execute.assert_called_with('test -d /some_path; echo $?', stdout=False, sudo=True)

    @istest
    def doesnt_create_directory_if_it_already_exists(self):
        with self.mock_role_method('remote_exists_dir') as remote_exists_dir, self.execute_mock() as execute:
            remote_exists_dir.return_value = True
            self.role.ensure_dir('/some_path')
            self.assertFalse(execute.called)

    @istest
    def creates_the_directory_if_it_doesnt_exist(self):
        with self.mock_role_method('remote_exists_dir') as remote_exists_dir, self.execute_mock() as execute:
            remote_exists_dir.return_value = False
            self.role.ensure_dir('/some_path')
            execute.assert_called_with('mkdir -p /some_path', stdout=False, sudo=False)

    @istest
    def gets_distro_info_for_debian(self):
        with self.execute_mock() as execute:
            execute.return_value = 'No LSB modules are available.\nDistributor ID:\tDebian\nDescription:\tDebian GNU/Linux 6.0.5 (squeeze)\nRelease:\t6.0.5\nCodename:\tsqueeze'
            distro_info = self.role.get_distro_info()
            execute.assert_called_with('lsb_release -a')
            self.assertEqual(distro_info.distributor_id, 'Debian')
            self.assertEqual(distro_info.description, 'Debian GNU/Linux 6.0.5 (squeeze)')
            self.assertEqual(distro_info.release, '6.0.5')
            self.assertEqual(distro_info.codename, 'squeeze')

    @istest
    def gets_distro_info_for_ubuntu(self):
        with self.execute_mock() as execute:
            execute.return_value = 'No LSB modules are available.\r\nDistributor ID:\tUbuntu\r\nDescription:\tUbuntu 12.04.1 LTS\r\nRelease:\t12.04\r\nCodename:\tprecise'
            distro_info = self.role.get_distro_info()
            execute.assert_called_with('lsb_release -a')
            self.assertEqual(distro_info.distributor_id, 'Ubuntu')
            self.assertEqual(distro_info.description, 'Ubuntu 12.04.1 LTS')
            self.assertEqual(distro_info.release, '12.04')
            self.assertEqual(distro_info.codename, 'precise')

    @istest
    def gets_distro_info_for_centos(self):
        with self.execute_mock() as execute:
            execute.return_value = 'LSB Version:\t:core-4.0-ia32:core-4.0-noarch:graphics-4.0-ia32:graphics-4.0-noarch:printing-4.0-ia32:printing-4.0-noarch\nDistributor ID:\tCentOS\nDescription:\tCentOS release 5.8 (Final)\nRelease:\t5.8\nCodename:\tFinal'
            distro_info = self.role.get_distro_info()
            execute.assert_called_with('lsb_release -a')
            self.assertEqual(distro_info.lsb_version, ':core-4.0-ia32:core-4.0-noarch:graphics-4.0-ia32:graphics-4.0-noarch:printing-4.0-ia32:printing-4.0-noarch')
            self.assertEqual(distro_info.distributor_id, 'CentOS')
            self.assertEqual(distro_info.description, 'CentOS release 5.8 (Final)')
            self.assertEqual(distro_info.release, '5.8')
            self.assertEqual(distro_info.codename, 'Final')
