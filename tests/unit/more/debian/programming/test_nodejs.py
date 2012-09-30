from contextlib import contextmanager

from mock import MagicMock, patch, call
from nose.tools import istest

from provy.core.roles import DistroInfo
from provy.more.debian import AptitudeRole, NodeJsRole
from tests.unit.tools.helpers import ProvyTestCase


class NodeJsRoleTest(ProvyTestCase):
    def setUp(self):
        self.role = NodeJsRole(prov=None, context={})

    @contextmanager
    def node_method(self, method_name):
        with patch('provy.more.debian.NodeJsRole.%s' % method_name) as mock:
            yield mock

    @istest
    def adds_repositories_and_installs_necessary_sources_to_provision_to_debian(self):
        with self.execute_mock() as execute, self.using_stub(AptitudeRole) as mock_aptitude, self.mock_role_method('ensure_dir') as ensure_dir:
            self.role.provision_to_debian()

            mock_aptitude.ensure_package_installed.assert_called_with('g++')
            ensure_dir.assert_called_with('/tmp/nodejs', sudo=True)

            execute.assert_has_calls([
                call('wget -N http://nodejs.org/dist/node-latest.tar.gz', sudo=True),
                call('tar xzvf node-latest.tar.gz && cd `ls -rd node-v*` && ./configure && make install', sudo=True),
            ])

    @istest
    def adds_repositories_and_installs_necessary_packages_to_provision_to_ubuntu(self):
        with self.execute_mock() as execute, self.using_stub(AptitudeRole) as mock_aptitude:
            self.role.provision_to_ubuntu()

            mock_aptitude.ensure_package_installed.assert_any_call('python-software-properties')
            execute.assert_called_with('add-apt-repository ppa:chris-lea/node.js', sudo=True)
            self.assertTrue(mock_aptitude.force_update.called)
            mock_aptitude.ensure_package_installed.assert_any_call('nodejs')
            mock_aptitude.ensure_package_installed.assert_any_call('npm')
            mock_aptitude.ensure_package_installed.assert_any_call('nodejs-dev')

    @istest
    def checks_that_node_is_already_installed(self):
        test_case = self
        @contextmanager
        def settings(self, warn_only):
            test_case.assertTrue(warn_only)
            yield

        with self.execute_mock() as execute, patch('fabric.api.settings', settings):
            execute.return_value = 'v0.8.10'
            self.assertTrue(self.role.is_already_installed())

    @istest
    def checks_that_node_is_not_installed_yet_by_output_string(self):
        test_case = self
        @contextmanager
        def settings(self, warn_only):
            test_case.assertTrue(warn_only)
            yield

        with self.execute_mock() as execute, patch('fabric.api.settings', settings):
            execute.return_value = 'command not found'
            self.assertFalse(self.role.is_already_installed())

    @istest
    def checks_that_node_is_not_installed_yet_by_stranger_output_string(self):
        test_case = self
        @contextmanager
        def settings(self, warn_only):
            test_case.assertTrue(warn_only)
            yield

        with self.execute_mock() as execute, patch('fabric.api.settings', settings):
            execute.return_value = 'verbose error: command not found'
            self.assertFalse(self.role.is_already_installed())

    @istest
    def checks_that_node_is_not_installed_yet_by_output_as_none(self):
        test_case = self
        @contextmanager
        def settings(self, warn_only):
            test_case.assertTrue(warn_only)
            yield

        with self.execute_mock() as execute, patch('fabric.api.settings', settings):
            execute.return_value = None
            self.assertFalse(self.role.is_already_installed())

    @istest
    def provisions_to_debian_if_is_debian(self):
        with self.provisioning_to('debian'), self.node_method('provision_to_debian') as provision_to_debian, self.node_method('is_already_installed') as is_already_installed:
            is_already_installed.return_value = False
            self.role.provision()
            provision_to_debian.assert_called_with()

    @istest
    def provisions_to_ubuntu_if_is_ubuntu(self):
        with self.provisioning_to('ubuntu'), self.node_method('provision_to_ubuntu') as provision_to_ubuntu, self.node_method('is_already_installed') as is_already_installed:
            is_already_installed.return_value = False
            self.role.provision()
            provision_to_ubuntu.assert_called_with()

    @istest
    def doesnt_provision_if_already_installed(self):
        with self.provisioning_to('ubuntu'), self.node_method('provision_to_ubuntu') as provision_to_ubuntu, self.node_method('is_already_installed') as is_already_installed:
            is_already_installed.return_value = True
            self.role.provision()
            self.assertFalse(provision_to_ubuntu.called)
