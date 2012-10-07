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

    @contextmanager
    def mock_file_ops(self):
        with self.mock_role_method('read_remote_file') as read_remote_file:
            with self.mock_role_method('write_to_temp_file') as write_to_temp_file:
                with self.mock_role_method('put_file') as put_file:
                    yield read_remote_file, write_to_temp_file, put_file

    def content_from_list(self, list_):
        return '\n'.join(list_)

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

    @istest
    def restarts_the_server(self):
        with self.execute_mock() as execute:
            self.role.restart()

            execute.assert_called_with('service mongodb restart', sudo=True)

    @istest
    def appends_configuration_to_server_config(self):
        with self.mock_file_ops() as (read_remote_file, write_to_temp_file, put_file):
            read_remote_file.return_value = self.content_from_list([
                'foo=Foo',
            ])
            write_to_temp_file.return_value = '/some/tmp/path'

            self.role.configure({
                'bar': 'Bar',
            })

            read_remote_file.assert_called_with('/etc/mongodb.conf', sudo=True)
            write_to_temp_file.assert_called_with(self.content_from_list([
                'foo = Foo',
                'bar = Bar',
                '',  # newline in the end of the file
            ]))
            put_file.assert_called_with(from_file='/some/tmp/path', to_file='/etc/mongodb.conf', sudo=True)

    @istest
    def converts_boolean_config_from_input(self):
        with self.mock_file_ops() as (read_remote_file, write_to_temp_file, put_file):
            read_remote_file.return_value = self.content_from_list([
                'foo=Foo',
            ])
            write_to_temp_file.return_value = '/some/tmp/path'

            self.role.configure({
                'bar': True,
            })

            read_remote_file.assert_called_with('/etc/mongodb.conf', sudo=True)
            write_to_temp_file.assert_called_with(self.content_from_list([
                'foo = Foo',
                'bar = true',
                '',  # newline in the end of the file
            ]))
            put_file.assert_called_with(from_file='/some/tmp/path', to_file='/etc/mongodb.conf', sudo=True)

    @istest
    def overwrites_original_configuration_when_redefined(self):
        with self.mock_file_ops() as (read_remote_file, write_to_temp_file, put_file):
            read_remote_file.return_value = self.content_from_list([
                'foo=Foo',
            ])
            write_to_temp_file.return_value = '/some/tmp/path'

            self.role.configure({
                'foo': 'Baz',
                'bar': 'Bar',
            })

            read_remote_file.assert_called_with('/etc/mongodb.conf', sudo=True)
            write_to_temp_file.assert_called_with(self.content_from_list([
                'foo = Baz',
                'bar = Bar',
                '',  # newline in the end of the file
            ]))
            put_file.assert_called_with(from_file='/some/tmp/path', to_file='/etc/mongodb.conf', sudo=True)
