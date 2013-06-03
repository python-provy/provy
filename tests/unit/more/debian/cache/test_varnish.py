from mock import call
from nose.tools import istest

from provy.more.debian import AptitudeRole, VarnishRole
from tests.unit.tools.helpers import ProvyTestCase


class VarnishRoleTest(ProvyTestCase):
    def setUp(self):
        super(VarnishRoleTest, self).setUp()
        self.role = VarnishRole(prov=None, context={'owner': 'some-owner'})

    @istest
    def installs_necessary_packages_to_provision_to_ubuntu(self):
        with self.using_stub(AptitudeRole) as aptitude:
            self.role.provision_to_ubuntu()

            self.assertEqual(aptitude.ensure_package_installed.mock_calls, [
                call('varnish'),
            ])

    @istest
    def installs_necessary_packages_to_provision_to_debian(self):
        with self.using_stub(AptitudeRole) as aptitude:
            self.role.provision_to_debian()

            aptitude.ensure_gpg_key.assert_called_with('http://repo.varnish-cache.org/debian/GPG-key.txt')
            aptitude.ensure_aptitude_source.assert_called_with('deb http://repo.varnish-cache.org/debian/ wheezy varnish-3.0')
            aptitude.force_update.assert_called_with()
            aptitude.ensure_package_installed.assert_called_with('varnish')
