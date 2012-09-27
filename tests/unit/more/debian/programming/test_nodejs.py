from contextlib import contextmanager
from unittest import TestCase

from mock import MagicMock, patch, call
from nose.tools import istest

from provy.core.roles import DistroInfo
from provy.more.debian import AptitudeRole, NodeJsRole
from tests.unit.tools.helpers import ProvyTestCase


class NodeJsRoleTest(ProvyTestCase):
    def setUp(self):
        self.role = NodeJsRole(prov=None, context={})

    @istest
    def adds_repositories_and_installs_necessary_packages_to_provision_to_debian(self):
        with self.execute_mock() as execute, self.using_stub(AptitudeRole) as mock_aptitude, self.mock_role_method('ensure_dir') as ensure_dir, self.provisioning_to('debian'):
            self.role.provision_to_debian()

            mock_aptitude.ensure_package_installed.assert_called_with('g++')
            ensure_dir.assert_called_with('/tmp/nodejs', sudo=True)

            execute.assert_has_calls([
                call('wget -N http://nodejs.org/dist/node-latest.tar.gz', sudo=True),
                call('tar xzvf node-latest.tar.gz && cd `ls -rd node-v*` && ./configure && make install', sudo=True),
            ])