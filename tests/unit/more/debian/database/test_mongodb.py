from contextlib import contextmanager

from mock import MagicMock, patch, call
from nose.tools import istest

from provy.more.debian import AptitudeRole, MongoDBRole
from tests.unit.tools.helpers import ProvyTestCase


class MongoDBRoleTest(ProvyTestCase):
    def setUp(self):
        self.role = MongoDBRole(prov=None, context={})

    @contextmanager
    def mongo_method(self, method_name):
        with patch('provy.more.debian.MongoDBRole.%s' % method_name) as mock:
            yield mock

    @istest
    def installs_necessary_packages_to_provision_to_debian(self):
        with self.using_stub(AptitudeRole) as mock_aptitude:
            self.role.provision_to_debian()

            mock_aptitude.ensure_gpg_key.assert_called_with('http://docs.mongodb.org/10gen-gpg-key.asc')
            mock_aptitude.ensure_aptitude_source.assert_called_with('deb http://downloads-distro.mongodb.org/repo/debian-sysvinit dist 10gen')
            mock_aptitude.force_update.assert_called_with()
            mock_aptitude.ensure_package_installed.assert_called_with('mongodb-10gen')

    @istest
    def installs_necessary_packages_to_provision_to_ubuntu(self):
        with self.using_stub(AptitudeRole) as mock_aptitude:
            self.role.provision_to_ubuntu()

            mock_aptitude.ensure_gpg_key.assert_called_with('http://docs.mongodb.org/10gen-gpg-key.asc')
            mock_aptitude.ensure_aptitude_source.assert_called_with('deb http://downloads-distro.mongodb.org/repo/ubuntu-upstart dist 10gen')
            mock_aptitude.force_update.assert_called_with()
            mock_aptitude.ensure_package_installed.assert_called_with('mongodb-10gen')

    @istest
    def provisions_to_debian_if_is_debian(self):
        with self.provisioning_to('debian'), self.mongo_method('provision_to_debian') as provision_to_debian:
            self.role.provision()
            provision_to_debian.assert_called_with()

    @istest
    def provisions_to_ubuntu_if_is_ubuntu(self):
        with self.provisioning_to('ubuntu'), self.mongo_method('provision_to_ubuntu') as provision_to_ubuntu:
            self.role.provision()
            provision_to_ubuntu.assert_called_with()
