from contextlib import contextmanager
from unittest import TestCase

from mock import MagicMock, patch, call
from nose.tools import istest

from provy.more.debian import AptitudeRole, PHPRole
from tests.unit.tools.helpers import ProvyTestCase


class PHPRoleTest(ProvyTestCase):
    def setUp(self):
        self.role = PHPRole(prov=None, context={})

    @istest
    def installs_necessary_packages_to_provision(self):
        with self.using_stub(AptitudeRole) as mock_aptitude:
            self.role.provision()
            install_calls = mock_aptitude.ensure_package_installed.mock_calls
            self.assertEqual(install_calls, [call('php5'), call('php5-dev'), call('php-pear')])